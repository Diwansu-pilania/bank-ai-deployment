# Dockerfile for the Financial Stress AI Application

# 1. Start with a standard Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (for efficient caching)
COPY requirements.txt .

# 4. Install all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all of our project files into the container
# This includes all .py, .csv, .pkl, and .zip files
COPY . .

# 6. Expose the port that our FastAPI server will run on
EXPOSE 8000

# The CMD is set in the docker-compose.yml file, not here.
