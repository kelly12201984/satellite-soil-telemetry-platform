# BRSense — SmartOne C Delivery Spec (GLOBALSTAR)

**Date:** 2025-11-01 (Updated: 2025-11-03)  
**Status:** PRODUCTION (v1 API deployed, SSL certificates valid until Feb 1, 2026)

This document contains only the parameters Globalstar needs to configure HTTPS delivery from SmartOne C to BRSense (Olho no Solo platform).

---

## 1. HTTPS Destinations

| Purpose | Form reference | URL | Method |
| --- | --- | --- | --- |
| Telemetry uplink | **B2.3** | `https://api.soilreadings.com/v1/uplink/receive` | `POST` |
| Provisioning confirmation | **B4.3** | `https://api.soilreadings.com/v1/uplink/confirmation` | `POST` |

Both endpoints require HTTPS (TLS).

---

## 2. HTTP Headers

- `Content-Type: application/xml` _(Globalstar standard)_ or `application/json`
- `X-Uplink-Token: y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI=` _(required for authorization)_

---

## 3. Payload Schema

### Globalstar Standard XML (Primary Format)

For SmartOne C satellite payloads, the standard Globalstar `stuMessages` envelope with hex-encoded payloads:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<stuMessages timeStamp="15/12/2016 21:00:00 GMT" messageID="abc123">
  <stuMessage>
    <esn>0-99990</esn>
    <unixTime>1034268516</unixTime>
    <gps>N</gps>
    <payload length="9" source="pc" encoding="hex">0xC0560D72DA4AB2445A</payload>
  </stuMessage>
</stuMessages>
```

The hex `payload` from satellite frames will be automatically decoded and parsed.

### Simplified XML (Alternative Format)

For testing or direct integration:

```xml
<envelope>
  <esn>0-5024242</esn>
  <device_name>field-probe-1</device_name>
  <message>
    <reading>
      <moisture>12.3</moisture>
      <temperature_c>23.4</temperature_c>
    </reading>
  </message>
</envelope>
```

### JSON (Alternative Format)

Also supported for testing or API integration:

```json
{
  "esn": "0-5024242",
  "device_name": "field-probe-1",
  "message": {
    "reading": {
      "moisture": 12.3,
      "temperature_c": 23.4
    }
  }
}
```

### Field Definitions
- `esn` _(string, required)_: Device ESN/IMEI/unique ID
- `device_name` _(string, optional)_: Human friendly label
- `message.reading.moisture` _(number, %)_
- `message.reading.temperature_c` _(number, Celsius)_

> Additional metrics (battery, RSSI/SNR, GPS, timestamps, etc.) may be included and will be accepted by the API without breaking.

---

## 4. Expected Responses

Responses are returned in the **same format as the request**:
- XML requests receive XML responses
- JSON requests receive JSON responses

### Uplink Endpoint (`/v1/uplink/receive`)

**XML Response** (when sending XML):
```xml
<?xml version="1.0" encoding="utf-8"?>
<response>
  <device_id>1</device_id>
  <message_id>42</message_id>
  <totals>
    <devices>1</devices>
    <messages>64</messages>
    <readings>64</readings>
  </totals>
</response>
```

**JSON Response** (when sending JSON):
```json
{
  "device_id": 1,
  "message_id": 42,
  "totals": {
    "devices": 1,
    "messages": 64,
    "readings": 64
  }
}
```

### Provisioning Confirmation Endpoint (`/v1/uplink/confirmation`)

**XML Response** (when sending XML):
```xml
<?xml version="1.0" encoding="utf-8"?>
<response>
  <status>ok</status>
  <type>provisioning_confirmation</type>
  <esn>0-99990</esn>
  <ack>true</ack>
</response>
```

**JSON Response** (when sending JSON):
```json
{
  "status": "ok",
  "type": "provisioning_confirmation",
  "esn": "0-99990",
  "ack": true
}
```

- **401 Unauthorized**: missing/invalid `X-Uplink-Token`
- **400 Bad Request**: malformed JSON/XML
- **500 Internal Server Error**: transient server error (enable retries with backoff)

---

## 5. Retry Guidance

- Enable retries on **5xx** with exponential backoff (recommended: 3 attempts)
- Respect idempotency: the backend tolerates safe replays (duplicate messages are handled gracefully)

---

## 6. Throughput

- **MVP scale:** up to a few requests/second
- **Notify us before** higher rates if anticipating >10 req/s sustained

---

## 7. Security

- Keep the token confidential. Rotation available upon request.
- All traffic is encrypted via HTTPS/TLS
- Token must be sent in every request header

---

## 8. Testing & Verification

### Test Endpoint

You can verify connectivity before going live using XML (Globalstar standard format):

```bash
curl -X POST https://api.soilreadings.com/v1/uplink/receive \
  -H "Content-Type: application/xml" \
  -H "X-Uplink-Token: y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI=" \
  -d '<stuMessages><stuMessage><esn>TEST-001</esn><payload>0200000000000000</payload></stuMessage></stuMessages>'
```

Expected XML response:
```xml
<?xml version="1.0" encoding="utf-8"?>
<response><device_id>X</device_id><message_id>Y</message_id><totals>...</totals></response>
```

Or using JSON for testing:

```bash
curl -X POST https://api.soilreadings.com/v1/uplink/receive \
  -H "Content-Type: application/json" \
  -H "X-Uplink-Token: y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI=" \
  -d '{
    "esn": "TEST-001",
    "message": {
      "reading": {
        "moisture": 15.5,
        "temperature_c": 25.0
      }
    }
  }'
```

Expected JSON response: `{"device_id":X,"message_id":Y,"totals":{...}}`

### Health Check

The platform provides two endpoints for health/connectivity checks:

**Root Endpoint:**
```bash
curl https://api.soilreadings.com/
```

Expected: `{"status":"running","env":"prod"}`

**Ping Endpoint:**
```bash
curl https://api.soilreadings.com/ping
```

Expected: `{"status":"ok","message":"pong"}`

> Both endpoints are publicly accessible (no authentication required) and can be used for monitoring and connectivity verification.

---

## 9. Data Access

After successful ingestion, data is available via:

- **API:** `GET /v1/readings/latest?limit=N` (at `https://api.soilreadings.com/v1/readings/latest`)
- **Web UI:** `https://api.soilreadings.com/static/readings.html`

---

## Contact

- **Platform:** BRSense Platform API (Olho no Solo)
- **Deployment:** Fly.io (São Paulo region)
- **Database:** Neon Postgres (AWS South America East)
- **Version:** v1 (stable, backward-compatible)

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-01

