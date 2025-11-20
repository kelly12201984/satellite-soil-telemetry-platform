# Test script for Globalstar certification readiness (PowerShell version)
# Tests the /v1/uplink/receive endpoint with various scenarios

param(
    [string]$ApiUrl = "https://api.soilreadings.com",
    [string]$UplinkToken = "y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI=",
    [string]$TestMessageDir = "Test-Messages"
)

$ErrorActionPreference = "Stop"

# Test counter
$script:TestsPassed = 0
$script:TestsFailed = 0

# Helper functions
function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor Blue
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
}

function Write-TestName {
    param([string]$Name)
    Write-Host ""
    Write-Host "▶ TEST: $Name" -ForegroundColor Yellow
}

function Write-Pass {
    param([string]$Message)
    Write-Host "✓ PASS: $Message" -ForegroundColor Green
    $script:TestsPassed++
}

function Write-Fail {
    param([string]$Message)
    Write-Host "✗ FAIL: $Message" -ForegroundColor Red
    $script:TestsFailed++
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ $Message" -ForegroundColor Gray
}

# Test functions
function Test-HealthCheck {
    Write-TestName "Health Check Endpoint"

    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/" -Method Get

        if ($response.status -eq "running") {
            Write-Pass "Health endpoint returned running status"
            Write-Info "Response: $($response | ConvertTo-Json -Compress)"
        } else {
            Write-Fail "Health endpoint did not return expected status"
            Write-Info "Response: $($response | ConvertTo-Json -Compress)"
        }
    } catch {
        Write-Fail "Health check failed with error: $_"
    }
}

function Test-NoTokenNoAllowlist {
    Write-TestName "Request WITHOUT token (should FAIL for non-Globalstar IPs)"

    try {
        $body = '<stuMessages><stuMessage><esn>TEST-001</esn></stuMessage></stuMessages>'
        $headers = @{
            "Content-Type" = "application/xml"
        }

        Invoke-RestMethod -Uri "$ApiUrl/v1/uplink/receive" -Method Post -Headers $headers -Body $body
        Write-Fail "Request without token succeeded (should have failed with 401)"
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401) {
            Write-Pass "Correctly rejected request without token (HTTP 401)"
        } else {
            Write-Fail "Expected HTTP 401, got: $($_.Exception.Response.StatusCode)"
        }
    }
}

function Test-WithToken {
    Write-TestName "Request WITH valid token (should SUCCEED)"

    try {
        $body = '<stuMessages><stuMessage><esn>TEST-TOKEN-001</esn><payload>0200000000000000</payload></stuMessage></stuMessages>'
        $headers = @{
            "Content-Type" = "application/xml"
            "X-Uplink-Token" = $UplinkToken
        }

        $response = Invoke-RestMethod -Uri "$ApiUrl/v1/uplink/receive" -Method Post -Headers $headers -Body $body
        Write-Pass "Request with valid token succeeded (HTTP 200)"
        Write-Info "Response: $($response | ConvertTo-Json -Compress)"
    } catch {
        Write-Fail "Request with valid token failed: $_"
    }
}

function Test-RealPayload {
    Write-TestName "Real SmartOne-C XML payload from test files"

    # Find a test file
    $testFile = Get-ChildItem -Path $TestMessageDir -Filter "StuMessage*.xml" | Select-Object -First 1

    if (-not $testFile) {
        $testFile = Get-Item "$TestMessageDir/StuMessage_Rev8.xml" -ErrorAction SilentlyContinue
    }

    if (-not $testFile) {
        Write-Fail "Test message file not found in $TestMessageDir"
        return
    }

    Write-Info "Using test file: $($testFile.Name)"

    try {
        $body = Get-Content $testFile.FullName -Raw
        $headers = @{
            "Content-Type" = "application/xml"
            "X-Uplink-Token" = $UplinkToken
        }

        $response = Invoke-RestMethod -Uri "$ApiUrl/v1/uplink/receive" -Method Post -Headers $headers -Body $body
        Write-Pass "Real payload ingestion succeeded"
        Write-Info "Response: $($response | ConvertTo-Json -Compress)"
    } catch {
        Write-Fail "Real payload ingestion failed: $_"
    }
}

function Test-InvalidPayload {
    Write-TestName "Invalid XML payload (should return HTTP 400)"

    try {
        $body = '<invalid>xml<without>closing</tags>'
        $headers = @{
            "Content-Type" = "application/xml"
            "X-Uplink-Token" = $UplinkToken
        }

        Invoke-RestMethod -Uri "$ApiUrl/v1/uplink/receive" -Method Post -Headers $headers -Body $body
        Write-Fail "Invalid payload was accepted (should have failed with 400)"
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400) {
            Write-Pass "Invalid payload correctly rejected (HTTP 400)"
        } else {
            Write-Fail "Expected HTTP 400, got: $($_.Exception.Response.StatusCode)"
        }
    }
}

function Test-DataRetrieval {
    Write-TestName "Data Retrieval - Verify ingested data is accessible"

    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/v1/readings/latest?limit=5" -Method Get
        Write-Pass "Latest readings endpoint accessible"
        Write-Info "Found $($response.count) readings in database"
    } catch {
        Write-Fail "Could not retrieve readings: $_"
    }
}

function Test-DevicesEndpoint {
    Write-TestName "Devices List - Verify devices are registered"

    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/v1/devices" -Method Get
        Write-Pass "Devices endpoint accessible ($($response.count) devices registered)"
    } catch {
        Write-Fail "Could not retrieve devices list: $_"
    }
}

# Main execution
function Main {
    Write-Header "Globalstar Certification Readiness Tests"
    Write-Host "Testing endpoint: $ApiUrl/v1/uplink/receive"
    Write-Host "Started: $(Get-Date)"

    # Check test message directory
    if (-not (Test-Path $TestMessageDir)) {
        Write-Host "Error: Must run from repository root directory" -ForegroundColor Red
        Write-Host "Usage: .\scripts\test_globalstar_endpoint.ps1"
        exit 1
    }

    # Run all tests
    Test-HealthCheck
    Test-NoTokenNoAllowlist
    Test-WithToken
    Test-InvalidPayload
    Test-RealPayload
    Test-DataRetrieval
    Test-DevicesEndpoint

    # Summary
    Write-Header "Test Summary"

    $totalTests = $script:TestsPassed + $script:TestsFailed

    Write-Host "Total Tests: $totalTests"
    Write-Host "Passed: $script:TestsPassed" -ForegroundColor Green
    Write-Host "Failed: $script:TestsFailed" -ForegroundColor Red

    if ($script:TestsFailed -eq 0) {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host "  ✓ ALL TESTS PASSED - READY FOR GLOBALSTAR CERTIFICATION" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host ""
        exit 0
    } else {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
        Write-Host "  ✗ SOME TESTS FAILED - REVIEW ISSUES BEFORE CERTIFICATION" -ForegroundColor Red
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# Run main
Main
