# PowerShell script to get Fly.io secrets (including DATABASE_URL)
Write-Host "Getting Fly.io secrets for app: soilprobe-api-floral-sound-9539" -ForegroundColor Cyan
Write-Host ""

# Check if flyctl is available
$flyExists = Get-Command fly -ErrorAction SilentlyContinue
if (-not $flyExists) {
    Write-Host "ERROR: flyctl not found. Please install it first." -ForegroundColor Red
    exit 1
}

# List all secrets
Write-Host "Fetching secrets..." -ForegroundColor Yellow
fly secrets list -a soilprobe-api-floral-sound-9539

Write-Host ""
Write-Host "Note: Secret values are masked for security." -ForegroundColor Gray
Write-Host "To see if DATABASE_URL is set, look for it in the list above." -ForegroundColor Gray
Write-Host ""
Write-Host "To get the actual connection string:" -ForegroundColor Yellow
Write-Host "  1. Check your Neon dashboard" -ForegroundColor Cyan
Write-Host "  2. Or check Fly.io dashboard: https://fly.io/apps/soilprobe-api-floral-sound-9539/secrets" -ForegroundColor Cyan

