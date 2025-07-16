#!/usr/bin/env python3

import os
import requests
import time
import datetime
import json
import re
from dotenv import load_dotenv

# Load API keys
load_dotenv('/usr/local/bin/meraki.env')
api_keys = [v for k, v in os.environ.items() if k.startswith("MERAKI_API_KEY")]
if not api_keys:
    raise RuntimeError("❌ No API keys found in environment.")
print(f"🔑 Using {len(api_keys)} API keys")

BASE_URL = "https://api.meraki.com/api/v1"
DEST_IP = "8.8.8.8"  # Updated to Google DNS
MAX_TIMESPAN = 900
RESOLUTION = 60
REQUEST_DELAY = 0.3
RESULTS = []

# Load and sort inventory
DATA_DIR = "/var/www/html/meraki-data"
inventory_files = sorted(
    [f for f in os.listdir(DATA_DIR) if f.startswith("mx_inventory_live_") and f.endswith(".json")],
    key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)),
    reverse=True
)
if not inventory_files:
    raise FileNotFoundError("No mx_inventory_live_*.json found")

latest_inventory = os.path.join(DATA_DIR, inventory_files[0])
with open(latest_inventory) as f:
    devices = json.load(f).get("devices", [])

# Define filter for valid store names
def is_valid_store(name):
    name = name.strip().upper()
    if "00" in name:
        return False
    return bool(re.match(r"^[A-Z]+ \d{2}$", name))

# Apply the store name filter
devices = [d for d in devices if is_valid_store(d.get("network_name", ""))]
devices = sorted(devices, key=lambda d: d.get("network_name", "").strip().upper())

def make_api_request(url, api_key, params=None):
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    for _ in range(3):
        try:
            time.sleep(REQUEST_DELAY)
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 1))
                print(f"⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"RequestException: {str(e)}"
    return "Failed after retries"

success = 0
empty = 0
fail = 0

# Progress counters
total_queries = len(devices) * 2  # 2 uplinks per device
current_query = 0

for device in devices:
    store = device.get("network_name")
    serial = device.get("device_serial")
    for uplink in ["wan1", "wan2"]:
        current_query += 1
        url = f"{BASE_URL}/devices/{serial}/lossAndLatencyHistory"
        params = {
            "uplink": uplink,
            "ip": DEST_IP,
            "timespan": MAX_TIMESPAN,
            "resolution": RESOLUTION
        }
        key = api_keys[(hash(serial + uplink) % len(api_keys))]
        
        result = make_api_request(url, key, params)
        if isinstance(result, list) and result:
            outcome = "✅ PASS"
            success += 1
        elif isinstance(result, list) and not result:
            outcome = "⚠️ EMPTY"
            empty += 1
        else:
            outcome = "❌ FAIL"
            fail += 1
        
        record = {
            "store": store,
            "uplink": uplink,
            "serial": serial,
            "result": "success" if outcome == "✅ PASS" else (
                "empty" if outcome == "⚠️ EMPTY" else result)
        }
        RESULTS.append(record)

        print(f"[{current_query}/{total_queries}] {store} {uplink}: {outcome}")

# Print final summary
print("\n📋 Diagnostics Summary")
print(f"🟢 Success: {success} | ⚠️ Empty: {empty} | ❌ Failed: {fail}")

# Save all results to a file
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
output_path = f"/var/www/html/meraki-data/filtered_diagnostics_{ts}.json"
with open(output_path, "w") as f:
    json.dump(RESULTS, f, indent=2)

print(f"📝 Full results written to: {output_path}")
