# producer.py (Version 12 - Final, Render-Ready, Single Service)
import pandas as pd
from confluent_kafka import Producer
import json
import time
import os

# --- Config ---
KAFKA_TOPIC = 'financial_transactions'
# This will now connect to Kafka running in the same container
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
TRANSACTIONS_FILE = 'rich_transactions.csv'

# --- Main Loop ---
if __name__ == "__main__":
    producer_conf = {'bootstrap.servers': KAFKA_BROKER}
    producer = Producer(producer_conf)

    print(f"--- Transaction Producer Started. Reading from '{TRANSACTIONS_FILE}' ---")
    print(f"--- Sending messages to topic '{KAFKA_TOPIC}' on broker '{KAFKA_BROKER}'... ---")

    try:
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)
        for index, row in transactions_df.iterrows():
            transaction = row.to_dict()
            # Convert timestamp to string if it's not already
            if 'timestamp' in transaction and not isinstance(transaction['timestamp'], str):
                transaction['timestamp'] = str(transaction['timestamp'])

            producer.produce(KAFKA_TOPIC, key=str(transaction['customer_id']), value=json.dumps(transaction))
            producer.poll(0)  # Trigger delivery reports
            print(f"Sent transaction {index + 1}/{len(transactions_df)} for customer {transaction['customer_id']}")
            time.sleep(0.1) # Simulate a real-time stream

        producer.flush()
        print("\n--- All transactions sent. Producer finished. ---")

    except FileNotFoundError:
        print(f"FATAL ERROR: Transactions file '{TRANSACTIONS_FILE}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
