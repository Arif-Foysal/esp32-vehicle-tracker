from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
from datetime import datetime
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vehicle Monitoring Backend", version="1.0.0")

# Store active vehicle connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.vehicle_status: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, vehicle_id: str):
        await websocket.accept()
        self.active_connections[vehicle_id] = websocket
        logger.info(f"Vehicle {vehicle_id} connected")
    
    def disconnect(self, vehicle_id: str):
        if vehicle_id in self.active_connections:
            del self.active_connections[vehicle_id]
        if vehicle_id in self.vehicle_status:
            del self.vehicle_status[vehicle_id]
        logger.info(f"Vehicle {vehicle_id} disconnected")
    
    async def send_command(self, vehicle_id: str, command: dict):
        if vehicle_id in self.active_connections:
            websocket = self.active_connections[vehicle_id]
            try:
                await websocket.send_text(json.dumps(command))
                logger.info(f"Sent command to {vehicle_id}: {command}")
                return True
            except Exception as e:
                logger.error(f"Error sending command to {vehicle_id}: {e}")
                return False
        return False
    
    async def broadcast_to_all(self, message: dict):
        for vehicle_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {vehicle_id}: {e}")
    
    def update_vehicle_status(self, vehicle_id: str, status: dict):
        status['last_updated'] = datetime.now().isoformat()
        self.vehicle_status[vehicle_id] = status
        logger.info(f"Updated status for {vehicle_id}")

manager = ConnectionManager()

@app.get("/")
async def get_dashboard():
    """Simple dashboard to monitor vehicles and send commands"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vehicle Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .vehicle-card { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .status-online { border-left: 5px solid #4CAF50; }
            .status-offline { border-left: 5px solid #f44336; }
            .location-link { color: #1976D2; text-decoration: none; }
            .command-buttons button { margin: 5px; padding: 8px 15px; border: none; border-radius: 3px; cursor: pointer; }
            .lock-btn { background-color: #f44336; color: white; }
            .unlock-btn { background-color: #4CAF50; color: white; }
            .emergency-btn { background-color: #FF9800; color: white; }
            #status { margin-top: 20px; padding: 10px; background-color: #f5f5f5; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🚗 Vehicle Monitoring Dashboard</h1>
        <div id="vehicles"></div>
        <div id="status"></div>
        
        <script>
            let vehicles = {};
            
            function updateDashboard() {
                fetch('/api/vehicles/status')
                    .then(response => response.json())
                    .then(data => {
                        vehicles = data;
                        renderVehicles();
                    })
                    .catch(error => console.error('Error:', error));
            }
            
            function renderVehicles() {
                const container = document.getElementById('vehicles');
                container.innerHTML = '';
                
                if (Object.keys(vehicles).length === 0) {
                    container.innerHTML = '<p>No vehicles connected</p>';
                    return;
                }
                
                for (const [vehicleId, status] of Object.entries(vehicles)) {
                    const vehicleDiv = document.createElement('div');
                    vehicleDiv.className = 'vehicle-card status-online';
                    vehicleDiv.innerHTML = `
                        <h3>Vehicle: ${vehicleId}</h3>
                        <p><strong>Location:</strong> 
                            <a href="https://www.google.com/maps?q=${status.location?.lat || 0},${status.location?.lon || 0}" 
                               target="_blank" class="location-link">
                               ${status.location?.lat || 'N/A'}, ${status.location?.lon || 'N/A'}
                            </a>
                        </p>
                        <p><strong>Acceleration:</strong> X: ${status.acceleration?.x?.toFixed(2) || 'N/A'}g, 
                           Y: ${status.acceleration?.y?.toFixed(2) || 'N/A'}g, 
                           Z: ${status.acceleration?.z?.toFixed(2) || 'N/A'}g</p>
                        <p><strong>Total Acceleration:</strong> ${status.acceleration?.total?.toFixed(2) || 'N/A'}g</p>
                        <p><strong>Vehicle Status:</strong> ${status.vehicle_locked ? '🔒 Locked' : '🔓 Unlocked'}</p>
                        <p><strong>Last Updated:</strong> ${new Date(status.last_updated).toLocaleString()}</p>
                        
                        <div class="command-buttons">
                            <button class="lock-btn" onclick="sendCommand('${vehicleId}', 'lock')">🔒 Lock Vehicle</button>
                            <button class="unlock-btn" onclick="sendCommand('${vehicleId}', 'unlock')">🔓 Unlock Vehicle</button>
                            <button class="emergency-btn" onclick="sendCommand('${vehicleId}', 'emergency_stop')">🚨 Emergency Stop</button>
                        </div>
                    `;
                    container.appendChild(vehicleDiv);
                }
            }
            
            function sendCommand(vehicleId, command) {
                fetch('/api/vehicles/' + vehicleId + '/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({command: command})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = 
                        `<strong>Command Status:</strong> ${data.success ? 'Success' : 'Failed'} - ${data.message}`;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = 
                        `<strong>Error:</strong> ${error.message}`;
                });
            }
            
            // Update dashboard every 2 seconds
            setInterval(updateDashboard, 2000);
            updateDashboard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws/{vehicle_id}")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: str):
    await manager.connect(websocket, vehicle_id)
    try:
        while True:
            # Receive data from vehicle
            data = await websocket.receive_text()
            try:
                vehicle_data = json.loads(data)
                logger.info(f"Received from {vehicle_id}: {vehicle_data}")
                
                # Update vehicle status
                manager.update_vehicle_status(vehicle_id, vehicle_data)
                
                # Handle different message types
                if vehicle_data.get('type') == 'collision_alert':
                    logger.warning(f"COLLISION ALERT from {vehicle_id}!")
                    # You could trigger additional alerts here
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {vehicle_id}: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(vehicle_id)

@app.get("/api/vehicles/status")
async def get_all_vehicles_status():
    """Get status of all connected vehicles"""
    return manager.vehicle_status

@app.get("/api/vehicles/{vehicle_id}/status")
async def get_vehicle_status(vehicle_id: str):
    """Get status of a specific vehicle"""
    if vehicle_id in manager.vehicle_status:
        return manager.vehicle_status[vehicle_id]
    return {"error": "Vehicle not found"}

@app.post("/api/vehicles/{vehicle_id}/command")
async def send_vehicle_command(vehicle_id: str, command_data: dict):
    """Send command to a specific vehicle"""
    command = command_data.get('command')
    
    if not command:
        return {"success": False, "message": "No command specified"}
    
    # Validate command
    valid_commands = ['lock', 'unlock', 'emergency_stop', 'status_request']
    if command not in valid_commands:
        return {"success": False, "message": f"Invalid command. Valid commands: {valid_commands}"}
    
    # Send command to vehicle
    command_message = {
        "type": "command",
        "command": command,
        "timestamp": datetime.now().isoformat()
    }
    
    success = await manager.send_command(vehicle_id, command_message)
    
    if success:
        return {"success": True, "message": f"Command '{command}' sent to vehicle {vehicle_id}"}
    else:
        return {"success": False, "message": f"Failed to send command to vehicle {vehicle_id}. Vehicle may be offline."}

@app.get("/api/vehicles")
async def list_vehicles():
    """List all connected vehicles"""
    return {
        "connected_vehicles": list(manager.active_connections.keys()),
        "total_count": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
