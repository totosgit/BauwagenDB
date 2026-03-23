#!/bin/bash
set -e

cd "$(dirname "$0")"
source venv/bin/activate

# Get local IP for display
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo "==================================="
echo "  Bauwagen DB"
echo "  http://${LOCAL_IP}:8000"
echo "==================================="

cd backend
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
