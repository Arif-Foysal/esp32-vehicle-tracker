#!/usr/bin/env python3

"""
Test script for Vehicle Monitoring Backend
This script simulates an ESP32 device sending data to the backend
"""

import asyncio
import websockets
import json
import time
import random

BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
VEHICLE_ID = "TEST_V001"

async def simulate_vehicle():
    """Simulate vehicle data and commands"""
    uri = f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws/{VEHICLE_ID}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to backend as vehicle {VEHICLE_ID}")
            
            # Simulate sending status updates
            for i in range(10):
                # Generate random acceleration data (simulating normal driving)
                ax = random.uniform(-0.5, 0.5)
                ay = random.uniform(-0.5, 0.5)
                az = random.uniform(0.8, 1.2)  # Gravity component
                total = (ax**2 + ay**2 + az**2) ** 0.5
                
                status_message = {
                    "type": "status_update",
                    "vehicle_id": VEHICLE_ID,
                    "location": {
                        "lat": 23.798257 + random.uniform(-0.001, 0.001),
                        "lon": 90.449808 + random.uniform(-0.001, 0.001)
                    },
                    "acceleration": {
                        "x": ax,
                        "y": ay,
                        "z": az,
                        "total": total
                    },
                    "vehicle_locked": random.choice([True, False]),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                await websocket.send(json.dumps(status_message))
                print(f"Sent status update {i+1}/10")
                
                # Check for incoming commands
                try:
                    # Non-blocking receive with timeout
                    command = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    command_data = json.loads(command)
                    print(f"Received command: {command_data}")
                    
                    # Send response
                    response = {
                        "type": "command_response",
                        "command": command_data.get("command"),
                        "success": True,
                        "vehicle_id": VEHICLE_ID,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    await websocket.send(json.dumps(response))
                    print(f"Sent command response")
                    
                except asyncio.TimeoutError:
                    pass  # No command received
                
                await asyncio.sleep(2)
            
            # Simulate collision alert
            print("Simulating collision alert...")
            collision_alert = {
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
            
            await websocket.send(json.dumps(collision_alert))
            print("Collision alert sent!")
            
            # Wait a bit more to see any responses
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Vehicle Backend Test Script ===")
    print(f"Connecting to {BACKEND_HOST}:{BACKEND_PORT}")
    print("Make sure the backend server is running!")
    print()
    
    asyncio.run(simulate_vehicle())
