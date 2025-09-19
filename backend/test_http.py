#!/usr/bin/env python3

"""
Test script for HTTP endpoints
This script tests the HTTP-based communication with the backend
"""

import requests
import json
import time

BACKEND_URL = "https://esp32-vehicle-tracker.onrender.com"
VEHICLE_ID = "TEST_V001"

def test_vehicle_status_update():
    """Test sending vehicle status update"""
    url = f"{BACKEND_URL}/api/vehicles/{VEHICLE_ID}/status"
    
    status_data = {
        "type": "status_update",
        "vehicle_id": VEHICLE_ID,
        "location": {
            "lat": 23.798257,
            "lon": 90.449808
        },
        "acceleration": {
            "x": 0.12,
            "y": -0.05,
            "z": 0.98,
            "total": 1.02
        },
        "vehicle_locked": False,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        response = requests.post(url, json=status_data, timeout=10)
        print(f"Status Update Response: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Status update failed: {e}")
        return False

def test_collision_alert():
    """Test sending collision alert"""
    url = f"{BACKEND_URL}/api/vehicles/{VEHICLE_ID}/alert"
    
    alert_data = {
        "type": "collision_alert",
        "vehicle_id": VEHICLE_ID,
        "location": {
            "lat": 23.798257,
            "lon": 90.449808
        },
        "acceleration": {
            "x": 3.2,
            "y": -2.1,
            "z": 4.5,
            "total": 5.8
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "severity": "high"
    }
    
    try:
        response = requests.post(url, json=alert_data, timeout=10)
        print(f"Collision Alert Response: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Collision alert failed: {e}")
        return False

def test_get_vehicles():
    """Test getting vehicles list"""
    url = f"{BACKEND_URL}/api/vehicles"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Get Vehicles Response: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Get vehicles failed: {e}")
        return False

def test_vehicle_commands():
    """Test getting vehicle commands"""
    url = f"{BACKEND_URL}/api/vehicles/{VEHICLE_ID}/commands"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Get Commands Response: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Get commands failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Backend HTTP Endpoints Test ===")
    print(f"Testing backend at: {BACKEND_URL}")
    print(f"Vehicle ID: {VEHICLE_ID}")
    print()
    
    # Test all endpoints
    tests = [
        ("Get Vehicles", test_get_vehicles),
        ("Vehicle Status Update", test_vehicle_status_update),
        ("Collision Alert", test_collision_alert),
        ("Get Commands", test_vehicle_commands),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print(f"Result: {'PASS' if success else 'FAIL'}")
        print("-" * 40)
        time.sleep(1)  # Brief delay between tests
    
    # Summary
    print("\n=== Test Results Summary ===")
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! The backend is ready for ESP32 communication.")
    else:
        print("⚠️  Some tests failed. Check the backend server and try again.")
