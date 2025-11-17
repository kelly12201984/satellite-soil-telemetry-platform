# Temporary utility (migrated from your script)
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
from .smartone_c import decode_type0

LEAP_SEC = 18

def gps_unix_to_utc(ts: int) -> str:
    return datetime.fromtimestamp(ts - LEAP_SEC, tz=timezone.utc).isoformat()

def parse_stu_messages(xml_str: str):
    root = ET.fromstring(xml_str)
    msgs = []
    for m in root.findall('.//stuMessage'):
        esn = m.findtext('esn')
        ts  = int(m.findtext('unixTime'))
        payload = m.find('payload').text.strip().replace('0x','')
        dec = decode_type0(bytes.fromhex(payload))
        msgs.append({"esn": esn, "gps_time_utc": gps_unix_to_utc(ts), **dec})
    return msgs
