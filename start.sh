#!/bin/bash
set -e

# --- This is the final, FAST startup script ---

# --- Step 1: Configure and Start Kafka/Zookeeper ---
export ZOOKEEPER_CLIENT_PORT=2181
mkdir -p /app/tmp/zookeeper
echo "1" > /app/tmp/zookeeper/myid

export KAFKA_ZOOKEEPER_CONNECT=localhost:2181
export KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
export KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092
export KAFKA_BROKER_ID=1

echo "--- Starting Zookeeper & Kafka in background ---"
/opt/kafka/bin/zookeeper-server-start.sh -daemon /opt/kafka/config/zookeeper.properties
/opt/kafka/bin/kafka-server-start.sh -daemon /opt/kafka/config/server.properties

echo "--- Waiting for Kafka to be fully ready... ---"
i=0
until /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q 'financial_transactions'; do
  i=$((i+1))
  if [ $i -ge 24 ]; then
    echo "FATAL: Kafka topic was not created in time. Exiting."
    exit 1
  fi
  echo "Kafka not fully ready yet... creating topic and waiting 5 seconds."
  /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --topic financial_transactions --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1
  sleep 5
done
echo "--- Kafka is 100% ready! ---"

# --- Step 2: Start the main application IMMEDIATELY ---
# Data generation is now a separate, one-time job.
echo "--- Starting the main application (API, Consumer, Producer) ---"
uvicorn main:app --host 0.0.0.0 --port 8000 &
python3 consumer.py &
python3 producer.py

# Keep the main script running
wait -n
