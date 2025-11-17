#!/usr/bin/env python3
"""
Test the device_config migration locally.
This verifies the table exists and has all required columns.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import api
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect  # pyright: ignore[reportMissingImports]
from api.app.settings import settings

def test_migration():
    """Test that device_config table exists and has correct structure."""
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL") or str(settings.DATABASE_URL)
    
    try:
        engine = create_engine(db_url)
        
        # Check if device_config table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "device_config" not in tables:
            print("ERROR: device_config table not found!")
            print("   Run: alembic upgrade head")
            return False
        
        print("SUCCESS: device_config table exists!")
        
        # Verify columns
        columns = {col["name"]: col for col in inspector.get_columns("device_config")}
        required_cols = [
            "device_id", "mode", "fc_vwc_pct", "pwp_vwc_pct",
            "expected_interval_min", "farm_id", "lat", "lon", "updated_at"
        ]
        
        missing = [col for col in required_cols if col not in columns]
        if missing:
            print(f"ERROR: Missing columns: {missing}")
            return False
        
        print(f"SUCCESS: All {len(required_cols)} required columns present")
        print(f"   Columns: {', '.join(required_cols)}")
        
        # Check foreign key
        fks = inspector.get_foreign_keys("device_config")
        if fks:
            print(f"SUCCESS: Foreign key constraint exists")
        else:
            print("WARNING: No foreign key constraint found")
        
        return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)

