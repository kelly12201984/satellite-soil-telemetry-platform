import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from api.app.db.session import engine  # uses ENV_FILE (.env.dev for PG)

def q_all(sql: str):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql))]

print("DB URL:", engine.url)

counts = q_all("""
  SELECT
    (SELECT COUNT(*) FROM device)  AS devices,
    (SELECT COUNT(*) FROM message) AS messages,
    (SELECT COUNT(*) FROM reading) AS readings
""")[0]
print("counts:", counts)

print("devices:",  q_all("SELECT * FROM device  ORDER BY id DESC LIMIT 5"))
print("messages:", q_all("SELECT * FROM message ORDER BY id DESC LIMIT 5"))
print("readings:", q_all("SELECT * FROM reading ORDER BY id DESC LIMIT 5"))
