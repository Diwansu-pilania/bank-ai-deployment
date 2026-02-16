#!/bin/bash
set -e

# --- This script is for the bitnami/kafka image ---

echo "--- Starting Zookeeper in background ---"
/opt/bitnami/kafka/bin/zookeeper-server-start.sh /opt/bitnami/kafka/config/zookeeper.properties &

echo "--- Starting Kafka in background ---"
/opt/bitnami/kafka/bin/kafka-server-start.sh /opt/bitnami/kafka/config/server.properties &

echo "--- Waiting for Kafka to be ready... ---"
i=0
while ! nc -z localhost 9092; do
  i=$((i+1))
  if [ $i -ge 12 ]; then
    echo "Kafka did not start in time. Exiting."
    exit 1
  fi
  echo "Kafka not ready yet... waiting 5 seconds."
  sleep 5
done
echo "--- Kafka is ready! ---"

echo "--- Generating initial data if it doesn't exist ---"
python3 generate_rich_data.py

echo "--- Starting the main application (API, Consumer, Producer) ---"
uvicorn main:app --host 0.0.0.0 --port 8000 &
python3 consumer.py &
python3 producer.py

wait -n
