# producer.py (Using confluent-kafka)
from confluent_kafka import Producer
import pandas as pd
import json
import time

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
KAFKA_TOPIC = 'financial_transactions'

print("--- Starting Transaction Stream ---")
transactions_df = pd.read_csv('rich_transactions.csv').sort_values(by='timestamp')


for i, row in transactions_df.iterrows():
    transaction_message = row.to_dict()
    producer.produce(
        KAFKA_TOPIC,
        value=json.dumps(transaction_message).encode('utf-8')
    )
    producer.poll(0) # Trigger delivery reports
    print(f"Sent transaction {i+1}/{len(transactions_df)}")
    time.sleep(0.01)

producer.flush()
print("\n--- Transaction Stream Finished ---")
