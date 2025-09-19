#!/bin/bash

# Setup script for Vehicle Monitoring Backend

echo "=== Setting up Vehicle Monitoring Backend ==="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "=== Setup Complete ==="
echo ""
echo "To start the backend server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the server: python main.py"
echo "3. Open your browser to: http://localhost:8000"
echo ""
echo "Make sure to update the BACKEND_HOST in the ESP32 code to your server's IP address!"
