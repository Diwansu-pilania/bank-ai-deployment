# Start with the official Confluent platform image which has Kafka and Zookeeper
FROM confluentinc/cp-platform:7.3.2

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . .

# Install Python and pip
USER root
RUN apt-get update && apt-get install -y python3 python3-pip

# Install your Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the startup script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# The command that Render will run
CMD ["./start.sh"]
