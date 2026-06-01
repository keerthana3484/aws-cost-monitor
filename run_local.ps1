# PowerShell script to run the AWS Cost Monitor locally on Windows

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "[*] Priming local AWS Cost Monitor environment..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Start Docker container for DynamoDB Local
Write-Host ""
Write-Host "[1] Starting DynamoDB Local Container..." -ForegroundColor Yellow
docker-compose up -d

# 2. Wait for DynamoDB local to accept connections
Write-Host ""
Write-Host "[2] Waiting for DynamoDB local (port 8000) to spin up..." -ForegroundColor Yellow
for ($i=1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        Write-Host "SUCCESS: DynamoDB Local is ready and accepting requests." -ForegroundColor Green
        break
    } catch {
        Write-Host "   [Waiting for DB engine... attempt $i/30]" -ForegroundColor DarkGray
        Start-Sleep -Seconds 1
    }
}

# 3. Create tables, Seed configurations, and Backfill metrics
Write-Host ""
Write-Host "[3] Setting up database tables and seeding 30-day metrics..." -ForegroundColor Yellow
python scripts/setup_dynamodb.py
python scripts/seed_config.py
python scripts/backfill_metrics.py

# 4. Launching SAM Local API in a new PowerShell window
Write-Host ""
Write-Host "[4] Launching AWS SAM Local API on Port 3001 in a new window..." -ForegroundColor Green

$apiCommand = @'
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ACCESS_KEY_ID="mock_local_key"
$env:AWS_SECRET_ACCESS_KEY="mock_local_secret"
$env:DYNAMODB_ENDPOINT="http://localhost:8000"
$env:DYNAMODB_ENDPOINT_URL="http://localhost:8000"
$env:DYNAMODB_TABLE_COST="CostMetrics"
$env:DYNAMODB_TABLE_CONFIG="AlertConfig"
$env:SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:aws-cost-alerts-topic"
sam local start-api --port 3001
'@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand

# 5. Launching React Dashboard in a new PowerShell window
Write-Host ""
Write-Host "[5] Launching React Frontend Dashboard in a new window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd dashboard; npm start"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "SUCCESS: Portals started! Check the newly spawned windows." -ForegroundColor Green
Write-Host "Dashboard will be available at http://localhost:3000" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
