#!/bin/bash
# Test script to verify production deployment with Type-2 soil decoder

PROD_URL="https://api.soilreadings.com"
TOKEN="y7mlrffdn9XxPVR1SP9tt8iurW6XgZEfl4JpfcKv5eI="

echo "=========================================="
echo "Testing Production Deployment"
echo "=========================================="
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$PROD_URL/" | jq '.' || echo "Failed"
echo ""

# Test 2: Send test message with Type-2 payload
echo "2. Sending test message with soil sensor data..."
echo "   Payload: 0x02151516151515544D"
echo "   Expected: 6 readings (10cm, 20cm, 30cm, 40cm, 50cm, 60cm)"
echo ""

RESPONSE=$(curl -s -X POST "$PROD_URL/v1/uplink/receive" \
  -H "Content-Type: application/xml" \
  -H "X-Uplink-Token: $TOKEN" \
  --data-binary @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<stuMessages xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" timeStamp="17/11/2025 20:00:00 GMT" messageID="test-$(date +%s)">
<stuMessage>
<esn>0-5024504</esn>
<unixTime>$(date +%s)</unixTime>
<gps>N</gps>
<payload length="9" source="pc" encoding="hex">0x02151516151515544D</payload>
</stuMessage>
</stuMessages>
EOF
)

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

# Extract device_id from response
DEVICE_ID=$(echo "$RESPONSE" | jq -r '.device_id')
PREV_READINGS=$(echo "$RESPONSE" | jq -r '.totals.readings')

echo "   Device ID: $DEVICE_ID"
echo "   Previous total readings: $PREV_READINGS"
echo ""

# Test 3: Query latest readings for this device
echo "3. Querying latest readings (should show 6 new readings)..."
sleep 2  # Give DB a moment
curl -s "$PROD_URL/v1/readings/latest?limit=6" | jq '.items[] | {depth_cm, moisture_pct, temperature_c, device_id, esn}' || echo "Failed"
echo ""

# Test 4: Test PATCH endpoint
echo "4. Testing device update endpoint..."
UPDATE_RESPONSE=$(curl -s -X PATCH "$PROD_URL/v1/devices/$DEVICE_ID" \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie Test Probe"}')

echo "Update response:"
echo "$UPDATE_RESPONSE" | jq '.'
echo ""

# Test 5: Verify device list
echo "5. Verifying device list..."
curl -s "$PROD_URL/v1/devices" | jq ".[] | select(.id == $DEVICE_ID)" || echo "Failed"
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- If you see 6 new readings with depths 10, 20, 30, 40, 50, 60 cm"
echo "- And moisture values of 21%, 21%, 22%, 21%, 21%, 21%"
echo "- Then the Type-2 decoder is working correctly!"
echo ""
echo "Next step: Check dashboard at $PROD_URL/static/readings.html"
