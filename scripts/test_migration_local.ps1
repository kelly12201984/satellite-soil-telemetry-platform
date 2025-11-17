# PowerShell script to test device_config migration locally
# Make sure you're in the soilprobe-platform directory and have venv activated

Write-Host "Testing device_config Migration" -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNING: Virtual environment not detected!" -ForegroundColor Yellow
    Write-Host "   Activating .venv..." -ForegroundColor Gray
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    } else {
        Write-Host "   ERROR: .venv not found. Please activate your virtual environment first." -ForegroundColor Red
        Write-Host "   Run: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        exit 1
    }
}

# Step 1: Check if local DB is running
Write-Host "Step 1: Checking local database..." -ForegroundColor Yellow
$dbRunning = docker compose -f docker-compose.yml ps db --format json | ConvertFrom-Json | Where-Object { $_.State -eq "running" }
if (-not $dbRunning) {
    Write-Host "   WARNING: Local database not running. Starting it..." -ForegroundColor Yellow
    docker compose -f docker-compose.yml up -d db
    Start-Sleep -Seconds 5
    Write-Host "   SUCCESS: Database started" -ForegroundColor Green
} else {
    Write-Host "   SUCCESS: Database is running" -ForegroundColor Green
}

# Step 2: Set DATABASE_URL to local
Write-Host ""
Write-Host "Step 2: Setting DATABASE_URL to local..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/soilprobe"
Write-Host "   SUCCESS: DATABASE_URL set to local" -ForegroundColor Green

# Step 3: Check current migration state
Write-Host ""
Write-Host "Step 3: Checking current migration state..." -ForegroundColor Yellow
$current = python -m alembic current 2>&1
Write-Host "   Current revision: $current" -ForegroundColor Cyan

# Step 4: Show migration history
Write-Host ""
Write-Host "Step 4: Migration history..." -ForegroundColor Yellow
python -m alembic history | Select-Object -Last 5
Write-Host ""

# Step 5: Run migration
Write-Host "Step 5: Running migration..." -ForegroundColor Yellow
Write-Host "   Running: alembic upgrade head" -ForegroundColor Gray
python -m alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Write-Host "   SUCCESS: Migration completed successfully!" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Migration failed!" -ForegroundColor Red
    exit 1
}

# Step 6: Verify table exists
Write-Host ""
Write-Host "Step 6: Verifying device_config table..." -ForegroundColor Yellow
# Change to project root so Python can find api module
Push-Location
Set-Location $PSScriptRoot\..
$verify = python scripts/test_migration.py 2>&1
Pop-Location
if ($LASTEXITCODE -eq 0) {
    Write-Host "   SUCCESS: device_config table exists!" -ForegroundColor Green
    Write-Host $verify
} else {
    Write-Host "   ERROR: device_config table not found!" -ForegroundColor Red
    Write-Host $verify
    exit 1
}

# Step 7: Test rollback (optional)
Write-Host ""
Write-Host "Step 7: Testing rollback (optional)..." -ForegroundColor Yellow
$rollback = Read-Host "   Test rollback? (y/N)"
if ($rollback -eq "y") {
    Write-Host "   Rolling back..." -ForegroundColor Gray
    python -m alembic downgrade -1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   SUCCESS: Rollback successful" -ForegroundColor Green
        Write-Host "   Re-running migration..." -ForegroundColor Gray
        python -m alembic upgrade head
        Write-Host "   SUCCESS: Migration re-applied" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "SUCCESS: Migration test complete!" -ForegroundColor Green
Write-Host "   You can now test against Neon branch or deploy to production." -ForegroundColor Cyan
