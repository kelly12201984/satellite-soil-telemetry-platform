#!/usr/bin/env python3
"""
Quick verification script to check status computation.
Run after migration and deployment.
"""
import requests
import json
from collections import Counter

API_BASE = "https://api.soilreadings.com"

def main():
    print("🔍 Verifying Irrigation Alerts Status...\n")
    
    # 1. Health check
    try:
        r = requests.get(f"{API_BASE}/")
        print(f"✅ Health: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # 2. Devices attention endpoint
    try:
        r = requests.get(f"{API_BASE}/v1/devices/attention?limit=100")
        devices = r.json()
        print(f"\n✅ Devices attention: {len(devices)} devices")
        
        # Count by status
        status_counts = Counter(d["status"] for d in devices)
        print("\n📊 Status distribution:")
        for status, count in sorted(status_counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"   {status:10} → {count:3} devices")
        
        # Show top 5 worst
        if devices:
            print("\n🔴 Top 5 devices needing attention:")
            for i, d in enumerate(devices[:5], 1):
                print(f"   {i}. {d['alias']:20} | {d['status']:8} | {d.get('moisture30', 'N/A'):>6}% | {d['last_seen']}")
        
    except Exception as e:
        print(f"❌ Devices attention failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Devices list
    try:
        r = requests.get(f"{API_BASE}/v1/devices")
        devices = r.json()
        print(f"\n✅ Devices list: {len(devices)} total devices")
    except Exception as e:
        print(f"❌ Devices list failed: {e}")
    
    # 4. Metrics summary
    try:
        r = requests.get(f"{API_BASE}/v1/metrics/summary?from=2025-10-01T00:00:00Z&to=2025-11-03T23:59:59Z")
        summary = r.json()
        print(f"\n✅ Metrics summary:")
        print(f"   Avg Moisture: {summary.get('avg_moisture', 'N/A')}%")
        print(f"   Avg Temp: {summary.get('avg_temp', 'N/A')}°C")
        print(f"   Devices needing attention: {len(summary.get('devices_needing_attention', []))}")
    except Exception as e:
        print(f"❌ Metrics summary failed: {e}")
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()

