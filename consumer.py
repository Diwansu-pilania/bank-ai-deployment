# consumer.py (Version 12 - Definitive, Simple & Focused)
import json
import os
import time
from confluent_kafka import Consumer, KafkaError
import joblib
import pandas as pd
from datetime import datetime

print("--- Real-Time Engine Starting (v12 - The Final, Correct Version) ---")

# Config
KAFKA_TOPIC = 'financial_transactions'
KAFKA_BROKER = 'localhost:9092'
FEATURE_STORE_PATH = 'feature_store.json'
TEMP_FEATURE_STORE_PATH = 'feature_store.json.tmp'
MODEL_FILENAME = 'financial_stress_predictor.pkl'
GNN_FEATURES_PATH = 'gnn_network_features.csv'

# Load AI Assets
try:
    predictor_model = joblib.load(MODEL_FILENAME)
    gnn_features_df = pd.read_csv(GNN_FEATURES_PATH, index_col='customer_id')
    GNN_FEATURES = gnn_features_df.to_dict(orient='index')
    print("Successfully loaded all AI assets.")
except Exception as e:
    print(f"FATAL ERROR loading assets: {e}")
    exit()


# State Management (Atomic save)
def load_feature_store():
    if os.path.exists(FEATURE_STORE_PATH):
        with open(FEATURE_STORE_PATH, 'r') as f: return json.load(f)
    return {}


def save_feature_store_to_disk(store):
    with open(TEMP_FEATURE_STORE_PATH, 'w') as f: json.dump(store, f)
    os.replace(TEMP_FEATURE_STORE_PATH, FEATURE_STORE_PATH)  # This is atomic and safe


# Main Loop
if __name__ == "__main__":
    customer_feature_store = load_feature_store()
    last_save_time = time.time()

    consumer_conf = {'bootstrap.servers': KAFKA_BROKER, 'group.id': 'final-correct-consumer-v12',
                     'auto.offset.reset': 'earliest'}
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print("\n--- Waiting for new transactions... ---")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF: print(f"Kafka Error: {msg.error()}")
                continue

            transaction = json.loads(msg.value().decode('utf-8'))
            customer_id = transaction['customer_id']
            state = customer_feature_store[customer_id]
            now = datetime.now()

            # Update logic
            if transaction.get('merchant_id') == 'LENDINGAPP01':
                state['lending_app_timestamps'].append(transaction['timestamp'])

            # Purane timestamps ko saaf karo
            thirty_days_ago = now - timedelta(days=30)
            state['lending_app_timestamps'] = [ts for ts in state['lending_app_timestamps'] if
                                               datetime.fromisoformat(ts) > thirty_days_ago]

            # Nayi feature value calculate karo
            state['feature_lending_app_tx_count'] = len(state['lending_app_timestamps'])

            # Initialize state
            if customer_id not in customer_feature_store:
                customer_feature_store[customer_id] = {
                    'feature_late_salary_count': 0, 'feature_decline_week_count': 0, 'feature_lending_app_tx_count': 0,
                    'feature_late_utility_count': 0, 'feature_discretionary_spend_ratio': 0.5,
                    'feature_atm_withdrawal_count': 0,
                    'feature_failed_debit_count': 0,
                    'network_stress_feature': GNN_FEATURES.get(customer_id, {}).get('network_stress_feature', 0.0)
                }

            # Update features
            state = customer_feature_store[customer_id]
            if transaction.get('merchant_id') == 'LENDINGAPP01': state['feature_lending_app_tx_count'] += 1
            if transaction.get('status') == 'FAILED': state['feature_failed_debit_count'] += 1
            if transaction.get('merchant_id') == 'ATM01': state['feature_atm_withdrawal_count'] += 1
            if transaction.get('merchant_id') == 'SALARY' and tx_timestamp.day > 28: state[
                'feature_late_salary_count'] += 1
            if transaction.get('merchant_id') == 'UTILITY01' and tx_timestamp.day > 15: state[
                'feature_late_utility_count'] += 1

            print(f"Processed transaction for {customer_id}. Features updated.")

            # Periodically save feature store
            if time.time() - last_save_time > 5:
                save_feature_store_to_disk(customer_feature_store)
                last_save_time = time.time()

    except KeyboardInterrupt:
        print("\n--- Consumer stopped. Final save... ---")
    finally:
        save_feature_store_to_disk(customer_feature_store)
        consumer.close()
