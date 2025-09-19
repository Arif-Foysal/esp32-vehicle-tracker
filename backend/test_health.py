#!/usr/bin/env python3

"""
Simple connectivity test for ESP32
"""

import requests

def test_health_endpoint():
    """Test the simple health endpoint"""
    url = "https://esp32-vehicle-tracker.onrender.com/health"
    
    try:
        print(f"Testing health endpoint: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Simple Health Check Test ===")
    success = test_health_endpoint()
    print(f"Result: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\n✅ The health endpoint is working!")
        print("This means the ESP32 should be able to connect to the backend.")
        print("\nIf the ESP32 still shows SSL errors (-202), try these solutions:")
        print("1. Update the ESP32 firmware to the latest version")
        print("2. Use HTTP instead of HTTPS for testing:")
        print("   Change BACKEND_URL to 'http://...' in the ESP32 config")
        print("3. Consider using a local backend server for development")
    else:
        print("\n❌ Health endpoint failed. Check if the backend is running.")
