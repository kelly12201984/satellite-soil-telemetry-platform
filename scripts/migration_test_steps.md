# Migration Testing Steps

## Option 1: Test with Local Docker Compose DB (Safest)

1. **Start local database:**
   ```powershell
   cd soilprobe-platform
   docker compose up -d db
   ```

2. **Set DATABASE_URL to local:**
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/soilprobe"
   ```

3. **Check current migration state:**
   ```powershell
   python -m alembic current
   ```

4. **Run migration:**
   ```powershell
   python -m alembic upgrade head
   ```

5. **Verify table exists:**
   ```powershell
   python -c "from sqlalchemy import create_engine, inspect; engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/soilprobe'); inspector = inspect(engine); print('Tables:', inspector.get_table_names()); print('device_config exists:', 'device_config' in inspector.get_table_names())"
   ```

6. **Test rollback (optional):**
   ```powershell
   python -m alembic downgrade -1
   python -m alembic upgrade head
   ```

## Option 2: Test with Neon Branch (Production-like)

1. **In Neon Console:**
   - Create a branch from your prod DB
   - Name it `pre-alerts-test`

2. **Get connection string from Neon branch**

3. **Set DATABASE_URL:**
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg2://<user>:<pass>@<host>/<db>?sslmode=require"
   ```

4. **Run migration:**
   ```powershell
   cd soilprobe-platform
   python -m alembic upgrade head
   ```

5. **Verify:**
   ```powershell
   python scripts/test_migration.py
   ```

## What to Look For

✅ **Success:**
- Migration runs without errors
- `device_config` table appears in database
- All columns are present (device_id, mode, fc_vwc_pct, etc.)

❌ **Failure:**
- Foreign key constraint errors (device table missing)
- Syntax errors in migration file
- Connection errors

## Quick Verification SQL

After migration, you can verify with:

```sql
-- Check table exists
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'device_config';

-- Check columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'device_config';

-- Check foreign key
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE table_name = 'device_config' AND constraint_type = 'FOREIGN KEY';
```

