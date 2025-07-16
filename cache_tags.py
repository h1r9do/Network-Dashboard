#!/usr/bin/env python3
import json
import os
import glob
from datetime import datetime
from collections import defaultdict

INVENTORY_DIR = "/var/www/html/meraki-data"
output_file = os.path.join(INVENTORY_DIR, "tags_cache.json")

files = sorted(
    glob.glob(os.path.join(INVENTORY_DIR, "mx_inventory_live_*.json")),
    key=os.path.getmtime,
    reverse=True
)
if not files:
    raise FileNotFoundError("No mx_inventory_live_*.json files found")

inventory_file = files[0]
store_tags = defaultdict(set)

try:
    with open(inventory_file, 'r') as f:
        data = json.load(f)
        for device in data.get('devices', []):
            store = device.get("network_name")
            for tag in device.get('network_tags', []):
                if store:
                    store_tags[store].add(tag)

    store_tags = {k: sorted(v) for k, v in store_tags.items()}
    with open(output_file, 'w') as out:
        json.dump(store_tags, out, indent=2)

    print(f"✅ Stored tag mapping for {len(store_tags)} stores")
except Exception as e:
    print(f"❌ Error processing tags: {e}")
