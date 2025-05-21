#!/bin/bash
set -e

# This script will run inside the Docker container when it starts.
# It takes the BACKEND_URL environment variable (passed from docker-compose)
# and writes it into config.js, which the HTML/JS then loads.

echo "const BACKEND_URL = \"${BACKEND_URL}\";" > /usr/share/nginx/html/config.js

# Execute the original Nginx command 
exec "$@"