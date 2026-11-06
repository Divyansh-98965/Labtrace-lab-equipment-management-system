#!/usr/bin/env bash
# ==============================================================================
# LabTrace - Linux / macOS Bash Startup Script
# Automatically verifies Python environment, installs dependencies,
# seeds MySQL database (if empty), and launches the Flask web server.
# ==============================================================================

set -e

echo -e "\033[1;36m===========================================================\033[0m"
echo -e "\033[1;32m LabTrace: Laboratory Equipment Management System\033[0m"
echo -e "\033[1;33m Database Theory & Relational Schema Analysis Edition\033[0m"
echo -e "\033[1;36m===========================================================\033[0m"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m[ERROR] python3 could not be found in PATH.\033[0m"
    exit 1
fi

# 2. Virtual environment activation if present
if [ -d ".env" ]; then
    echo -e "\033[1;34m[*] Activating virtual environment (.env)...\033[0m"
    source .env/bin/activate || source .env/Scripts/activate || true
fi

# 3. Install requirements
echo -e "\033[1;34m[*] Checking dependencies...\033[0m"
pip install -r requirements.txt --quiet

# 4. Run Seed Verification
echo -e "\033[1;34m[*] Verifying MySQL database and seeding 12 tables...\033[0m"
python3 verify_seed.py || python verify_seed.py

# 5. Launch Application
echo ""
echo -e "\033[1;32m===========================================================\033[0m"
echo -e "\033[1;32m [SUCCESS] Starting Flask server on http://127.0.0.1:5000\033[0m"
echo -e "\033[1;33m Open your browser to explore the Dashboard & Theory Suite:\033[0m"
echo -e "  - Dashboard: http://127.0.0.1:5000"
echo -e "  - Theory & Analysis: http://127.0.0.1:5000/analysis"
echo -e "  - Interactive ER Diagram: http://127.0.0.1:5000/analysis/er-diagram"
echo -e "\033[1;32m===========================================================\033[0m"
echo ""

python3 app.py || python app.py

