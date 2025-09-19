# Vehicle Monitoring Backend

This backend server provides WebSocket communication for the ESP32 vehicle tracker, allowing real-time monitoring and remote control of vehicles.

## Features

- **Real-time Monitoring**: Receive live vehicle status, location, and acceleration data
- **Remote Control**: Send lock/unlock and emergency stop commands to vehicles
- **Web Dashboard**: Browser-based interface for monitoring and controlling vehicles
- **WebSocket Communication**: Low-latency bidirectional communication
- **Multi-vehicle Support**: Handle multiple vehicles simultaneously

## Setup

### 1. Install Dependencies

```bash
cd backend
./setup.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure ESP32

Update the following settings in your ESP32 `main.py`:

```python
# In Config class
BACKEND_HOST = "192.168.1.100"  # Change to your server's IP address
BACKEND_PORT = 8000
VEHICLE_ID = "V123"  # Unique identifier for your vehicle
```

### 3. Start the Backend Server

```bash
source venv/bin/activate
python main.py
```

The server will start on `http://localhost:8000`

## Usage

### Web Dashboard

1. Open your browser to `http://localhost:8000`
2. View connected vehicles and their status
3. Send commands using the control buttons:
   - 🔒 **Lock Vehicle**: Locks the vehicle remotely
   - 🔓 **Unlock Vehicle**: Unlocks the vehicle remotely
   - 🚨 **Emergency Stop**: Triggers emergency stop procedure

### API Endpoints

- `GET /`: Web dashboard
- `GET /api/vehicles/status`: Get status of all vehicles
- `GET /api/vehicles/{vehicle_id}/status`: Get status of specific vehicle
- `POST /api/vehicles/{vehicle_id}/command`: Send command to vehicle
- `WebSocket /ws/{vehicle_id}`: WebSocket connection for real-time communication

### WebSocket Messages

#### From ESP32 to Backend

**Status Update:**
```json
{
    "type": "status_update",
    "vehicle_id": "V123",
    "location": {
        "lat": 23.798257479710784,
        "lon": 90.44980802042723
    },
    "acceleration": {
        "x": 0.12,
        "y": -0.05,
        "z": 0.98,
        "total": 1.02
    },
    "vehicle_locked": false,
    "timestamp": "Current time"
}
```

**Collision Alert:**
```json
{
    "type": "collision_alert",
    "vehicle_id": "V123",
    "location": {
        "lat": 23.798257479710784,
        "lon": 90.44980802042723
    },
    "acceleration": {
        "x": 2.5,
        "y": -1.8,
        "z": 3.2,
        "total": 4.5
    },
    "timestamp": "Current time",
    "severity": "high"
}
```

#### From Backend to ESP32

**Commands:**
```json
{
    "type": "command",
    "command": "lock",  // "lock", "unlock", "emergency_stop", "status_request"
    "timestamp": "2023-09-19T10:30:00"
}
```

**Command Response (ESP32 to Backend):**
```json
{
    "type": "command_response",
    "command": "lock",
    "success": true,
    "vehicle_id": "V123",
    "timestamp": "Current time"
}
```

## Configuration

### ESP32 Configuration

Key settings to update in your ESP32 code:

```python
class Config:
    # Backend WebSocket Settings
    BACKEND_HOST = "192.168.1.100"  # Your server IP
    BACKEND_PORT = 8000
    WEBSOCKET_RECONNECT_DELAY = 5  # seconds
    STATUS_UPDATE_INTERVAL = 2  # seconds
    
    # Vehicle Settings
    VEHICLE_ID = "V123"  # Unique identifier
    DEFAULT_LATITUDE = 23.798257479710784
    DEFAULT_LONGITUDE = 90.44980802042723
```

### Network Requirements

- ESP32 and backend server must be on the same network
- Ensure firewall allows connections on port 8000
- For remote access, configure port forwarding or use a cloud server

## Development

### Adding New Commands

1. Add command validation in `send_vehicle_command()` function
2. Handle command in ESP32's `handle_backend_commands()` method
3. Update the web dashboard buttons if needed

### Extending Vehicle Status

1. Add new fields to status messages in ESP32 `DataLogger.create_status_message()`
2. Update backend vehicle status display
3. Modify web dashboard to show new information

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if backend server is running
   - Verify IP address and port in ESP32 configuration
   - Ensure both devices are on the same network

2. **Commands Not Working**
   - Check WebSocket connection status
   - Verify command format and valid command names
   - Check ESP32 console for error messages

3. **No Status Updates**
   - Confirm WiFi connection on ESP32
   - Check WebSocket connection status
   - Verify STATUS_UPDATE_INTERVAL setting

### Debugging

Enable verbose logging by checking the console output from both the backend server and ESP32 device.

## Security Considerations

- This implementation is for development/testing purposes
- For production use, add authentication and encryption
- Consider using HTTPS/WSS for secure communication
- Implement proper access controls for vehicle commands
