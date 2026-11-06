# ==============================================================================
# LabTrace - Windows PowerShell Startup Script
# Automatically verifies Python environment, installs dependencies,
# seeds XAMPP MySQL database (if empty), and launches the Flask web server.
# ==============================================================================

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host " LabTrace: Laboratory Equipment Management System" -ForegroundColor Green
Write-Host " Database Theory & Relational Schema Analysis Edition" -ForegroundColor Yellow
Write-Host "===========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python is not installed or not in your system PATH." -ForegroundColor Red
    exit 1
}

# 2. Check Virtual Environment
if (Test-Path ".env\Scripts\Activate.ps1") {
    Write-Host "[*] Activating virtual environment (.env)..." -ForegroundColor Blue
    & .\.env\Scripts\Activate.ps1
}

# 3. Install requirements
Write-Host "[*] Checking and installing Python dependencies..." -ForegroundColor Blue
pip install -r requirements.txt --quiet

# 4. Verify & Seed Database
Write-Host "[*] Checking XAMPP MySQL connectivity and seeding if needed..." -ForegroundColor Blue
python verify_seed.py

# 5. Launch Application
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Application starting on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host " Open your browser to explore the Dashboard & Theory Suite:" -ForegroundColor Yellow
Write-Host "  - Dashboard: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  - Theory & Analysis: http://127.0.0.1:5000/analysis" -ForegroundColor White
Write-Host "  - Interactive ER Diagram: http://127.0.0.1:5000/analysis/er-diagram" -ForegroundColor White
Write-Host "  - Normalization Proofs: http://127.0.0.1:5000/analysis/normalization" -ForegroundColor White
Write-Host "===========================================================" -ForegroundColor Green
Write-Host ""

python app.py

