#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
import json
import os
from dotenv import load_dotenv
import csv
from io import StringIO
import requests
import itertools
from datetime import datetime

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Initialize Flask app
app = Flask(
    __name__,
    template_folder='/usr/local/bin/templates',
    static_folder='/usr/local/bin/static'
)

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"
CHANGELOG_DIR = os.path.join(INVENTORY_DIR, "changelogs")
os.makedirs(CHANGELOG_DIR, exist_ok=True)
BASE_URL = "https://api.meraki.com/api/v1"
LATEST_JSON = None
LAST_UPDATE = None

# Load API keys for Meraki API
api_keys = []
for key, value in os.environ.items():
    if key.startswith("MERAKI_API_KEY") and value:
        api_keys.append(value)
api_cycle = itertools.cycle(api_keys)

def get_headers(api_key):
    return {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }

def make_edit_api_request(url, method='GET', payload=None):
    for attempt in range(len(api_keys)):
        key = next(api_cycle)
        headers = get_headers(key)
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers)
            elif method == 'PUT':
                resp = requests.put(url, headers=headers, json=payload)
            if resp.status_code == 429:
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error on key {api_keys.index(key)+1}: {e}")
    return None

def load_latest_inventory(file_prefix="mx_inventory_live_"):
    global LATEST_JSON, LAST_UPDATE
    files = sorted(
        [f for f in os.listdir(INVENTORY_DIR) if f.startswith(file_prefix)],
        key=lambda x: os.path.getmtime(os.path.join(INVENTORY_DIR, x)),
        reverse=True
    )
    if not files:
        print(f"No files found with prefix {file_prefix}")
        LATEST_JSON = {} if file_prefix == "mx_inventory_live_" else []
        LAST_UPDATE = None
        return LATEST_JSON

    filepath = os.path.join(INVENTORY_DIR, files[0])
    try:
        with open(filepath, 'r') as f:
            if file_prefix == "mx_inventory_live_":
                LATEST_JSON = json.load(f)
            else:
                LATEST_JSON = [json.loads(line.strip()) for line in f if line.strip()]
        LAST_UPDATE = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        LATEST_JSON = {} if file_prefix == "mx_inventory_live_" else []
        LAST_UPDATE = None
    return LATEST_JSON

def log_change(serial, changes, user="web"):
    changelog_file = os.path.join(CHANGELOG_DIR, f"changes_{datetime.now().strftime('%Y%m%d')}.json")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "serial": serial,
        "changes": changes,
        "user": user
    }
    try:
        with open(changelog_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        print(f"Error writing to changelog: {e}")
        return False

def update_device_info(serial, notes=None, tags=None, user_ip=None):
    inventory = load_latest_inventory(file_prefix="mx_inventory_live_")
    if not inventory:
        return {"error": "Inventory not found"}
    device = next((d for d in inventory.get('devices', []) if d['device_serial'] == serial), None)
    if not device:
        return {"error": "Device not found"}
    changes = {}
    if notes is not None and notes != device.get('raw_notes', ''):
        changes['notes'] = notes
    if tags is not None and set(tags) != set(device.get('network_tags', [])):
        changes['tags'] = tags
    if not changes:
        return {"message": "No changes detected"}
    update_success = True
    if 'notes' in changes:
        url = f"{BASE_URL}/networks/{device['network_id']}/devices/{serial}"
        payload = {'notes': changes['notes']}
        result = make_edit_api_request(url, method='PUT', payload=payload)
        if not result:
            update_success = False
    if 'tags' in changes and update_success:
        url = f"{BASE_URL}/networks/{device['network_id']}"
        payload = {'tags': changes['tags']}
        result = make_edit_api_request(url, method='PUT', payload=payload)
        if not result:
            update_success = False
    if update_success:
        log_change(serial, changes, user_ip or "web")
        return {"message": "Device updated successfully"}
    else:
        return {"error": "Failed to update device"}

def process_csv_upload(file_stream, user_ip):
    try:
        stream = StringIO(file_stream.read().decode("UTF8"))
        csv_reader = csv.DictReader(stream)
        required_fields = {'serial', 'notes', 'tags'}
        if not required_fields.issubset(set(csv_reader.fieldnames)):
            return {"error": f"CSV must contain these columns: {required_fields}"}
        results = []
        inventory = load_latest_inventory(file_prefix="mx_inventory_live_")
        if not inventory:
            return {"error": "Inventory not found"}
        devices_by_serial = {d['device_serial']: d for d in inventory.get('devices', [])}
        for row in csv_reader:
            serial = row['serial'].strip()
            if serial not in devices_by_serial:
                results.append({
                    "serial": serial,
                    "status": "error",
                    "message": "Device not found in inventory"
                })
                continue
            device = devices_by_serial[serial]
            changes = {}
            new_notes = row['notes'].strip()
            if new_notes != device.get('raw_notes', ''):
                changes['notes'] = new_notes
            new_tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
            current_tags = device.get('network_tags', [])
            if set(new_tags) != set(current_tags):
                changes['tags'] = new_tags
            if not changes:
                results.append({
                    "serial": serial,
                    "status": "skipped",
                    "message": "No changes detected"
                })
                continue
            update_result = update_device_info(
                serial,
                changes.get('notes'),
                changes.get('tags'),
                f"csv_upload:{user_ip}"
            )
            if 'error' not in update_result:
                results.append({
                    "serial": serial,
                    "status": "success",
                    "message": "Device updated successfully",
                    "changes": list(changes.keys())
                })
            else:
                results.append({
                    "serial": serial,
                    "status": "error",
                    "message": update_result['error']
                })
        return {"results": results}
    except Exception as e:
        return {"error": f"Error processing CSV: {str(e)}"}

@app.route('/information.html')
def information():
    inventory = load_latest_inventory(file_prefix="mx_inventory_live_")
    if not inventory:
        return render_template('information.html',
                              error="No inventory data found",
                              devices=[],
                              last_update=None)
    try:
        return render_template('information.html',
                              devices=inventory.get('devices', []),
                              last_update=LAST_UPDATE,
                              error=None)
    except Exception as e:
        print(f"Error loading inventory data for information.html: {e}")
        return render_template('information.html',
                              error=f"Error loading inventory data: {str(e)}",
                              devices=[],
                              last_update=None)

@app.route('/api/information/devices')
def get_information_devices():
    inventory = load_latest_inventory(file_prefix="mx_inventory_live_")
    if not inventory:
        return jsonify({"error": "Inventory not found"}), 404
    return jsonify(inventory.get('devices', []))

@app.route('/api/information/update_device', methods=['POST'])
def information_update_device():
    data = request.json
    if not data or 'serial' not in data:
        return jsonify({"error": "Invalid request"}), 400
    result = update_device_info(
        data['serial'],
        data.get('notes'),
        data.get('tags'),
        request.remote_addr
    )
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/information/upload_csv', methods=['POST'])
def information_upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are allowed"}), 400
    result = process_csv_upload(file.stream, request.remote_addr)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='localhost', port=5051, debug=True)
