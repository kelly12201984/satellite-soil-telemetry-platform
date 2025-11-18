# Test script to verify production deployment with Type-2 soil decoder

$PROD_URL = "https://api.soilreadings.com"
$TOKEN = "y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI="

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing Production Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "1. Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$PROD_URL/"
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
    Write-Host "   Environment: $($health.env)" -ForegroundColor Green
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Send test message with Type-2 payload
Write-Host "2. Sending test message with soil sensor data..." -ForegroundColor Yellow
Write-Host "   Payload: 0x02151516151515544D"
Write-Host "   Expected: 6 readings (10cm, 20cm, 30cm, 40cm, 50cm, 60cm)"
Write-Host ""

$timestamp = Get-Date -Format "dd/MM/yyyy HH:mm:ss 'GMT'"
$messageId = "test-$(Get-Date -UFormat %s)"
$unixTime = [int](Get-Date -UFormat %s)

$xmlPayload = @"
<?xml version="1.0" encoding="UTF-8"?>
<stuMessages xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" timeStamp="$timestamp" messageID="$messageId">
<stuMessage>
<esn>0-5024504</esn>
<unixTime>$unixTime</unixTime>
<gps>N</gps>
<payload length="9" source="pc" encoding="hex">0x02151516151515544D</payload>
</stuMessage>
</stuMessages>
"@

try {
    $response = Invoke-RestMethod -Uri "$PROD_URL/v1/uplink/receive" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/xml"
            "X-Uplink-Token" = $TOKEN
        } `
        -Body $xmlPayload

    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json | Write-Host

    $DEVICE_ID = $response.device_id
    $PREV_READINGS = $response.totals.readings

    Write-Host ""
    Write-Host "   Device ID: $DEVICE_ID" -ForegroundColor Green
    Write-Host "   Total readings in DB: $PREV_READINGS" -ForegroundColor Green
    Write-Host "   (Should have increased by 6 if decoder is working)" -ForegroundColor Cyan
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
    $DEVICE_ID = 5  # Fallback to known device
}
Write-Host ""

# Test 3: Query latest readings
Write-Host "3. Querying latest 6 readings for device $DEVICE_ID..." -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Give DB a moment

try {
    $readings = Invoke-RestMethod -Uri "$PROD_URL/v1/readings/latest?limit=6"

    Write-Host "Latest readings:" -ForegroundColor Green
    foreach ($reading in $readings.items) {
        if ($reading.device_id -eq $DEVICE_ID) {
            Write-Host "   Depth: $($reading.depth_cm) cm | Moisture: $($reading.moisture_pct)% | Temp: $($reading.temperature_c)°C | Device: $($reading.esn)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Test PATCH endpoint
Write-Host "4. Testing device update endpoint..." -ForegroundColor Yellow
try {
    $updateBody = @{ name = "Charlie's Test Probe" } | ConvertTo-Json
    $updateResponse = Invoke-RestMethod -Uri "$PROD_URL/v1/devices/$DEVICE_ID" `
        -Method PATCH `
        -ContentType "application/json" `
        -Body $updateBody

    Write-Host "   Device updated successfully!" -ForegroundColor Green
    Write-Host "   Name: $($updateResponse.name)" -ForegroundColor White
    Write-Host "   ESN: $($updateResponse.esn)" -ForegroundColor White
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Verify device list
Write-Host "5. Verifying device appears in device list..." -ForegroundColor Yellow
try {
    $devices = Invoke-RestMethod -Uri "$PROD_URL/v1/devices"
    $device = $devices | Where-Object { $_.id -eq $DEVICE_ID }

    if ($device) {
        Write-Host "   Found device:" -ForegroundColor Green
        Write-Host "   ID: $($device.id) | Name: $($device.alias) | ESN: $($device.esn)" -ForegroundColor White
    } else {
        Write-Host "   Device not found in list" -ForegroundColor Red
    }
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What to look for:" -ForegroundColor Yellow
Write-Host "✓ 6 new readings with depths: 10, 20, 30, 40, 50, 60 cm" -ForegroundColor White
Write-Host "✓ Moisture values: 21%, 21%, 22%, 21%, 21%, 21%" -ForegroundColor White
Write-Host "✓ Temperature: 20°C" -ForegroundColor White
Write-Host "✓ Device name updated successfully" -ForegroundColor White
Write-Host ""
Write-Host "If you see these, the Type-2 decoder is working! 🎉" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Check dashboard at $PROD_URL/static/readings.html" -ForegroundColor Cyan
