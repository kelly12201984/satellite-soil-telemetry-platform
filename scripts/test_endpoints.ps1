# PowerShell script to test the new irrigation alerts endpoints

param(
    [string]$BaseUrl = "https://api.soilreadings.com"
)

Write-Host "Testing Irrigation Alerts Endpoints" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Gray
Write-Host ""

# Test 1: Health check
Write-Host "1. Health Check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get
    Write-Host "   SUCCESS: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Devices Attention (new status logic)
Write-Host "2. Devices Attention (new status logic):" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/v1/devices/attention?limit=10" -Method Get
    Write-Host "   SUCCESS: Found $($response.Count) devices" -ForegroundColor Green
    
    if ($response.Count -gt 0) {
        Write-Host "   First device:" -ForegroundColor Cyan
        $first = $response[0]
        Write-Host "      Device ID: $($first.device_id)" -ForegroundColor Gray
        Write-Host "      Alias: $($first.alias)" -ForegroundColor Gray
        Write-Host "      Status: $($first.status)" -ForegroundColor Gray
        Write-Host "      Last Seen: $($first.last_seen)" -ForegroundColor Gray
        Write-Host "      Moisture 30cm: $($first.moisture30)" -ForegroundColor Gray
        
        # Count by status
        $statusCounts = $response | Group-Object status | Select-Object Count, Name
        Write-Host "   Status distribution:" -ForegroundColor Cyan
        foreach ($stat in $statusCounts) {
            Write-Host "      $($stat.Name): $($stat.Count)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   No devices found (this is OK if you haven't ingested data yet)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
    Write-Host "   Response: $($_.Exception.Response)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Devices List (with status)
Write-Host "3. Devices List (with status):" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/v1/devices" -Method Get
    Write-Host "   SUCCESS: Found $($response.Count) devices" -ForegroundColor Green
    
    if ($response.Count -gt 0) {
        Write-Host "   Sample device:" -ForegroundColor Cyan
        $first = $response[0]
        Write-Host "      ID: $($first.id)" -ForegroundColor Gray
        Write-Host "      Alias: $($first.alias)" -ForegroundColor Gray
        Write-Host "      Status: $($first.status)" -ForegroundColor Gray
        Write-Host "      Lat/Lon: $($first.lat), $($first.lon)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Metrics Summary (updated to use new status)
Write-Host "4. Metrics Summary (with attention devices):" -ForegroundColor Yellow
try {
    $fromDate = (Get-Date).AddDays(-30).ToString("yyyy-MM-ddTHH:mm:ssZ")
    $toDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    $url = "$BaseUrl/v1/metrics/summary?from=$fromDate&to=$toDate"
    
    $response = Invoke-RestMethod -Uri $url -Method Get
    Write-Host "   SUCCESS" -ForegroundColor Green
    Write-Host "      Avg Moisture: $($response.avg_moisture)%" -ForegroundColor Gray
    Write-Host "      Avg Temp: $($response.avg_temp)°C" -ForegroundColor Gray
    Write-Host "      Devices needing attention: $($response.devices_needing_attention.Count)" -ForegroundColor Gray
    Write-Host "      Last Reading: $($response.last_reading_at)" -ForegroundColor Gray
    
    if ($response.devices_needing_attention.Count -gt 0) {
        Write-Host "   Attention devices:" -ForegroundColor Cyan
        foreach ($dev in $response.devices_needing_attention) {
            Write-Host "      - $($dev.alias) (Status: $($dev.status), Moisture: $($dev.avg_moisture_30cm)%)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Check if status sorting is correct
Write-Host "5. Status Sorting Check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/v1/devices/attention?limit=100" -Method Get
    
    if ($response.Count -gt 1) {
        $statusOrder = @("red", "amber", "stale", "offline", "blue", "green", "gray")
        $correctOrder = $true
        
        for ($i = 0; $i -lt ($response.Count - 1); $i++) {
            $currentStatus = $response[$i].status
            $nextStatus = $response[$i + 1].status
            
            $currentIndex = [array]::IndexOf($statusOrder, $currentStatus)
            $nextIndex = [array]::IndexOf($statusOrder, $nextStatus)
            
            if ($currentIndex -gt $nextIndex) {
                $correctOrder = $false
                break
            }
        }
        
        if ($correctOrder) {
            Write-Host "   SUCCESS: Devices are sorted correctly (worst → best)" -ForegroundColor Green
        } else {
            Write-Host "   WARNING: Sorting may not be correct" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   SKIP: Need at least 2 devices to test sorting" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "What to look for:" -ForegroundColor Yellow
Write-Host "  - Status values should be: red, amber, green, blue, stale, offline, or gray" -ForegroundColor Gray
Write-Host "  - Devices should be sorted worst → best (red → amber → stale → offline → blue → green)" -ForegroundColor Gray
Write-Host "  - If you see empty arrays, that's OK if you haven't ingested data yet" -ForegroundColor Gray

