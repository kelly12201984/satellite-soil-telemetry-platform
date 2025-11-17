#!/usr/bin/env python3
"""
Find database connection information from various sources.
"""
import os
import sys
from pathlib import Path

def find_db_info():
    """Search for database connection info."""
    print("🔍 Searching for database connection information...\n")
    
    # 1. Check environment variables
    print("1. Environment Variables:")
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Mask password for display
        masked = db_url.split("@")[0].split(":")[:-1] + ["***"] + db_url.split("@")[1:] if "@" in db_url and ":" in db_url else db_url
        print(f"   ✅ DATABASE_URL found: {masked}")
        print(f"   Full URL (hidden): {db_url[:50]}...")
    else:
        print("   ❌ DATABASE_URL not set in environment")
    print()
    
    # 2. Check .env files
    print("2. .env Files:")
    env_files = [
        ".env",
        ".env.local",
        ".env.prod",
        ".env.compose",
        "api/.env",
        "api/.env.prod",
    ]
    
    found_env = False
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            found_env = True
            print(f"   ✅ Found: {env_file}")
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DATABASE_URL") and "=" in line:
                            # Mask password
                            if "@" in line:
                                parts = line.split("://")
                                if len(parts) > 1:
                                    user_pass = parts[1].split("@")[0]
                                    if ":" in user_pass:
                                        user = user_pass.split(":")[0]
                                        masked_line = f"{parts[0]}://{user}:***@{parts[1].split('@')[1]}"
                                        print(f"      {masked_line}")
                                    else:
                                        print(f"      {line[:80]}...")
                                else:
                                    print(f"      {line[:80]}...")
                            else:
                                print(f"      {line[:80]}...")
            except Exception as e:
                print(f"      Error reading: {e}")
    
    if not found_env:
        print("   ❌ No .env files found")
    print()
    
    # 3. Check settings.py for defaults
    print("3. Settings File:")
    try:
        sys.path.insert(0, str(Path.cwd()))
        from api.app.settings import settings
        default_url = str(settings.DATABASE_URL)
        if "postgres" in default_url.lower():
            # Mask password
            if "@" in default_url:
                parts = default_url.split("://")
                if len(parts) > 1:
                    user_pass = parts[1].split("@")[0]
                    if ":" in user_pass:
                        user = user_pass.split(":")[0]
                        masked = f"{parts[0]}://{user}:***@{parts[1].split('@')[1]}"
                        print(f"   Default DATABASE_URL: {masked}")
                    else:
                        print(f"   Default DATABASE_URL: {default_url[:80]}...")
                else:
                    print(f"   Default DATABASE_URL: {default_url[:80]}...")
            else:
                print(f"   Default DATABASE_URL: {default_url[:80]}...")
        else:
            print(f"   Default: {default_url[:80]}...")
    except Exception as e:
        print(f"   ❌ Could not load settings: {e}")
    print()
    
    # 4. Check Fly.io secrets (if flyctl is available)
    print("4. Fly.io Secrets:")
    try:
        import subprocess
        result = subprocess.run(
            ["fly", "secrets", "list", "-a", "soilprobe-api-floral-sound-9539"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "DATABASE_URL" in line:
                    print(f"   ✅ DATABASE_URL found in Fly.io secrets")
                    print(f"   (Value is masked in fly secrets list)")
                    break
            else:
                print("   ❌ DATABASE_URL not found in Fly.io secrets")
        else:
            print("   ⚠️  Could not check Fly.io (flyctl not available or not logged in)")
    except Exception:
        print("   ⚠️  Could not check Fly.io (flyctl not available)")
    print()
    
    # 5. Check recent commands/history (shell history)
    print("5. Recommendations:")
    print("   - Check your Neon dashboard for connection strings")
    print("   - Look for previous commands in PowerShell history")
    print("   - Check if you have a branch connection string")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY:")
    if db_url and "neon" in db_url.lower():
        print("✅ DATABASE_URL is set (appears to be Neon)")
        print("   You can use this value for migration")
    elif db_url:
        print("⚠️  DATABASE_URL is set but doesn't appear to be Neon")
        print("   Double-check this is the correct database")
    else:
        print("❌ DATABASE_URL not found")
        print("   You need to:")
        print("   1. Get connection string from Neon dashboard")
        print("   2. Set it: $env:DATABASE_URL = 'postgresql+psycopg2://...'")
        print("   3. Or create a branch in Neon and use that connection string")

if __name__ == "__main__":
    find_db_info()

