#!/bin/bash

# Make this script exit if any command fails
set -e

echo "--- Starting Zookeeper in background ---"
/etc/confluent/docker/run &

echo "--- Starting Kafka in background ---"
# We need to configure Kafka to listen on localhost within the container
export KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
/etc/confluent/docker/run &

echo "--- Waiting for Kafka to be ready... ---"
# This is a simple loop to wait for Kafka to start
# It tries to connect every 5 seconds, up to 12 times (1 minute)
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
# This will run the data generation script only once
python generate_rich_data.py

echo "--- Starting the main application (API, Consumer, Producer) ---"
# Start the main application components in the background
uvicorn main:app --host 0.0.0.0 --port 8000 &
python consumer.py &
python producer.py

# Keep the script running to keep the container alive
wait -n
