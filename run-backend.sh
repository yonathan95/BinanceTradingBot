#!/bin/bash

# Script to build and run the Hive Mind backend services

echo "Building and starting Hive Mind backend services..."

# Build the Docker images
docker-compose build

# Start the services
docker-compose up -d

# Wait for the database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Initialize the database
echo "Initializing the database..."
docker exec -it hivemind-api python control-plane/init_db.py

# Populate the database with mock data
echo "Populating the database with mock data..."
docker exec -it hivemind-api python control-plane/init_mock_data.py

echo "Hive Mind backend services are now running!"
echo "API available at: http://localhost:5000"
echo "Grafana dashboard at: http://localhost:3000"
echo "Prometheus metrics at: http://localhost:9090" 