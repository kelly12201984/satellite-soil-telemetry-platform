# Quick Migration Test Guide

## Fastest Way: Test with Local Docker DB

Run this PowerShell script:

```powershell
cd soilprobe-platform
.\scripts\test_migration_local.ps1
```

This will:
1. ✅ Start local database if not running
2. ✅ Set DATABASE_URL to local
3. ✅ Check current migration state
4. ✅ Run `alembic upgrade head`
5. ✅ Verify `device_config` table exists
6. ✅ Optionally test rollback

## Manual Steps (if script doesn't work)

### 1. Start local database
```powershell
cd soilprobe-platform
docker compose up -d db
```

### 2. Set DATABASE_URL
```powershell
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/soilprobe"
```

### 3. Check current state
```powershell
python -m alembic current
```

### 4. Run migration
```powershell
python -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade d776ab29a494 -> a1b2c3d4e5f6, add device_config table
```

### 5. Verify table exists
```powershell
python -c "from sqlalchemy import create_engine, inspect; engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/soilprobe'); print('device_config' in inspect(engine).get_table_names())"
```

Should print: `True`

## Test Against Neon Branch (Recommended Before Prod)

1. Create branch in Neon console: `pre-alerts-test`
2. Copy connection string
3. Set DATABASE_URL:
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg2://<user>:<pass>@<host>/<db>?sslmode=require"
   ```
4. Run migration:
   ```powershell
   python -m alembic upgrade head
   ```
5. Verify:
   ```powershell
   python scripts/test_migration.py
   ```

## What Success Looks Like

✅ Migration runs without errors  
✅ `device_config` table appears  
✅ All columns present (device_id, mode, fc_vwc_pct, pwp_vwc_pct, etc.)  
✅ Foreign key constraint to `device` table works

## Troubleshooting

**Error: "relation device does not exist"**
- Run existing migrations first: `alembic upgrade d776ab29a494`
- Then: `alembic upgrade head`

**Error: "table device_config already exists"**
- Migration already ran, or table exists from manual creation
- Check: `alembic current` should show `a1b2c3d4e5f6`

**Connection refused**
- Database not running: `docker compose up -d db`
- Wrong DATABASE_URL: check connection string

