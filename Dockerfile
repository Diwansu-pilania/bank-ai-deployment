# Start with a reliable and public Kafka image from Bitnami
FROM bitnami/kafka:3.5

# Set the working directory
WORKDIR /app

# Switch to root user to install packages
USER root

# Install Python, pip, and netcat (for the startup check)
RUN install_packages python3 python3-pip netcat-openbsd

# Copy your application code into the container
COPY . .

# Install your Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make the startup script executable
RUN chmod +x start.sh

# Switch back to the non-root user for better security
USER 1001

# The command that Render will run
CMD ["/app/start.sh"]
