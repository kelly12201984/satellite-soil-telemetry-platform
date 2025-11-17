# scripts/init_db.py
# Create all tables on the DB pointed to by ENV_FILE (.env.dev -> Postgres)

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.app.db.session import engine
# Import ALL model modules so their tables are registered on Base.metadata
from api.app.models import device, message, reading

# Prefer a shared Base if your models define one (common pattern)
Base = getattr(device, "Base", None) or getattr(message, "Base", None)
if not Base:
    raise SystemExit("Could not find declarative Base on your models.")

Base.metadata.create_all(bind=engine)

print(f"Created tables on: {engine.url}")
for tbl in Base.metadata.sorted_tables:
    print(f"- {tbl.name}")
