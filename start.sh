#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Initialize the database
echo "Initializing database..."
python docker_init_db.py

# Start the API server
echo "Starting API server..."
exec uvicorn bdi_api.s7.api:app --host 0.0.0.0 --port 8000 --reload
