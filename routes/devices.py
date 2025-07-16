from flask import Blueprint, jsonify
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Create Blueprint
devices_bp = Blueprint('devices', __name__)

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"
LATEST_JSON = []

def load_latest_metrics():
    global LATEST_JSON
    # Use fixed date for April 25, 2025
    date_str = "20250425"
    filename = f"wan_metrics_{date_str}.json"
    filepath = os.path.join(INVENTORY_DIR, filename)
    print(f"Loading metrics from {filepath}")
    try:
        with open(filepath, 'r') as f:
            LATEST_JSON = [json.loads(line.strip()) for line in f if line.strip()]
        print(f"Loaded {len(LATEST_JSON)} records")
    except FileNotFoundError:
        print(f"Metrics file {filepath} not found")
        LATEST_JSON = []
    except Exception as e:
        print(f"Error loading WAN metrics file {filepath}: {e}")
        LATEST_JSON = []

@devices_bp.route('/api/devices')
def get_devices():
    print(f"Accessing /api/devices")
    try:
        load_latest_metrics()
        return jsonify(LATEST_JSON)
    except Exception as e:
        print(f"Error in get_devices route: {str(e)}")
        return jsonify({"error": f"Failed to load devices: {str(e)}"}), 500
