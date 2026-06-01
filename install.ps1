# PowerShell script to install all dependencies for the AWS Cost Monitor on Windows

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "[*] Installing AWS Cost Monitor Dependencies..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Root python dependencies
Write-Host ""
Write-Host "[1] Installing root development dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 2. Metric Collector dependencies
Write-Host ""
Write-Host "[2] Installing Metric Collector dependencies..." -ForegroundColor Yellow
pip install -r functions/metric-collector/requirements.txt -t functions/metric-collector/

# 3. Alert Checker dependencies
Write-Host ""
Write-Host "[3] Installing Alert Checker dependencies..." -ForegroundColor Yellow
pip install -r functions/alert-checker/requirements.txt -t functions/alert-checker/

# 4. API Handler dependencies
Write-Host ""
Write-Host "[4] Installing API Handler dependencies..." -ForegroundColor Yellow
pip install -r functions/api-handler/requirements.txt -t functions/api-handler/

# 5. Dashboard dependencies
Write-Host ""
Write-Host "[5] Installing React dashboard dependencies..." -ForegroundColor Yellow
cd dashboard
npm install
cd ..

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "SUCCESS: All dependencies installed successfully!" -ForegroundColor Green
Write-Host "Please run the app using: .\run_local.ps1" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
