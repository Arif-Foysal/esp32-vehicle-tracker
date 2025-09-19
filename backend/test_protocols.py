#!/usr/bin/env python3

"""
Test HTTP vs HTTPS connections to Render deployment
This helps identify which protocol works for ESP32
"""

import requests
import time

BACKEND_HOST = "esp32-vehicle-tracker.onrender.com"
VEHICLE_ID = "TEST_V001"

def test_http_connection():
    """Test HTTP connection"""
    print("=== Testing HTTP Connection ===")
    base_url = f"http://{BACKEND_HOST}"
    
    endpoints = [
        "/health",
        "/",
        "/api/vehicles"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"✅ HTTP Success: {response.status_code}")
            response.close()
            return True
        except Exception as e:
            print(f"❌ HTTP Failed: {e}")
    
    return False

def test_https_connection():
    """Test HTTPS connection"""
    print("\n=== Testing HTTPS Connection ===")
    base_url = f"https://{BACKEND_HOST}"
    
    endpoints = [
        "/health",
        "/",
        "/api/vehicles"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"✅ HTTPS Success: {response.status_code}")
            response.close()
            return True
        except Exception as e:
            print(f"❌ HTTPS Failed: {e}")
    
    return False

def test_post_request(use_https=True):
    """Test POST request"""
    protocol = "https" if use_https else "http"
    print(f"\n=== Testing {protocol.upper()} POST Request ===")
    
    base_url = f"{protocol}://{BACKEND_HOST}"
    url = f"{base_url}/api/vehicles/{VEHICLE_ID}/status"
    
    test_data = {
        "type": "status_update",
        "vehicle_id": VEHICLE_ID,
        "location": {"lat": 23.798257, "lon": 90.449808},
        "acceleration": {"x": 0.1, "y": -0.05, "z": 0.98, "total": 1.0},
        "vehicle_locked": False,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        print(f"Testing POST: {url}")
        response = requests.post(url, json=test_data, timeout=10)
        print(f"✅ {protocol.upper()} POST Success: {response.status_code}")
        print(f"Response: {response.json()}")
        response.close()
        return True
    except Exception as e:
        print(f"❌ {protocol.upper()} POST Failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing connections to: {BACKEND_HOST}")
    print("This will help determine the best protocol for ESP32")
    print("-" * 50)
    
    # Test both protocols
    http_works = test_http_connection()
    https_works = test_https_connection()
    
    if http_works:
        http_post_works = test_post_request(use_https=False)
    
    if https_works:
        https_post_works = test_post_request(use_https=True)
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY FOR ESP32 CONFIGURATION:")
    print("=" * 50)
    
    if http_works:
        print("✅ HTTP connections work - ESP32 should use HTTP")
        print("   Configure ESP32 with: Config.BACKEND_URL_FALLBACK")
    else:
        print("❌ HTTP connections failed")
    
    if https_works:
        print("✅ HTTPS connections work - but may fail on ESP32 due to SSL issues")
        print("   ESP32 SSL support is limited")
    else:
        print("❌ HTTPS connections failed")
    
    print("\nRECOMMENDATION:")
    if http_works:
        print("🎯 Use HTTP for ESP32 communication")
        print("   Set: BACKEND_URL = 'http://esp32-vehicle-tracker.onrender.com'")
    elif https_works:
        print("⚠️  Only HTTPS available - ESP32 may have SSL issues")
        print("   Consider using a different deployment or SSL proxy")
    else:
        print("❌ No working connection found - check Render deployment")
