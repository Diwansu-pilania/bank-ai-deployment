#!/bin/bash
set -e

# --- This script is for the manual Kafka installation ---

echo "--- Starting Zookeeper in background ---"
/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties &

echo "--- Starting Kafka in background ---"
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties &

echo "--- Waiting for Kafka to be ready... ---"
i=0
while ! nc -z localhost 9092; do
  i=$((i+1 ))
  if [ $i -ge 20 ]; then # Increased timeout to 100 seconds
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
