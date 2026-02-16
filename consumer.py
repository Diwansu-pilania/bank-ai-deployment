# consumer.py (Version 14 - Final, Render-Ready, Single Service)
import json
import os
import time
from confluent_kafka import Consumer, KafkaError
import pandas as pd
from datetime import datetime, timedelta

print("--- Real-Time Engine Starting (v14 - Final, Render-Ready) ---")

# --- Config (Simple Paths for Single Service) ---
KAFKA_TOPIC = 'financial_transactions'
# This will now connect to Kafka running in the same container
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')

FEATURE_STORE_PATH = 'feature_store.json'
TEMP_FEATURE_STORE_PATH = 'feature_store.json.tmp'
GNN_FEATURES_PATH = 'gnn_network_features.csv'
TRANSACTION_HISTORY_PATH = 'transaction_history.csv'
TEMP_TRANSACTION_HISTORY_PATH = 'transaction_history.csv.tmp'

# --- Load AI Assets ---
try:
    gnn_features_df = pd.read_csv(GNN_FEATURES_PATH, index_col='customer_id')
    GNN_FEATURES = gnn_features_df.to_dict(orient='index')
    print("Successfully loaded GNN network features.")
except Exception as e:
    print(f"FATAL ERROR loading GNN features: {e}")
    exit()

# --- State Management (Atomic Writes) ---
def load_feature_store():
    if os.path.exists(FEATURE_STORE_PATH):
        try:
            with open(FEATURE_STORE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("WARNING: Feature store was corrupted or not found. Starting fresh.")
            return {}
    return {}

def save_feature_store_to_disk(store):
    try:
        with open(TEMP_FEATURE_STORE_PATH, 'w') as f:
            json.dump(store, f, indent=2)
        os.replace(TEMP_FEATURE_STORE_PATH, FEATURE_STORE_PATH)
    except Exception as e:
        print(f"ERROR saving feature store: {e}")

def atomic_append_to_history(transaction_dict):
    # Append to a temporary file first
    mode = 'a' if os.path.exists(TEMP_TRANSACTION_HISTORY_PATH) else 'w'
    header = mode == 'w'
    pd.DataFrame([transaction_dict]).to_csv(TEMP_TRANSACTION_HISTORY_PATH, mode=mode, header=header, index=False)
    # Atomically replace the old file with the new one
    os.replace(TEMP_TRANSACTION_HISTORY_PATH, TRANSACTION_HISTORY_PATH)

# --- Main Loop ---
if __name__ == "__main__":
    customer_feature_store = load_feature_store()
    last_save_time = time.time()

    consumer_conf = {'bootstrap.servers': KAFKA_BROKER, 'group.id': 'final-render-consumer-v14',
                     'auto.offset.reset': 'earliest'}
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"\n--- Waiting for new transactions on topic '{KAFKA_TOPIC}' from broker '{KAFKA_BROKER}'... ---")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Kafka Error: {msg.error()}")
                continue

            try:
                transaction = json.loads(msg.value().decode('utf-8'))
                customer_id = transaction['customer_id']

                # Initialize state FIRST if customer is new
                if customer_id not in customer_feature_store:
                    customer_feature_store[customer_id] = {
                        'feature_late_salary_count': 0,
                        'feature_decline_week_count': 0,
                        'feature_lending_app_tx_count': 0,
                        'feature_late_utility_count': 0,
                        'feature_discretionary_spend_ratio': 0.5,
                        'feature_atm_withdrawal_count': 0,
                        'feature_failed_debit_count': 0,
                        'network_stress_feature': GNN_FEATURES.get(customer_id, {}).get('network_stress_feature', 0.0)
                    }
                    print(f"Initialized new state for customer {customer_id}")

                # Now, safely get the state and update features
                state = customer_feature_store[customer_id]
                tx_timestamp = datetime.fromisoformat(transaction['timestamp'])

                # Update features based on the current transaction
                if transaction.get('merchant_id') == 'LENDINGAPP01': state['feature_lending_app_tx_count'] += 1
                if transaction.get('status') == 'FAILED': state['feature_failed_debit_count'] += 1
                if transaction.get('merchant_id') == 'ATM01': state['feature_atm_withdrawal_count'] += 1
                if transaction.get('merchant_id') == 'SALARY' and tx_timestamp.day > 29: state['feature_late_salary_count'] += 1
                if transaction.get('merchant_id') == 'UTILITY01' and tx_timestamp.day > 20: state['feature_late_utility_count'] += 1

                # Log the transaction to the persistent history file
                atomic_append_to_history(transaction)
                print(f"Processed and logged transaction for {customer_id}.")

                # Periodically save feature store to disk
                if time.time() - last_save_time > 5:
                    save_feature_store_to_disk(customer_feature_store)
                    last_save_time = time.time()
                    print("--- Periodically saved feature store to disk. ---")

            except (json.JSONDecodeError, KeyError) as e:
                print(f"ERROR processing message: {e} - Data: {msg.value()}")

    except KeyboardInterrupt:
        print("\n--- Consumer stopped by user. Final save... ---")
    finally:
        save_feature_store_to_disk(customer_feature_store)
        consumer.close()
        print("--- Feature store saved and consumer closed. ---")
