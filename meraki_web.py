#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import glob
from datetime import datetime
import os
from dotenv import load_dotenv
import csv
from io import StringIO
import requests
import itertools

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Initialize Flask app
app = Flask(__name__,
            template_folder='/usr/local/bin/templates',
            static_folder='/usr/local/bin/static')

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"
CHANGELOG_DIR = os.path.join(INVENTORY_DIR, "changelogs")
os.makedirs(CHANGELOG_DIR, exist_ok=True)
ORG_NAME = os.getenv('ORG_NAME')
LATEST_JSON = None
LAST_UPDATE = None
BASE_URL = "https://api.meraki.com/api/v1"

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

def load_latest_inventory(file_prefix="wan_metrics_"):
    global LATEST_JSON, LAST_UPDATE
    files = sorted(
        [f for f in os.listdir(INVENTORY_DIR) if f.startswith(file_prefix)],
        key=lambda x: os.path.getmtime(os.path.join(INVENTORY_DIR, x)),
        reverse=True
    )
    if not files:
        print(f"No files found with prefix {file_prefix}")
        LATEST_JSON = [] if file_prefix == "wan_metrics_" else {}
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
        LATEST_JSON = [] if file_prefix == "wan_metrics_" else {}
        LAST_UPDATE = None
    return LATEST_JSON

def clean_csv(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    cleaned_data = data.decode('utf-8', errors='replace')
    cleaned_file_path = file_path + '.cleaned'
    with open(cleaned_file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_data)
    return cleaned_file_path

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

@app.route('/')
def index():
    load_latest_inventory()
    return render_template('index.html',
                          org_name=ORG_NAME,
                          last_update=LAST_UPDATE,
                          total_sites=len(LATEST_JSON))

@app.route('/api/devices')
def get_devices():
    load_latest_inventory()
    return jsonify(LATEST_JSON)

@app.route('/api/search')
def search_devices():
    query = request.args.get('q', '').lower()
    load_latest_inventory()
    if not LATEST_JSON or not query:
        return jsonify([])
    results = []
    for device in LATEST_JSON:
        wan_label = device.get('wanLabel', '').lower()
        store = device.get('store', '').lower()
        tags = [tag.lower() for tag in device.get('tags', [])]
        if query in wan_label or query in store or query in tags:
            device['matches'] = []
            if query in wan_label:
                device['matches'].append('WAN')
            if query in store:
                device['matches'].append('Store')
            if query in tags:
                device['matches'].append('Tag')
            results.append(device)
    return jsonify(results)

@app.route('/metrics')
def get_metrics():
    from collections import defaultdict
    date_param = request.args.get('date', '')
    date_str = date_param if date_param else datetime.now().strftime("%Y%m%d")
    filename = f"wan_metrics_{date_str}.json"
    filepath = os.path.join(INVENTORY_DIR, filename)
    latest_by_device = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    key = (record['store'], record['uplink'])
                    latest_by_device[key] = record
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON line: {e}")
    except Exception as e:
        print(f"Error loading metrics file {filepath}: {e}")
    return jsonify(list(latest_by_device.values()))

@app.route('/tags')
def get_tags():
    tag_file = os.path.join(INVENTORY_DIR, "tags_cache.json")
    try:
        with open(tag_file, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        print(f"Error loading tag cache: {e}")
        return jsonify([])

@app.route('/issues.html')
def issues():
    return render_template('issues.html')

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

@app.route('/master.html')
def master():
    json_file_path = '/var/www/html/circuitinfo/master_list_data.json'
    try:
        with open(json_file_path, 'r') as json_file:
            master_list_data = json.load(json_file)
    except Exception as e:
        master_list_data = []
        print(f"Error loading Master List data: {e}")
    return render_template('master.html', stores=master_list_data)

@app.route('/ready_matrix.html')
def ready_matrix():
    ready_matrix_file = os.path.join(INVENTORY_DIR, 'ready_matrix_data.json')
    try:
        with open(ready_matrix_file, 'r') as f:
            ready_matrix_data = json.load(f)
    except Exception as e:
        ready_matrix_data = []
        print(f"Error loading ready matrix data: {e}")
    return render_template('ready_matrix.html', data=ready_matrix_data)

@app.route('/new_circuit_contract.html', methods=['GET', 'POST'])
def new_circuit_contract():
    log_file = '/var/www/html/meraki-data/contract_update_log.txt'
    if request.method == 'POST':
        store_list = request.form.get('stores')
        store_list = store_list.strip().split('\n')
        with open(log_file, 'a') as log:
            log.write(f"Added stores: {', '.join(store_list)} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return render_template('new_circuit_contract.html', message=f"Stores added: {', '.join(store_list)}")
    return render_template('new_circuit_contract.html')

@app.route('/vision_live.html', methods=['GET', 'POST'])
def vision_live():
    log_file = '/var/www/html/meraki-data/vision_live_log.txt'
    if request.method == 'POST':
        store_list = request.form.get('stores')
        store_list = store_list.strip().split('\n')
        with open(log_file, 'a') as log:
            log.write(f"Added stores to Vision Production: {', '.join(store_list)} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return render_template('vision_live.html', message=f"Stores added to Vision Production: {', '.join(store_list)}")
    return render_template('vision_live.html')

@app.route('/vision_check.html', methods=['GET', 'POST'])
def vision_check():
    if request.method == 'POST':
        store_list = request.form.get('stores')
        store_list = store_list.strip().split('\n')
        vision_status_data = {'Vision Active': 0, 'Vision Inactive': 0}
        return render_template('vision_check.html', vision_status_data=vision_status_data, stores=store_list)
    return render_template('vision_check.html')

@app.route('/starlink_project_stores.html', methods=['GET', 'POST'])
def starlink_project_stores():
    log_file = '/var/www/html/meraki-data/starlink_project_log.txt'
    if request.method == 'POST':
        store_list = request.form.get('stores')
        store_list = store_list.strip().split('\n')
        with open(log_file, 'a') as log:
            log.write(f"Updated Starlink status for stores: {', '.join(store_list)} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return render_template('starlink_project_stores.html', message=f"Updated Starlink status for stores: {', '.join(store_list)}")
    return render_template('starlink_project_stores.html')

@app.route('/circuitinfo/<filename>')
def serve_csv(filename):
    csv_dir = '/var/www/html/circuitinfo/'
    return send_from_directory(csv_dir, filename)

@app.route('/dsrcircuits')
def dsrcircuits():
    csv_dir = '/var/www/html/circuitinfo/'
    csv_files = glob.glob(os.path.join(csv_dir, 'tracking_data_*.csv'))
    if not csv_files:
        print("No CSV files found")
        return render_template('dsrcircuits.html', error="No CSV files found.")
    csv_file_path = max(csv_files, key=os.path.getmtime)
    cleaned_file_path = clean_csv(csv_file_path)
    data = []
    try:
        with open(cleaned_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return render_template('dsrcircuits.html', error="Failed to load data from CSV.")
    enabled_data = [row for row in data if row.get('status', '').lower() == 'enabled']
    grouped_data = {}
    for row in enabled_data:
        site_name = row.get('Site Name', '').strip()
        if not site_name:
            continue
        if site_name not in grouped_data:
            grouped_data[site_name] = []
        grouped_data[site_name].append(row)
    return render_template('dsrcircuits.html', grouped_data=grouped_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)