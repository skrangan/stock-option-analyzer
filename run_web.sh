#!/usr/bin/env bash
# Launcher for FastAPI Mobile & Desktop Web Application

PORT=8000
HOST="0.0.0.0"

echo "=========================================================="
echo "🚀 Starting High-Performance Stock & Option Web App..."
echo "=========================================================="
echo "• Local Desktop URL: http://localhost:$PORT"

# Get Local IP address for phone
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n 1 | awk '{print $2}')
if [ -n "$LOCAL_IP" ]; then
    echo "• 📱 Access on your Phone (Same Wi-Fi): http://$LOCAL_IP:$PORT"
fi
echo "=========================================================="

if [ -f "/opt/anaconda3/bin/uvicorn" ]; then
    /opt/anaconda3/bin/uvicorn server:app --host $HOST --port $PORT --reload
else
    uvicorn server:app --host $HOST --port $PORT --reload
fi
