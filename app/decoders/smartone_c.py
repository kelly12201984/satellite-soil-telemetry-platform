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


def decode_type2_soil(payload: bytes) -> list[dict]:
    """
    SmartOne C Type-2 (Soil Sensor) 9-byte payload:
    [type=0x02][moisture1][moisture2][moisture3][moisture4][moisture5][moisture6][temp_high][temp_low/crc]

    Returns list of readings with depth_cm, moisture_pct, temperature_c
    Depths: 10cm, 20cm, 30cm, 40cm, 50cm, 60cm (every 10cm from 10-60cm)
    """
    if len(payload) != 9:
        raise ValueError("SmartOne C Type-2 soil sensor expects 9 bytes")

    if payload[0] != 0x02:
        raise ValueError(f"Expected type 0x02, got {hex(payload[0])}")

    # Extract moisture readings (bytes 1-6) - values are percentages in hex
    moisture_values = [payload[i] for i in range(1, 7)]

    # Extract temperature (bytes 7-8)
    # Interpretation: byte 7 could be temp in C, byte 8 is checksum
    temp_byte = payload[7]
    # Based on 0x54 = 84, if we subtract 64 (0x40), we get 20C - reasonable!
    temperature_c = float(temp_byte - 0x40)  # Offset of 64 gives reasonable soil temps

    # Map moisture readings to depths: 10cm, 20cm, 30cm, 40cm, 50cm, 60cm
    depths_cm = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]

    readings = []
    for i, depth in enumerate(depths_cm):
        readings.append({
            "depth_cm": depth,
            "moisture_pct": float(moisture_values[i]),
            "temperature_c": temperature_c,
        })

    return readings
