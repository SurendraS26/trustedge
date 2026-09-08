#!/bin/bash
echo "[*] Starting trustedge framework"
echo "[*] FastAPI server on port 8000"
echo "[*] Streamlit dashboard on port 8500"
echo "[*] Activating Zenity popups"
python main.py &
streamlit run dashboard/app.py --server.port=8500 --server.address=0.0.0.0
