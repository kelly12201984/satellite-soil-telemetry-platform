# Testing the New Irrigation Alerts Endpoints

## Quick Test Script

Run the automated test:

```powershell
cd C:\Users\kelly\Charlie_APP\Olho_no_solo\soilprobe-platform
.\scripts\test_endpoints.ps1
```

Or test against localhost (if API is running locally):

```powershell
.\scripts\test_endpoints.ps1 -BaseUrl "http://localhost:8000"
```

## Manual Testing with curl

### 1. Health Check
```powershell
curl.exe https://api.soilreadings.com/
```

Expected: `{"status":"running","env":"prod"}`

### 2. Devices Attention (New Status Logic)
```powershell
curl.exe "https://api.soilreadings.com/v1/devices/attention?limit=10"
```

**What to check:**
- Returns JSON array
- Each device has: `device_id`, `alias`, `status`, `last_seen`, `moisture30`, `battery_hint`
- Status values: `red`, `amber`, `green`, `blue`, `stale`, `offline`, `gray`
- Devices sorted worst → best (red first, green last)

**Example response:**
```json
[
  {
    "device_id": 4,
    "alias": "Field B - Center",
    "status": "red",
    "last_seen": "23h",
    "moisture30": 20.8,
    "battery_hint": "unknown"
  },
  {
    "device_id": 3,
    "alias": "Field A - South",
    "status": "amber",
    "last_seen": "23h",
    "moisture30": 25.8,
    "battery_hint": "unknown"
  }
]
```

### 3. Devices List (With Status)
```powershell
curl.exe "https://api.soilreadings.com/v1/devices"
```

**What to check:**
- Each device includes `status` field
- Includes `lat` and `lon` if configured

### 4. Metrics Summary (Updated)
```powershell
curl.exe "https://api.soilreadings.com/v1/metrics/summary?from=2025-10-01T00:00:00Z&to=2025-11-04T23:59:59Z"
```

**What to check:**
- `devices_needing_attention` array
- Each device in array has `status` field (should be `red` or `amber`)

### 5. Status Sorting Verification
```powershell
curl.exe "https://api.soilreadings.com/v1/devices/attention?limit=100" | ConvertFrom-Json | Group-Object status
```

**What to check:**
- Devices should be grouped by status
- Counts show how many devices in each status
- Red devices should appear first

## Expected Status Values

- **red**: Moisture critically low (needs irrigation now)
- **amber**: Moisture low (plan irrigation)
- **green**: Moisture OK (target range)
- **blue**: Saturated/post-rain (leaching risk)
- **stale**: No data > 3× expected interval
- **offline**: No data > 24 hours
- **gray**: Alerts disabled or no data

## Troubleshooting

**Empty arrays**: This is normal if you haven't ingested readings yet. The endpoints will work once you have data.

**500 errors**: Check Fly.io logs:
```powershell
fly logs -a soilprobe-api-floral-sound-9539
```

**Wrong status values**: Make sure Fly.io secrets are set correctly (MOISTURE_RED_MAX, etc.)

**Status not sorting**: Check that the backend code is deployed (run `fly deploy`)

