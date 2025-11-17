def int24_be_to_signed(n: int) -> int:
    return n - (1 << 24) if (n & 0x800000) else n


def _deg_from_raw(lat_raw: int, lon_raw: int) -> tuple[float, float]:
    # SmartOne C 24-bit signed fixed-point
    lat = lat_raw * 90.0 / (1 << 23)
    lon = lon_raw * 180.0 / (1 << 23)
    return lat, lon


def _parse_flags(b: bytes) -> dict:
    # Starter map; refine as we verify against spec tables
    f = b[0]
    return {
        "gps_valid": bool(f & 0b1000_0000),
        "battery_low": bool(f & 0b0100_0000),
        "in_motion": bool(f & 0b0010_0000),
        "input1": bool(f & 0b0001_0000),
        "input2": bool(f & 0b0000_1000),
        "raw_flags_hex": b.hex(),
    }


def decode_type0(payload: bytes) -> dict:
    """SmartOne C Type-0 (Standard) 9-byte payload: [type][lat24][lon24][flags2]"""
    if len(payload) != 9:
        raise ValueError("SmartOne C Type-0 expects 9 bytes")
    t = payload[0]
    lat_raw = int24_be_to_signed(int.from_bytes(payload[1:4], "big"))
    lon_raw = int24_be_to_signed(int.from_bytes(payload[4:7], "big"))
    flags = payload[7:9]
    lat, lon = _deg_from_raw(lat_raw, lon_raw)
    out = {"type": t, "lat_raw": lat_raw, "lon_raw": lon_raw, "lat": lat, "lon": lon}
    out.update(_parse_flags(flags))
    return out
