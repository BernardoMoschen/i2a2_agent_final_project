#!/bin/bash

# Start file server in background
python3 << 'EOF' &
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root.parent))

logging.basicConfig(level=logging.INFO)

from src.ui.file_server import ReportFileServer

server = ReportFileServer(reports_dir="./reports")
server.run(host="127.0.0.1", port=5000, debug=False)
EOF

FILE_SERVER_PID=$!
echo "File server started with PID: $FILE_SERVER_PID"

# Sleep a moment for file server to start
sleep 2

# Start Streamlit
echo "Starting Streamlit..."
streamlit run src/ui/app.py "$@"

# Clean up on exit
trap "kill $FILE_SERVER_PID" EXIT
