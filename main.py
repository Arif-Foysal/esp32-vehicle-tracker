import machine
import time
from machine import I2C, Pin, PWM
import urequests
import network
import ujson

# ========================================
# CONFIGURATION
# ========================================
class Config:
    # MPU6050 Configuration
    MPU6050_ADDR = 0x68
    ACCEL_XOUT_H = 0x3B
    PWR_MGMT_1 = 0x6B
    
    # Pin Configuration
    SCL_PIN = 8
    SDA_PIN = 9
    BUZZER_PIN = 10
    
    # Collision Detection Settings
    COLLISION_THRESHOLD = 1.5
    SENSOR_READ_INTERVAL = 0.1
    
    # Buzzer Settings
    BUZZER_FREQUENCY = 2000
    BUZZER_DURATION = 1.0
    BUZZER_PATTERN_REPEATS = 8
    
    # Telegram Notification Settings
    BOT_TOKEN = "7549764083:AAFXVfvK34OAD83REoBGDLeLorrqTKuq7Gk"
    # CHAT_ID = "5217461051"
    CHAT_ID = "-4894924380"  # Group chat ID
    COLLISION_MESSAGE = "🚨 🚨 COLLISION DETECTED! 🚨 🚨\n\nVehicle accident detected at {timestamp}\nLocation: https://www.google.com/maps?q=23.798257479710784,90.44980802042723\nAcceleration: X={ax:.2f}g, Y={ay:.2f}g, Z={az:.2f}g"

    # WiFi Settings - CHANGE THESE TO YOUR ACTUAL WIFI CREDENTIALS
    WIFI_SSID = "car-app"  # Replace with your WiFi network name
    WIFI_PASSWORD = "asdfasdf"  # Replace with your WiFi password
    WIFI_TIMEOUT = 30  # Connection timeout in seconds
    
    # Vehicle Settings
    VEHICLE_ID = "V123"  # Unique vehicle identifier
    DEFAULT_LATITUDE = 23.798257479710784
    DEFAULT_LONGITUDE = 90.44980802042723
    
    # Backend Settings
    BACKEND_HOST = "esp32-vehicle-tracker.onrender.com"  # Just the hostname
    BACKEND_PORT = 443  # HTTPS port for secure connections
    BACKEND_URL = "https://esp32-vehicle-tracker.onrender.com"  # Full URL for HTTP requests
    # For testing with SSL issues, you can temporarily use HTTP:
    # BACKEND_URL = "http://esp32-vehicle-tracker.onrender.com"  # Uncomment this line for HTTP testing
    WEBSOCKET_RECONNECT_DELAY = 5  # seconds
    STATUS_UPDATE_INTERVAL = 2  # seconds

# ========================================
# SENSOR LAYER
# ========================================
class MPU6050Sensor:
    """MPU6050 Accelerometer sensor driver"""
    
    def __init__(self, scl_pin, sda_pin):
        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self._initialize()
    
    def _initialize(self):
        """Initialize the MPU6050 sensor"""
        # Wake up the MPU6050
        self.i2c.writeto_mem(Config.MPU6050_ADDR, Config.PWR_MGMT_1, b'\x00')
    
    def read_acceleration(self):
        """Read acceleration data from MPU6050"""
        data = self.i2c.readfrom_mem(Config.MPU6050_ADDR, Config.ACCEL_XOUT_H, 6)
        
        # Convert 16-bit signed integers from big-endian bytes
        ax = self._convert_raw_data(data[0], data[1])
        ay = self._convert_raw_data(data[2], data[3])
        az = self._convert_raw_data(data[4], data[5])
        
        # Convert to g (gravity units)
        return ax / 16384, ay / 16384, az / 16384
    
    def _convert_raw_data(self, high_byte, low_byte):
        """Convert raw bytes to signed integer"""
        value = (high_byte << 8) | low_byte
        return value - 65536 if value > 32767 else value

# ========================================
# ACTUATOR LAYER
# ========================================
class BuzzerController:
    """Buzzer controller for audio alerts"""
    
    def __init__(self, pin):
        self.pin = pin
    
    def sound_alert(self, frequency=None, duration=None, pattern_repeats=None):
        """Sound buzzer with emergency pattern"""
        freq = frequency or Config.BUZZER_FREQUENCY
        dur = duration or Config.BUZZER_DURATION
        repeats = pattern_repeats or Config.BUZZER_PATTERN_REPEATS
        
        buzzer = PWM(Pin(self.pin))
        
        for _ in range(repeats):
            # First beep
            buzzer.freq(freq)
            buzzer.duty(512)
            time.sleep(0.1)
            buzzer.duty(0)
            time.sleep(0.05)
            
            # Second beep (higher frequency)
            buzzer.freq(freq * 2)
            buzzer.duty(512)
            time.sleep(0.1)
            buzzer.duty(0)
            time.sleep(0.05)
        
        buzzer.deinit()

class WiFiManager:
    """WiFi connection manager"""
    
    def __init__(self, ssid=None, password=None):
        self.ssid = ssid or Config.WIFI_SSID
        self.password = password or Config.WIFI_PASSWORD
        self.wlan = network.WLAN(network.STA_IF)
    
    def connect(self):
        """Connect to WiFi network"""
        try:
            if self.wlan.isconnected():
                print(f"Already connected to WiFi. IP: {self.wlan.ifconfig()[0]}")
                return True
            
            print(f"Connecting to WiFi: {self.ssid}")
            self.wlan.active(True)
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection with timeout
            timeout = Config.WIFI_TIMEOUT
            while timeout > 0:
                if self.wlan.isconnected():
                    ip = self.wlan.ifconfig()[0]
                    print(f"WiFi connected successfully! IP: {ip}")
                    return True
                time.sleep(1)
                timeout -= 1
                print(f"Connecting... ({timeout}s remaining)")
            
            print("WiFi connection failed - timeout")
            return False
            
        except Exception as e:
            print(f"WiFi connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WiFi"""
        try:
            self.wlan.disconnect()
            self.wlan.active(False)
            print("WiFi disconnected")
        except Exception as e:
            print(f"WiFi disconnect error: {e}")
    
    def is_connected(self):
        """Check if WiFi is connected"""
        return self.wlan.isconnected()
    
    def get_ip(self):
        """Get current IP address"""
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None

class TelegramNotifier:
    """Telegram notification controller for emergency alerts"""
    
    def __init__(self, wifi_manager, bot_token=None, chat_id=None):
        self.wifi_manager = wifi_manager
        self.bot_token = bot_token or Config.BOT_TOKEN
        self.chat_id = chat_id or Config.CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_collision_alert(self, ax, ay, az):
        """Send collision alert message to Telegram"""
        # Check WiFi connectivity first
        if not self.wifi_manager.is_connected():
            print("WiFi not connected. Attempting to reconnect...")
            if not self.wifi_manager.connect():
                print("Failed to connect to WiFi. Cannot send Telegram notification.")
                return False
        
        try:
            # Format the message with current timestamp and acceleration data
            timestamp = self._get_timestamp()
            message = Config.COLLISION_MESSAGE.format(
                timestamp=timestamp,
                ax=ax,
                ay=ay,
                az=az
            )
            
            # URL encode the message to handle special characters
            message_encoded = self._url_encode(message)
            
            # Prepare the data payload - use form data instead of JSON
            data = f"chat_id={self.chat_id}&text={message_encoded}"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            # Send the message
            print("Sending Telegram notification...")
            response = urequests.post(self.api_url, data=data, headers=headers)
            
            if response.status_code == 200:
                print("Telegram notification sent successfully!")
                response.close()
                return True
            else:
                print(f"Failed to send Telegram notification. Status: {response.status_code}")
                try:
                    error_text = response.text
                    print(f"Error response: {error_text}")
                except:
                    print("Could not read error response")
                response.close()
                return False
            
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False
    
    def _url_encode(self, text):
        """Simple URL encoding for special characters"""
        # Replace common special characters that cause issues
        text = text.replace(" ", "%20")
        text = text.replace("\n", "%0A")
        text = text.replace("🚨", "%F0%9F%9A%A8")  # Emoji encoding
        text = text.replace("!", "%21")
        text = text.replace(":", "%3A")
        text = text.replace("=", "%3D")
        text = text.replace(",", "%2C")
        return text
    
    def _get_timestamp(self):
        """Get current timestamp (simplified for MicroPython)"""
        # Note: MicroPython doesn't have datetime, so we use a simple format
        return "Current time"  # You could enhance this with RTC if available

class BackendClient:
    """HTTP-based client for communicating with backend server (more reliable than WebSocket for MicroPython)"""
    
    def __init__(self, wifi_manager, vehicle_id=None):
        self.wifi_manager = wifi_manager
        self.vehicle_id = vehicle_id or Config.VEHICLE_ID
        self.base_url = Config.BACKEND_URL
        self.connected = False
        
    def connect(self):
        """Test connection to backend server"""
        if not self.wifi_manager.is_connected():
            print("WiFi not connected. Cannot establish backend connection.")
            return False
            
        # Try multiple endpoints to test connectivity
        test_endpoints = [
            f"{self.base_url}/health",           # Simple health check
            f"{self.base_url}/api/vehicles",     # Main API endpoint
        ]
        
        for url in test_endpoints:
            try:
                print(f"Testing connection to {url}")
                response = urequests.get(url, timeout=15)
                
                if response.status_code == 200:
                    self.connected = True
                    print("Backend connection successful!")
                    response.close()
                    return True
                else:
                    print(f"Backend responded with status: {response.status_code}")
                    response.close()
                    
            except OSError as e:
                error_code = e.args[0] if e.args else "Unknown"
                print(f"Connection error {error_code} for {url}")
                if error_code == -202:
                    print("SSL/TLS error detected. This is common with MicroPython HTTPS requests.")
                continue
            except Exception as e:
                print(f"Backend connection error: {e}")
                continue
        
        print("All connection attempts failed.")
        return False
    
    def disconnect(self):
        """Disconnect from backend server"""
        self.connected = False
        print("Backend disconnected")
    
    def _make_request(self, method, url, data=None, retries=2):
        """Make HTTP request with error handling and retries"""
        headers = {"Content-Type": "application/json"}
        
        for attempt in range(retries + 1):
            try:
                if method.upper() == "GET":
                    response = urequests.get(url, timeout=10)
                elif method.upper() == "POST":
                    response = urequests.post(url, data=data, headers=headers, timeout=10)
                else:
                    return None
                
                # Check if response is successful
                success = 200 <= response.status_code < 300
                
                if success:
                    try:
                        result = response.json() if response.text else {}
                        response.close()
                        return result
                    except:
                        response.close()
                        return {"success": True}
                else:
                    print(f"HTTP {response.status_code} error for {url}")
                    response.close()
                    
            except OSError as e:
                error_code = e.args[0] if e.args else "Unknown"
                if error_code == -202:
                    print(f"SSL error on attempt {attempt + 1}/{retries + 1}")
                else:
                    print(f"Network error {error_code} on attempt {attempt + 1}/{retries + 1}")
                    
                if attempt < retries:
                    time.sleep(1)  # Wait before retry
                    
            except Exception as e:
                print(f"Request error: {e}")
                if attempt < retries:
                    time.sleep(1)
        
        # All attempts failed
        self.connected = False
        return None
    
    def send_status_update(self, message):
        """Send status update to backend via HTTP POST"""
        if not self.connected:
            return False
            
        url = f"{self.base_url}/api/vehicles/{self.vehicle_id}/status"
        data = ujson.dumps(message)
        
        result = self._make_request("POST", url, data)
        return result is not None
    
    def send_collision_alert(self, message):
        """Send collision alert to backend"""
        if not self.connected:
            return False
            
        url = f"{self.base_url}/api/vehicles/{self.vehicle_id}/alert"
        data = ujson.dumps(message)
        
        result = self._make_request("POST", url, data)
        
        if result:
            print("Collision alert sent to backend!")
            return True
        return False
    
    def check_for_commands(self):
        """Check for pending commands from backend"""
        if not self.connected:
            return None
            
        url = f"{self.base_url}/api/vehicles/{self.vehicle_id}/commands"
        result = self._make_request("GET", url)
        
        return result if result else None
    
    def send_command_response(self, command_id, command, success):
        """Send command execution response to backend"""
        if not self.connected:
            return False
            
        url = f"{self.base_url}/api/vehicles/{self.vehicle_id}/command-response"
        
        response_data = {
            "command_id": command_id,
            "command": command,
            "success": success,
            "vehicle_id": self.vehicle_id,
            "timestamp": "Current time"
        }
        
        data = ujson.dumps(response_data)
        result = self._make_request("POST", url, data)
        
        return result is not None

class VehicleController:
    """Vehicle control system for lock/unlock functionality"""
    
    def __init__(self):
        self.is_locked = False
        # You can add actual hardware control pins here
        # self.lock_pin = Pin(LOCK_PIN, Pin.OUT)
        
    def lock_vehicle(self):
        """Lock the vehicle"""
        self.is_locked = True
        print("🔒 Vehicle LOCKED")
        # Add actual hardware control here
        # self.lock_pin.on()
        return True
        
    def unlock_vehicle(self):
        """Unlock the vehicle"""
        self.is_locked = False
        print("🔓 Vehicle UNLOCKED")
        # Add actual hardware control here
        # self.lock_pin.off()
        return True
        
    def emergency_stop(self):
        """Emergency stop procedure"""
        print("🚨 EMERGENCY STOP ACTIVATED!")
        # Add emergency stop logic here
        # Could disable engine, activate emergency lights, etc.
        return True
        
    def get_status(self):
        """Get current vehicle status"""
        return {
            "locked": self.is_locked,
            "emergency": False  # You can add more status fields
        }

# ========================================
# BUSINESS LOGIC LAYER
# ========================================
class CollisionDetector:
    """Core collision detection logic"""
    
    def __init__(self, threshold=None):
        self.threshold = threshold or Config.COLLISION_THRESHOLD
    
    def calculate_magnitude(self, ax, ay, az):
        """Calculate the magnitude of 3D acceleration vector"""
        return (ax**2 + ay**2 + az**2) ** 0.5
    
    def is_collision(self, total_acceleration):
        """Determine if collision occurred based on acceleration threshold"""
        # Normal gravity is ~1g, collision causes significant deviation
        return abs(total_acceleration - 1) > self.threshold

class DataLogger:
    """Handle data logging and display"""
    
    @staticmethod
    def log_sensor_data(ax, ay, az, total_accel):
        """Log live acceleration data"""
        print("Live Accel: X={:.2f}, Y={:.2f}, Z={:.2f}, Total={:.2f}".format(
            ax, ay, az, total_accel))
    
    @staticmethod
    def log_collision_event(ax, ay, az):
        """Log collision detection event"""
        lat, lon = Config.DEFAULT_LATITUDE, Config.DEFAULT_LONGITUDE
        timestamp = "Current time"  # Placeholder for timestamp
        print("""
    🚨 COLLISION DETECTED!  

    🚗 Vehicle: {}  
    📍 Location: https://www.google.com/maps?q={:.6f},{:.6f}  
    🕒 Time: {}
    """.format(Config.VEHICLE_ID, lat, lon, timestamp))
    
    @staticmethod
    def create_status_message(ax, ay, az, total_accel, vehicle_status):
        """Create status message for backend"""
        return {
            "type": "status_update",
            "vehicle_id": Config.VEHICLE_ID,
            "location": {
                "lat": Config.DEFAULT_LATITUDE,
                "lon": Config.DEFAULT_LONGITUDE
            },
            "acceleration": {
                "x": ax,
                "y": ay,
                "z": az,
                "total": total_accel
            },
            "vehicle_locked": vehicle_status["locked"],
            "timestamp": "Current time"
        }
    
    @staticmethod
    def create_collision_alert(ax, ay, az):
        """Create collision alert message for backend"""
        return {
            "type": "collision_alert",
            "vehicle_id": Config.VEHICLE_ID,
            "location": {
                "lat": Config.DEFAULT_LATITUDE,
                "lon": Config.DEFAULT_LONGITUDE
            },
            "acceleration": {
                "x": ax,
                "y": ay,
                "z": az,
                "total": (ax**2 + ay**2 + az**2) ** 0.5
            },
            "timestamp": "Current time",
            "severity": "high"
        }

# ========================================
# APPLICATION LAYER
# ========================================
class VehicleMonitoringSystem:
    """Main application orchestrating all components"""
    
    def __init__(self):
        print("=== Vehicle Collision Detection System ===")
        print("Initializing components...")
        
        # Initialize WiFi connection
        self.wifi_manager = WiFiManager()
        wifi_connected = self.wifi_manager.connect()
        if not wifi_connected:
            print("WARNING: WiFi not connected. Remote features will be unavailable.")
        
        # Initialize hardware components
        self.accelerometer = MPU6050Sensor(Config.SCL_PIN, Config.SDA_PIN)
        self.buzzer = BuzzerController(Config.BUZZER_PIN)
        self.telegram_notifier = TelegramNotifier(self.wifi_manager)
        
        # Initialize vehicle control
        self.vehicle_controller = VehicleController()
        
        # Initialize Backend client
        self.backend_client = BackendClient(self.wifi_manager)
        self.backend_connected = False
        
        # Initialize business logic components
        self.collision_detector = CollisionDetector()
        self.logger = DataLogger()
        
        # Timing variables
        self.last_status_update = 0
        self.last_backend_attempt = 0
        self.last_command_check = 0
        
        print("System initialized successfully!")
        print("Vehicle ID: {}".format(Config.VEHICLE_ID))
        print("Monitoring threshold: {:.1f}g".format(Config.COLLISION_THRESHOLD))
        if wifi_connected:
            print(f"WiFi Status: Connected (IP: {self.wifi_manager.get_ip()})")
            print(f"Backend Server: {Config.BACKEND_URL}")
        else:
            print("WiFi Status: Disconnected")
        print("=" * 40)
    
    def ensure_backend_connection(self):
        """Ensure backend connection is established"""
        current_time = time.time()
        
        # Check if we should attempt reconnection
        if not self.backend_connected and (current_time - self.last_backend_attempt) > Config.WEBSOCKET_RECONNECT_DELAY:
            self.last_backend_attempt = current_time
            
            if self.wifi_manager.is_connected():
                print("Attempting backend connection...")
                if self.backend_client.connect():
                    self.backend_connected = True
                    print("Backend connected!")
                else:
                    print("Backend connection failed. Will retry in {} seconds.".format(Config.WEBSOCKET_RECONNECT_DELAY))
            else:
                print("WiFi not connected. Cannot establish backend connection.")
    
    def handle_backend_commands(self):
        """Handle commands received from backend"""
        if not self.backend_connected:
            return
            
        current_time = time.time()
        # Check for commands every 5 seconds to avoid overloading the server
        if (current_time - self.last_command_check) < 5:
            return
            
        self.last_command_check = current_time
        
        # Check for incoming commands
        commands = self.backend_client.check_for_commands()
        if commands:
            for cmd in commands:
                print("Received command from backend: {}".format(cmd))
                
                command = cmd.get('command')
                command_id = cmd.get('id', 'unknown')
                
                if command == 'lock':
                    success = self.vehicle_controller.lock_vehicle()
                    self.send_command_response(command_id, command, success)
                    
                elif command == 'unlock':
                    success = self.vehicle_controller.unlock_vehicle()
                    self.send_command_response(command_id, command, success)
                    
                elif command == 'emergency_stop':
                    success = self.vehicle_controller.emergency_stop()
                    self.send_command_response(command_id, command, success)
                    
                elif command == 'status_request':
                    self.send_immediate_status_update()
                    
                else:
                    print("Unknown command: {}".format(command))
    
    def send_command_response(self, command_id, command, success):
        """Send command execution response to backend"""
        if self.backend_connected:
            if not self.backend_client.send_command_response(command_id, command, success):
                self.backend_connected = False
    
    def send_status_update(self, ax, ay, az, total_accel):
        """Send status update to backend via HTTP"""
        if not self.backend_connected:
            return
            
        vehicle_status = self.vehicle_controller.get_status()
        status_message = self.logger.create_status_message(ax, ay, az, total_accel, vehicle_status)
        
        if not self.backend_client.send_status_update(status_message):
            print("Failed to send status update. Backend connection lost.")
            self.backend_connected = False
    
    def send_immediate_status_update(self):
        """Send immediate status update (for status requests)"""
        # Read current sensor data
        ax, ay, az = self.accelerometer.read_acceleration()
        total_accel = self.collision_detector.calculate_magnitude(ax, ay, az)
        self.send_status_update(ax, ay, az, total_accel)
    
    def send_collision_alert(self, ax, ay, az):
        """Send collision alert to backend"""
        if not self.backend_connected:
            return
            
        alert_message = self.logger.create_collision_alert(ax, ay, az)
        
        if not self.backend_client.send_collision_alert(alert_message):
            print("Failed to send collision alert. Backend connection lost.")
            self.backend_connected = False
    
    def process_sensor_data(self):
        """Process one cycle of sensor data"""
        # Read sensor data
        ax, ay, az = self.accelerometer.read_acceleration()
        
        # Calculate total acceleration
        total_accel = self.collision_detector.calculate_magnitude(ax, ay, az)
        
        # Log sensor data
        self.logger.log_sensor_data(ax, ay, az, total_accel)
        
        # Send periodic status updates to backend
        current_time = time.time()
        if (current_time - self.last_status_update) >= Config.STATUS_UPDATE_INTERVAL:
            self.send_status_update(ax, ay, az, total_accel)
            self.last_status_update = current_time
        
        # Check for collision and respond
        if self.collision_detector.is_collision(total_accel):
            self._handle_collision_event(ax, ay, az)
    
    def _handle_collision_event(self, ax, ay, az):
        """Handle collision detection event"""
        self.logger.log_collision_event(ax, ay, az)
        self.buzzer.sound_alert()
        self.telegram_notifier.send_collision_alert(ax, ay, az)
        self.send_collision_alert(ax, ay, az)

    def run(self):
        """Main execution loop"""
        try:
            while True:
                # Ensure backend connection
                self.ensure_backend_connection()
                
                # Handle backend commands
                self.handle_backend_commands()
                
                # Process sensor data
                self.process_sensor_data()
                
                time.sleep(Config.SENSOR_READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\nSystem stopped by user")
        except Exception as e:
            print("System error: {}".format(e))
        finally:
            # Clean up connections
            if self.backend_connected:
                self.backend_client.disconnect()
            self.wifi_manager.disconnect()

# ========================================
# ENTRY POINT
# ========================================
if __name__ == "__main__":
    # Create and run the monitoring system
    system = VehicleMonitoringSystem()
    system.run()
