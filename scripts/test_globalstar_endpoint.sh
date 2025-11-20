#!/bin/bash
# Test script for Globalstar certification readiness
# Tests the /v1/uplink/receive endpoint with various scenarios

set -e

# Configuration
API_URL="https://api.soilreadings.com"
UPLINK_TOKEN="y7mlrffdn9XxPVR1SP8tt8iurW6XgZEfl4JpfcKv5eI="
TEST_MESSAGE_DIR="Test-Messages"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test() {
    echo -e "\n${YELLOW}▶ TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "  ℹ $1"
}

# Test functions
test_health_check() {
    print_test "Health Check Endpoint"

    response=$(curl -s "$API_URL/")

    if echo "$response" | grep -q '"status":"running"'; then
        print_pass "Health endpoint returned running status"
        print_info "Response: $response"
    else
        print_fail "Health endpoint did not return expected status"
        print_info "Response: $response"
    fi
}

test_no_token_no_allowlist() {
    print_test "Request WITHOUT token (should FAIL for non-Globalstar IPs)"

    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/uplink/receive" \
        -H "Content-Type: application/xml" \
        -d '<stuMessages><stuMessage><esn>TEST-001</esn></stuMessage></stuMessages>')

    if [ "$http_code" = "401" ]; then
        print_pass "Correctly rejected request without token (HTTP 401)"
    else
        print_fail "Expected HTTP 401, got HTTP $http_code"
    fi
}

test_with_token() {
    print_test "Request WITH valid token (should SUCCEED)"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$API_URL/v1/uplink/receive" \
        -H "Content-Type: application/xml" \
        -H "X-Uplink-Token: $UPLINK_TOKEN" \
        -d '<stuMessages><stuMessage><esn>TEST-TOKEN-001</esn><payload>0200000000000000</payload></stuMessage></stuMessages>')

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE:")

    if [ "$http_code" = "200" ]; then
        print_pass "Request with valid token succeeded (HTTP 200)"
        print_info "Response: $body"
    else
        print_fail "Expected HTTP 200, got HTTP $http_code"
        print_info "Response: $body"
    fi
}

test_real_payload() {
    print_test "Real SmartOne-C XML payload from test files"

    # Find a real test message file
    test_file=$(ls "$TEST_MESSAGE_DIR"/StuMessage*.xml 2>/dev/null | head -1)

    if [ -z "$test_file" ]; then
        test_file="$TEST_MESSAGE_DIR/StuMessage_Rev8.xml"
    fi

    if [ ! -f "$test_file" ]; then
        print_fail "Test message file not found: $test_file"
        return
    fi

    print_info "Using test file: $test_file"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$API_URL/v1/uplink/receive" \
        -H "Content-Type: application/xml" \
        -H "X-Uplink-Token: $UPLINK_TOKEN" \
        --data-binary "@$test_file")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE:")

    if [ "$http_code" = "200" ]; then
        print_pass "Real payload ingestion succeeded"
        print_info "Response: $body"
    else
        print_fail "Real payload ingestion failed with HTTP $http_code"
        print_info "Response: $body"
    fi
}

test_invalid_payload() {
    print_test "Invalid XML payload (should return HTTP 400)"

    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/uplink/receive" \
        -H "Content-Type: application/xml" \
        -H "X-Uplink-Token: $UPLINK_TOKEN" \
        -d '<invalid>xml<without>closing</tags>')

    if [ "$http_code" = "400" ]; then
        print_pass "Invalid payload correctly rejected (HTTP 400)"
    else
        print_fail "Expected HTTP 400, got HTTP $http_code"
    fi
}

test_data_retrieval() {
    print_test "Data Retrieval - Verify ingested data is accessible"

    response=$(curl -s "$API_URL/v1/readings/latest?limit=5")

    if echo "$response" | grep -q '"count"'; then
        print_pass "Latest readings endpoint accessible"

        # Check if we have any readings
        count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d: -f2)
        print_info "Found $count readings in database"
    else
        print_fail "Could not retrieve readings"
        print_info "Response: $response"
    fi
}

test_devices_endpoint() {
    print_test "Devices List - Verify devices are registered"

    response=$(curl -s "$API_URL/v1/devices")

    if echo "$response" | grep -q '"count"'; then
        count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d: -f2)
        print_pass "Devices endpoint accessible ($count devices registered)"
    else
        print_fail "Could not retrieve devices list"
        print_info "Response: $response"
    fi
}

# Main test execution
main() {
    print_header "Globalstar Certification Readiness Tests"
    echo "Testing endpoint: $API_URL/v1/uplink/receive"
    echo "Started: $(date)"

    # Run all tests
    test_health_check
    test_no_token_no_allowlist
    test_with_token
    test_invalid_payload
    test_real_payload
    test_data_retrieval
    test_devices_endpoint

    # Summary
    print_header "Test Summary"

    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  ✓ ALL TESTS PASSED - READY FOR GLOBALSTAR CERTIFICATION${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        exit 0
    else
        echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}  ✗ SOME TESTS FAILED - REVIEW ISSUES BEFORE CERTIFICATION${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        exit 1
    fi
}

# Check if running from correct directory
if [ ! -d "$TEST_MESSAGE_DIR" ]; then
    echo -e "${RED}Error: Must run from repository root directory${NC}"
    echo "Usage: ./scripts/test_globalstar_endpoint.sh"
    exit 1
fi

# Run tests
main
