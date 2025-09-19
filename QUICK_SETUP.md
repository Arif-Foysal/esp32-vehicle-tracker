# Quick Setup Instructions

## Backend Server Setup

1. **Install Dependencies**
   ```bash
   cd backend
   ./setup.sh
   ```

2. **Start Backend Server**
   ```bash
   source venv/bin/activate
   python main.py
   ```

3. **Access Dashboard**
   - Open browser: `http://localhost:8000`
   - Or from other devices: `http://YOUR_SERVER_IP:8000`

## ESP32 Configuration

1. **Update IP Address**
   - Find your server IP: `hostname -I` (Linux) or `ipconfig` (Windows)
   - Update `BACKEND_HOST` in `main.py`:
   ```python
   BACKEND_HOST = "192.168.1.XXX"  # Your actual IP
   ```

2. **Update WiFi Credentials**
   ```python
   WIFI_SSID = "your_wifi_name"
   WIFI_PASSWORD = "your_wifi_password"
   ```

3. **Set Vehicle ID**
   ```python
   VEHICLE_ID = "V123"  # Make it unique for each vehicle
   ```

4. **Upload and Run**
   ```bash
   mpremote connect /dev/cu.usbserial-10 fs cp main.py :/main.py
   mpremote connect /dev/cu.usbserial-10 run main.py
   ```

## Testing

1. **Test Backend Connection**
   ```bash
   cd backend
   python test_client.py
   ```

2. **Check ESP32 Output**
   - Look for "WebSocket connected!" message
   - Monitor live acceleration data

3. **Test Remote Commands**
   - Open web dashboard
   - Use Lock/Unlock/Emergency Stop buttons
   - Check ESP32 console for command responses

## Network Requirements

- ESP32 and server must be on the same WiFi network
- Port 8000 must be accessible
- For remote access, configure port forwarding or use cloud hosting
