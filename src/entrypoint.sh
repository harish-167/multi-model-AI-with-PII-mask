#!/bin/bash

# Start the Gunicorn server in the background.
# --workers 4: Number of worker processes for handling requests
# --bind 0.0.0.0:8000: Listen on all network interfaces on port 8000
# app:application: Tells Gunicorn to look for a callable named 'application' in the 'app.py' file.
echo "Starting Gunicorn..."
gunicorn --workers 4 --bind 0.0.0.0:8000 app:application &

# Start Apache in the foreground.
# The `exec` command is important because it replaces the shell process with the Apache process.
# This makes Apache the main process (PID 1) that Docker watches.
# When Apache stops, the container will stop.
echo "Starting Apache..."
exec apache2-foreground