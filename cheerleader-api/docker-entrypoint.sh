#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start server
echo "Starting server..."
gunicorn --bind 0.0.0.0:8000 cheerleader.wsgi
