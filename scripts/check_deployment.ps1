# Check deployment status and UI URLs
Write-Host "Checking Deployment Status" -ForegroundColor Cyan
Write-Host ""

# Check Fly.io status
Write-Host "1. Fly.io App Status:" -ForegroundColor Yellow
fly status -a soilprobe-api-floral-sound-9539

Write-Host ""
Write-Host "2. Recent Deployments:" -ForegroundColor Yellow
fly releases -a soilprobe-api-floral-sound-9539 | Select-Object -First 5

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "UI URLs:" -ForegroundColor Green
Write-Host ""
Write-Host "Simple HTML Dashboard:" -ForegroundColor Yellow
Write-Host "  https://api.soilreadings.com/readings" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Yellow
Write-Host "  Health: https://api.soilreadings.com/" -ForegroundColor Gray
Write-Host "  Devices: https://api.soilreadings.com/v1/devices/attention" -ForegroundColor Gray
Write-Host "  Metrics: https://api.soilreadings.com/v1/metrics/summary" -ForegroundColor Gray
Write-Host ""
Write-Host "React Frontend (if deployed):" -ForegroundColor Yellow
Write-Host "  Local dev: http://localhost:5173" -ForegroundColor Gray
Write-Host "  (Not yet deployed to production)" -ForegroundColor Gray
Write-Host ""

