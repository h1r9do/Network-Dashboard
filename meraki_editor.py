import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
import itertools
import csv
from io import StringIO

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"
CHANGELOG_DIR = os.path.join(INVENTORY_DIR, "changelogs")
os.makedirs(CHANGELOG_DIR, exist_ok=True)
BASE_URL = "https://api.meraki.com/api/v1"

# Load API keys
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

def make_api_request(url, method='GET', payload=None):
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

def load_latest_inventory():
    inventory_files = sorted(
        [f for f in os.listdir(INVENTORY_DIR) if f.startswith("mx_inventory_live_")],
        reverse=True
    )
    
    if not inventory_files:
        return None
        
    latest_file = os.path.join(INVENTORY_DIR, inventory_files[0])
    
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading inventory file: {e}")
        return None

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

def update_device(serial, notes=None, tags=None, user_ip=None):
    inventory = load_latest_inventory()
    if not inventory:
        return {"error": "Inventory not found"}
    
    # Find the device in inventory
    device = next((d for d in inventory['devices'] if d['device_serial'] == serial), None)
    if not device:
        return {"error": "Device not found"}
    
    # Prepare changes
    changes = {}
    if notes is not None and notes != device.get('raw_notes', ''):
        changes['notes'] = notes
    
    if tags is not None and set(tags) != set(device.get('network_tags', [])):
        changes['tags'] = tags
    
    if not changes:
        return {"message": "No changes detected"}
    
    # Update device in Meraki
    update_success = True
    if 'notes' in changes:
        url = f"{BASE_URL}/networks/{device['network_id']}/devices/{serial}"
        payload = {'notes': changes['notes']}
        result = make_api_request(url, method='PUT', payload=payload)
        if not result:
            update_success = False
    
    if 'tags' in changes and update_success:
        url = f"{BASE_URL}/networks/{device['network_id']}"
        payload = {'tags': changes['tags']}
        result = make_api_request(url, method='PUT', payload=payload)
        if not result:
            update_success = False
    
    if update_success:
        # Log the change
        log_change(serial, changes, user_ip or "web")
        return {"message": "Device updated successfully"}
    else:
        return {"error": "Failed to update device"}

def process_csv_upload(file_stream, user_ip):
    try:
        # Read CSV file
        stream = StringIO(file_stream.read().decode("UTF8"))
        csv_reader = csv.DictReader(stream)
        
        # Validate CSV format
        required_fields = {'serial', 'notes', 'tags'}
        if not required_fields.issubset(set(csv_reader.fieldnames)):
            return {"error": f"CSV must contain these columns: {required_fields}"}
        
        # Process each row
        results = []
        inventory = load_latest_inventory()
        if not inventory:
            return {"error": "Inventory not found"}
        
        devices_by_serial = {d['device_serial']: d for d in inventory['devices']}
        
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
            
            # Check notes
            new_notes = row['notes'].strip()
            if new_notes != device.get('raw_notes', ''):
                changes['notes'] = new_notes
            
            # Check tags
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
            
            # Update device
            update_result = update_device(
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