# Start with a basic, universally available Ubuntu image
FROM ubuntu:22.04

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install essential tools, Java (for Kafka), Python, and netcat
RUN apt-get update && \
    apt-get install -y wget default-jre python3 python3-pip netcat-openbsd && \
    apt-get clean

# Download and extract Kafka
# We are using a specific, stable version of Kafka
RUN wget https://archive.apache.org/dist/kafka/3.5.0/kafka_2.13-3.5.0.tgz && \
    tar -xzf kafka_2.13-3.5.0.tgz && \
    mv kafka_2.13-3.5.0 /opt/kafka && \
    rm kafka_2.13-3.5.0.tgz

# Copy your application code into the container
COPY . .

# Install your Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make the startup script executable
RUN chmod +x start.sh

# Expose the API port
EXPOSE 8000

# The command that Render will run
CMD ["./start.sh"]
