#!/usr/bin/env bash
# Quick launcher for Stock Analysis Application

# Prefer Anaconda python if available, otherwise fallback to system python
if [ -f "/opt/anaconda3/bin/streamlit" ]; then
    STREAMLIT_BIN="/opt/anaconda3/bin/streamlit"
elif command -v streamlit &> /dev/null; then
    STREAMLIT_BIN="streamlit"
else
    echo "Streamlit not found in standard paths. Attempting via python -m streamlit..."
    STREAMLIT_BIN="python3 -m streamlit"
fi

echo "=========================================================="
echo "🚀 Launching Stock Analysis & Forecast Dashboard..."
echo "=========================================================="
$STREAMLIT_BIN run app.py
