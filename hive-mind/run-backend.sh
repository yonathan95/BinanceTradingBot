#!/bin/bash

# Build and start the backend services
docker-compose up -d hive-mind-backend

echo "Hive Mind backend is running on http://localhost:5000"
echo "To view logs: docker-compose logs -f hive-mind-backend"
echo "To stop: docker-compose down" 