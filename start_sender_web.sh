#!/bin/bash

echo "🚀 Starting Log Sender Web Tool..."

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit
fi

echo "🌐 Starting Web Interface..."
echo "💡 Tip: Web interface will open in your browser"
echo "💡 For LAN access, use --server.address 0.0.0.0 parameter"
echo ""

# Start Streamlit application
streamlit run log_sender_web.py --server.port 8501
