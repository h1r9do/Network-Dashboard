from flask import Blueprint, render_template, jsonify
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"
ORG_NAME = os.getenv('ORG_NAME', 'Unknown Org')
LATEST_JSON = []
LAST_UPDATE = None

def load_latest_metrics():
    global LATEST_JSON, LAST_UPDATE
    # Use fixed date for April 25, 2025
    date_str = "20250425"
    filename = f"wan_metrics_{date_str}.json"
    filepath = os.path.join(INVENTORY_DIR, filename)
    print(f"Loading metrics from {filepath}")
    try:
        with open(filepath, 'r') as f:
            LATEST_JSON = [json.loads(line.strip()) for line in f if line.strip()]
        LAST_UPDATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Loaded {len(LATEST_JSON)} records")
    except FileNotFoundError:
        print(f"Metrics file {filepath} not found")
        LATEST_JSON = []
    except Exception as e:
        print(f"Error loading WAN metrics file {filepath}: {e}")
        LATEST_JSON = []

@main_bp.route('/')
def index():
    print(f"Attempting to render index.html")
    try:
        load_latest_metrics()
        return render_template('index.html',
                              org_name=ORG_NAME,
                              last_update=LAST_UPDATE,
                              total_sites=len(LATEST_JSON))
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        return jsonify({"error": f"Failed to render index: {str(e)}"}), 500
