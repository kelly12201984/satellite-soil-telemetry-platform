from api.app.db.session import engine
from sqlalchemy import text

def q1(sql: str):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql))]

print("counts:", q1("""
    select
      (select count(*) from device)  as devices,
      (select count(*) from message) as messages,
      (select count(*) from reading) as readings
""")[0])

print("devices:",  q1("select id, esn, name, created_at from device order by id desc limit 5"))
print("messages:", q1("select id, device_id, message_id, timestamp from message order by id desc limit 5"))
print("readings:", q1("select id, message_id, device_id, depth_cm, moisture_pct, temperature_c from reading order by id desc limit 5"))
