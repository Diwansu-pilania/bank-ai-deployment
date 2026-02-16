# consumer.py (Version 13 - Render-Ready, Logic Corrected)
import json
import os
import time
from confluent_kafka import Consumer, KafkaError
import pandas as pd
from datetime import datetime, timedelta # <-- FIX: Import timedelta

print("--- Real-Time Engine Starting (v13 - Render Ready) ---")

# --- Config (Render-Ready Paths) ---
DATA_DIR = "/app/data"
KAFKA_TOPIC = 'financial_transactions'
# NOTE: In Render, Kafka will be available at 'kafka:29092' because they are in the same Docker network
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:29092') # Use environment variable or default

FEATURE_STORE_PATH = os.path.join(DATA_DIR, 'feature_store.json')
TEMP_FEATURE_STORE_PATH = os.path.join(DATA_DIR, 'feature_store.json.tmp')
GNN_FEATURES_PATH = os.path.join(DATA_DIR, 'gnn_network_features.csv')

# --- Load AI Assets ---
try:
    # Consumer doesn't need the model, only the GNN features for initialization
    gnn_features_df = pd.read_csv(GNN_FEATURES_PATH, index_col='customer_id')
    GNN_FEATURES = gnn_features_df.to_dict(orient='index')
    print("Successfully loaded GNN network features.")
except Exception as e:
    print(f"FATAL ERROR loading GNN features: {e}")
    exit()


# --- State Management (Atomic save) ---
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


# --- Main Loop ---
if __name__ == "__main__":
    customer_feature_store = load_feature_store()
    last_save_time = time.time()

    consumer_conf = {'bootstrap.servers': KAFKA_BROKER, 'group.id': 'final-render-consumer-v13',
                     'auto.offset.reset': 'earliest'}
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"\n--- Waiting for new transactions on topic '{KAFKA_TOPIC}' from broker '{KAFKA_BROKER}'... ---")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Kafka Error: {msg.error()}")
                continue

            try:
                transaction = json.loads(msg.value().decode('utf-8'))
                customer_id = transaction['customer_id']

                # --- FIX: Initialize state FIRST if customer is new ---
                if customer_id not in customer_feature_store:
                    customer_feature_store[customer_id] = {
                        'feature_late_salary_count': 0,
                        'feature_decline_week_count': 0, # This would be updated by a separate batch job
                        'feature_lending_app_tx_count': 0,
                        'feature_late_utility_count': 0,
                        'feature_discretionary_spend_ratio': 0.5, # Default value
                        'feature_atm_withdrawal_count': 0,
                        'feature_failed_debit_count': 0,
                        'network_stress_feature': GNN_FEATURES.get(customer_id, {}).get('network_stress_feature', 0.0)
                    }
                    print(f"Initialized new state for customer {customer_id}")

                # --- Now, safely get the state and update features ---
                state = customer_feature_store[customer_id]
                
                # FIX: Get timestamp from transaction
                tx_timestamp = datetime.fromisoformat(transaction['timestamp'])

                # Update features based on the current transaction
                if transaction.get('merchant_id') == 'LENDINGAPP01':
                    state['feature_lending_app_tx_count'] += 1
                if transaction.get('status') == 'FAILED':
                    state['feature_failed_debit_count'] += 1
                if transaction.get('merchant_id') == 'ATM01':
                    state['feature_atm_withdrawal_count'] += 1
                # Example logic for late payments
                if transaction.get('merchant_id') == 'SALARY' and tx_timestamp.day > 29: # Salary after the 29th is late
                    state['feature_late_salary_count'] += 1
                if transaction.get('merchant_id') == 'UTILITY01' and tx_timestamp.day > 20: # Utility after the 20th is late
                    state['feature_late_utility_count'] += 1

                print(f"Processed transaction for {customer_id}. Features updated.")

                # Periodically save feature store to disk
                if time.time() - last_save_time > 5: # Save every 5 seconds
                    save_feature_store_to_disk(customer_feature_store)
                    last_save_time = time.time()
                    print("--- Periodically saved feature store to disk. ---")

            except json.JSONDecodeError:
                print(f"ERROR: Could not decode message: {msg.value()}")
            except KeyError as e:
                print(f"ERROR: Missing key in transaction: {e} - Data: {msg.value()}")

    except KeyboardInterrupt:
        print("\n--- Consumer stopped by user. Final save... ---")
    finally:
        save_feature_store_to_disk(customer_feature_store)
        consumer.close()
        print("--- Feature store saved and consumer closed. ---")

