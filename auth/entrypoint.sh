#!/bin/sh
# This script ensures the database is initialized before starting the app.

# Abort on any error
set -e

# Run the database initialization command
flask init-db

# Now, execute the command passed to this script (the Dockerfile's CMD)
exec "$@"
