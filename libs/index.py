#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

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
ORG_NAME = os.getenv('ORG_NAME')
LATEST_JSON = None
LAST_UPDATE = None

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

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/wanmetrics.html')
def wan_metrics():
    load_latest_inventory()
    return render_template('wanmetrics.html',
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

if __name__ == '__main__':
    app.run(host='localhost', port=5050, debug=True)
