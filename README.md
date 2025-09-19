# ESP32-S3 Vehicle Collision Detection System

A comprehensive collision detection system using ESP32-S3 microcontroller with MPU6050 accelerometer, buzzer alerts, Telegram notifications, and **real-time WebSocket communication with FastAPI backend**.

## 🚗 System Overview

This system continuously monitors vehicle acceleration and detects potential collisions. When a collision is detected (acceleration > 1.5g), it:
- 🔊 Sounds an emergency buzzer pattern
- 📱 Sends detailed Telegram notification with location
- 📊 Logs collision data with acceleration values
- **🌐 Sends real-time alerts to backend server via WebSocket**
- **🎛️ Receives remote commands (lock/unlock, emergency stop)**

## ✨ New Features

### Real-time Backend Communication
- **WebSocket Connection**: Low-latency bidirectional communication
- **Live Monitoring**: Real-time vehicle status, location, and sensor data
- **Remote Control**: Lock/unlock vehicle and emergency stop commands
- **Web Dashboard**: Browser-based monitoring and control interface
- **Multi-vehicle Support**: Monitor multiple vehicles simultaneously

### Vehicle Control
- **Lock/Unlock**: Remote vehicle locking system
- **Emergency Stop**: Remote emergency procedures
- **Status Monitoring**: Real-time vehicle status updates
- **Location Tracking**: GPS coordinates (configurable)

## 🔧 Hardware Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Microcontroller | ESP32-S3 PLUS | Main processing unit with WiFi |
| Accelerometer | MPU6050 | 3-axis acceleration sensing |
| Buzzer | Active Buzzer | Audio collision alerts |
| Breadboard | Half-size | Component mounting |
| Jumper Wires | M-M, M-F | Connections |

## 📐 Wiring Diagram

### ESP32-S3 Pin Connections

```
ESP32-S3 PLUS          MPU6050
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO8 (SCL)      ←→    SCL
GPIO9 (SDA)      ←→    SDA
3.3V             ←→    VCC
GND              ←→    GND

ESP32-S3 PLUS          BUZZER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO10           ←→    Positive (+)
GND              ←→    Negative (-)
```

### Physical Wiring Layout

```
          ESP32-S3 PLUS
     ┌─────────────────────┐
     │ 3.3V  GND  GPIO8-9  │
     │  │     │     │   │  │
     └──┼─────┼─────┼───┼──┘
        │     │     │   │
        │     │   ┌─┴───┴─┐
        │     │   │ MPU6050│
        │     │   │ SCL SDA│
        │     │   │ VCC GND│
        │     │   └───┬───┬┘
        │     │       │   │
        └─────┼───────┘   │
              └───────────┘

     GPIO10    GND
        │       │
        │   ┌───┴───┐
        └───┤ BUZZER │
            │   +   - │
            └───────┘
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VEHICLE MONITORING SYSTEM                 │
├─────────────────────────────────────────────────────────────┤
│                     APPLICATION LAYER                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            VehicleMonitoringSystem                      │ │
│  │  • Orchestrates all components                          │ │
│  │  • Main execution loop                                  │ │
│  │  • Error handling & recovery                            │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    BUSINESS LOGIC LAYER                      │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │ CollisionDetector│  │           DataLogger                │ │
│  │ • Threshold calc │  │ • Console logging                   │ │
│  │ • Magnitude calc │  │ • Collision events                  │ │
│  │ • Decision logic │  │ • Live sensor data                  │ │
│  └─────────────────┘  └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      ACTUATOR LAYER                          │
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ BuzzerController│  │ WiFiManager │  │TelegramNotifier │   │
│  │ • PWM control   │  │ • Connect   │  │ • API calls     │   │
│  │ • Alert patterns│  │ • Monitor   │  │ • Error handle  │   │
│  │ • Emergency tone│  │ • Reconnect │  │ • URL encoding  │   │
│  └─────────────────┘  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                       SENSOR LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 MPU6050Sensor                           │ │
│  │  • I2C communication                                   │ │
│  │  • Raw data conversion                                 │ │
│  │  • 3-axis acceleration reading                         │ │
│  │  • Gravity unit conversion                             │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     HARDWARE LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   ESP32-S3  │  │   MPU6050   │  │       BUZZER        │   │
│  │ • WiFi      │  │ • Accel X   │  │ • PWM Audio         │   │
│  │ • I2C       │  │ • Accel Y   │  │ • Emergency Pattern │   │
│  │ • PWM       │  │ • Accel Z   │  │ • Collision Alert   │   │
│  │ • Processing│  │ • I2C Bus   │  │                     │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagram

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   MPU6050   │───▶│ Read Accel   │───▶│ Calculate       │
│ Accelerometer│    │ X, Y, Z      │    │ Magnitude       │
└─────────────┘    └──────────────┘    └─────────────────┘
                                                │
                   ┌─────────────────┐         ▼
                   │ Live Data       │◀────┌─────────────────┐
                   │ Console Log     │     │ Threshold       │
                   └─────────────────┘     │ Comparison      │
                                          └─────────────────┘
                                                │
                                          ┌─────▼─────┐
                                          │ Collision │
                                          │ Detected? │
                                          └─────┬─────┘
                                               │ YES
                          ┌────────────────────┼────────────────────┐
                          ▼                    ▼                    ▼
                   ┌─────────────┐    ┌─────────────────┐  ┌─────────────────┐
                   │   Buzzer    │    │ Console Alert   │  │ Telegram Alert  │
                   │ Emergency   │    │ with Location   │  │ with GPS Link   │
                   │   Pattern   │    │ & Acceleration  │  │ & Details       │
                   └─────────────┘    └─────────────────┘  └─────────────────┘
```

## ⚙️ Configuration

Edit the `Config` class in `main.py`:

```python
class Config:
    # WiFi Settings - CHANGE THESE
    WIFI_SSID = "YourWiFiName"
    WIFI_PASSWORD = "YourWiFiPassword"
    
    # Telegram Settings - CHANGE THESE
    BOT_TOKEN = "your_bot_token_here"
    CHAT_ID = "your_chat_id_here"
    
    # Collision Threshold (g-force)
    COLLISION_THRESHOLD = 1.5  # Adjust sensitivity
    
    # Pin Assignments
    SCL_PIN = 8   # I2C Clock
    SDA_PIN = 9   # I2C Data
    BUZZER_PIN = 10  # PWM Buzzer
```

## 🚀 Installation & Setup

### 1. Hardware Assembly
1. Connect MPU6050 to ESP32-S3 using I2C (pins 8 & 9)
2. Connect buzzer to GPIO10 and GND
3. Power ESP32-S3 via USB-C

### 2. Backend Server Setup (NEW!)
1. Navigate to backend directory: `cd backend`
2. Run setup script: `./setup.sh` (or manually install dependencies)
3. Update `BACKEND_HOST` in ESP32 `main.py` to your server's IP address
4. Start the backend server: `python main.py`
5. Access web dashboard at `http://localhost:8000`

### 3. Software Setup
1. Flash MicroPython firmware to ESP32-S3
2. Configure WiFi credentials in `main.py`
3. Set up Telegram bot and get bot token
4. **Configure backend server IP in `Config.BACKEND_HOST`**
5. Upload code to ESP32-S3

### 4. Telegram Bot Setup
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Get bot token from BotFather
4. Get your chat ID by messaging @userinfobot

### 5. Configuration
Update these settings in `main.py`:

```python
class Config:
    # WiFi Settings
    WIFI_SSID = "your_wifi_name"
    WIFI_PASSWORD = "your_wifi_password"
    
    # Backend Settings (NEW!)
    BACKEND_HOST = "192.168.1.100"  # Your server IP
    BACKEND_PORT = 8000
    VEHICLE_ID = "V123"  # Unique vehicle identifier
    
    # Telegram Settings
    BOT_TOKEN = "your_bot_token"
    CHAT_ID = "your_chat_id"
```

### 6. Upload and Run
```bash
# Upload main.py to ESP32-S3
mpremote connect /dev/cu.usbserial-10 fs cp main.py :/main.py

# Run the system
mpremote connect /dev/cu.usbserial-10 run main.py
```

### 7. Testing Backend Communication
Use the test client to verify backend functionality:
```bash
cd backend
python test_client.py
```

## 📊 System Operation

### Normal Operation with Backend
```
=== Vehicle Collision Detection System ===
Initializing components...
Connecting to WiFi: YourWiFiName
WiFi connected successfully! IP: 192.168.1.100
System initialized successfully!
Vehicle ID: V123
Monitoring threshold: 1.5g
WiFi Status: Connected (IP: 192.168.1.100)
Backend Server: 192.168.1.100:8000
========================================
Attempting WebSocket connection...
WebSocket connected!
Live Accel: X=0.43, Y=0.53, Z=-0.80, Total=1.05
Live Accel: X=0.44, Y=0.52, Z=-0.79, Total=1.04
...
```

### Remote Commands
```
Received command from backend: {'type': 'command', 'command': 'lock', 'timestamp': '2023-09-19T10:30:00'}
🔒 Vehicle LOCKED

Received command from backend: {'type': 'command', 'command': 'unlock', 'timestamp': '2023-09-19T10:31:00'}
🔓 Vehicle UNLOCKED

Received command from backend: {'type': 'command', 'command': 'emergency_stop', 'timestamp': '2023-09-19T10:32:00'}
🚨 EMERGENCY STOP ACTIVATED!
```

### Collision Detected with Backend Alert
```
Live Accel: X=2.50, Y=1.80, Z=0.95, Total=3.20

🚨 COLLISION DETECTED!

🚗 Vehicle: V123
📍 Location: https://www.google.com/maps?q=23.798258,90.449808
🕒 Time: Current time

Sending Telegram notification...
Telegram notification sent successfully!
```

### Web Dashboard Features
- **Real-time Monitoring**: View live vehicle location and acceleration data
- **Vehicle Status**: See lock/unlock status and last update time
- **Remote Control**: Send lock/unlock and emergency stop commands
- **Location Links**: Click coordinates to view location in Google Maps
- **Multi-vehicle Support**: Monitor multiple vehicles simultaneously

## 🔧 Troubleshooting

### Common Issues

**WiFi Connection Failed**
- Check SSID and password in Config
- Ensure WiFi is 2.4GHz (ESP32 limitation)
- Verify WiFi range and signal strength

**WebSocket Connection Failed (NEW!)**
- Check if backend server is running (`python backend/main.py`)
- Verify `BACKEND_HOST` IP address in ESP32 config
- Ensure both devices are on the same network
- Check firewall settings on server (port 8000)

**Remote Commands Not Working**
- Verify WebSocket connection is established
- Check command format in web dashboard
- Monitor ESP32 console for error messages
- Ensure valid command names (lock, unlock, emergency_stop)

**No Status Updates in Dashboard**
- Confirm WiFi connection on ESP32
- Check WebSocket connection status
- Verify `STATUS_UPDATE_INTERVAL` setting
- Refresh browser page

**MPU6050 Not Responding**
- Check I2C wiring (SCL=8, SDA=9)
- Verify 3.3V power connection
- Test with I2C scanner code

**Telegram Not Working**
- Verify bot token and chat ID
- Check internet connectivity
- Test bot with @BotFather first

**False Collision Detection**
- Adjust `COLLISION_THRESHOLD` in Config
- Check sensor mounting (should be stable)
- Calibrate for your vehicle's normal vibration

### Debug Mode
Add debug prints to troubleshoot:
```python
print(f"Raw acceleration: {ax}, {ay}, {az}")
print(f"WiFi status: {self.wifi_manager.is_connected()}")
```

## 📱 Telegram Notification Format

When collision detected, you'll receive:
```
🚨 🚨 COLLISION DETECTED! 🚨 🚨

Vehicle accident detected at Current time
Location: https://www.google.com/maps?q=23.798257,90.449808
Acceleration: X=2.50g, Y=1.80g, Z=-0.95g
```

## 🔋 Power Consumption

| Component | Current Draw | Notes |
|-----------|--------------|-------|
| ESP32-S3 | ~80mA | Active WiFi |
| MPU6050 | ~3.9mA | Normal operation |
| Buzzer | ~30mA | When active |
| **Total** | **~114mA** | During collision alert |

## 📈 Performance Metrics

- **Sensor Reading Rate**: 10Hz (100ms interval)
- **Collision Detection Latency**: <200ms
- **Telegram Notification Time**: 2-5 seconds
- **Buzzer Response Time**: <100ms
- **WiFi Reconnection Time**: 5-10 seconds

## 🛡️ Safety Features

- **Graceful Degradation**: Works without WiFi
- **Error Recovery**: Automatic WiFi reconnection
- **Fail-Safe Operation**: Buzzer works independently
- **Threshold Protection**: Prevents false positives
- **Status Monitoring**: Real-time system health

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit your changes
4. Push to the branch
5. Create Pull Request

## 📞 Support

For issues and questions:
- Check troubleshooting section
- Review wiring connections
- Verify configuration settings
- Test individual components

---
**Made with ❤️ for vehicle safety**
