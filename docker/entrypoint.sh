#!/bin/sh
set -e
# settings log to <repository>/logs: make sure it exists in the mounted checkout
mkdir -p /app/logs
exec "$@"
