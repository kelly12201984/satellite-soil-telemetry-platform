# Deployment Checklist - Irrigation Alerts (v1)

## 0) Prep (60 seconds)

Make sure your `DATABASE_URL` points where you expect before each step.

Keep these envs ready (same values you used earlier):

```powershell
ALERTS_ENABLED=true
EXPECTED_INTERVAL_MIN=60
STALE_FACTOR=3
OFFLINE_HOURS=24
MOISTURE_RED_MAX=18
MOISTURE_AMBER_MAX=24
MOISTURE_GREEN_MAX=36
MOISTURE_BLUE_MIN=40
```

**Note:** ChatGPT's plan had a typo: `MOISTURE_BLUE_MIN_MIN=40` → should be `MOISTURE_BLUE_MIN=40`

## 1) Safe migration dry-run (Neon branch)

**Why:** Neon lets you create a branch; test the Alembic upgrade there first.

1. In Neon console: Create branch from your prod DB (name it `pre-alerts-test`)
2. Copy that branch's connection string → set it locally:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://<user>:<pass>@<host>/<db>?sslmode=require"
```

3. From repo root:

```powershell
cd soilprobe-platform
alembic upgrade head
```

**Expect:** Alembic completes with no errors; `device_config` table exists.

## 2) Local smoke test (against the branch)

Run the API locally (however you normally do it—uvicorn or docker compose up). Then:

```powershell
# health
curl.exe http://localhost:8000/

# attention list (should return [] or devices if you already have some)
curl.exe "http://localhost:8000/v1/devices/attention?limit=10"

# devices list
curl.exe "http://localhost:8000/v1/devices"
```

If you want, insert 1–2 tiny mock rows into the branch to verify status sorting works (optional).

## 3) Migrate prod Neon

When the branch looks good, point `DATABASE_URL` to prod Neon and run:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://<user>:<pass>@<host>/<db>?sslmode=require"
alembic upgrade head
```

**Rollback plan:** `alembic downgrade -1` (or switch Neon to the pre-migration branch if needed).

## 4) Ensure Fly has new env + deploy

Set (or re-set) secrets on Fly to match your .env:

```powershell
fly secrets set `
  ALERTS_ENABLED=true `
  EXPECTED_INTERVAL_MIN=60 `
  STALE_FACTOR=3 `
  OFFLINE_HOURS=24 `
  MOISTURE_RED_MAX=18 `
  MOISTURE_AMBER_MAX=24 `
  MOISTURE_GREEN_MAX=36 `
  MOISTURE_BLUE_MIN=40
```

**Note:** Fix the typo from ChatGPT's plan - use `MOISTURE_BLUE_MIN=40`, not `MOISTURE_BLUE_MIN_MIN=40`.

Then deploy:

```powershell
fly deploy
fly status
```

## 5) Prod smoke test (the new endpoints)

```powershell
# Health (prod, through Cloudflare)
curl.exe https://api.soilreadings.com/

# Attention list (should be sorted RED > AMBER > STALE > OFFLINE > BLUE > GREEN)
curl.exe "https://api.soilreadings.com/v1/devices/attention?limit=10"

# Devices list
curl.exe "https://api.soilreadings.com/v1/devices"

# Optional: latest readings window (should handle empty cleanly)
curl.exe "https://api.soilreadings.com/v1/readings/latest?limit=5"
```

**What "good" looks like:**
- `/` → `{"status":"running","env":"prod"}`
- `/v1/devices/attention` → valid JSON array (empty is fine if you haven't ingested).
- No 500s; errors are clean 4xx with JSON bodies.

## 6) Quick verifier script

Run the verification script:

```powershell
cd soilprobe-platform
python scripts/verify_status.py
```

Or use PowerShell one-liner:

```powershell
(Invoke-WebRequest "https://api.soilreadings.com/v1/devices/attention?limit=1000").Content | ConvertFrom-Json | Group-Object status | Select-Object Count,Name
```

**Expect** a table like:
```
Count Name
----- ----
    1 red
    2 amber
    5 green
```

(Counts can be 0 if you haven't decoded readings yet—this just confirms endpoint wiring.)

## When to move to UI work

After Step 5 is green, go ahead with the UI todos (time presets, map pins, attention card polish). You've proven backend + schema are solid.

## If something blows up

- **Alembic error** → run on the Neon branch again and fix locally; only touch prod once it passes.
- **500s on endpoints** → `fly logs -a soilprobe-api-floral-sound-9539` and check the stack.
- **Cloudflare 525/SSL weirdness** → re-run `fly certs check api.soilreadings.com` and make sure the cert is Ready.

