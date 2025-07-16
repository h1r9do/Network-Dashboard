#!/usr/bin/env python3
"""Export Meraki inventory from database to JSON for legacy scripts"""

import json
import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

conn = get_db_connection()
cursor = conn.cursor()

# Get Meraki data
cursor.execute("""
    SELECT DISTINCT ON (network_name) 
        network_name, 
        device_tags,
        device_serial,
        device_model
    FROM meraki_inventory 
    WHERE network_name IS NOT NULL
    ORDER BY network_name, last_updated DESC
""")

meraki_data = []
for row in cursor.fetchall():
    network_name, tags, serial, model = row
    meraki_data.append({
        "network_name": network_name,
        "device_tags": tags or [],
        "serial": serial,
        "model": model,
        "wan1": {
            "provider": "",
            "speed": "",
            "ip": ""
        },
        "wan2": {
            "provider": "",
            "speed": "",
            "ip": ""
        },
        "raw_notes": ""
    })

# Create directory if needed
os.makedirs("/var/www/html/meraki-data", exist_ok=True)

# Write JSON file
with open("/var/www/html/meraki-data/mx_inventory_live.json", "w") as f:
    json.dump(meraki_data, f, indent=2)

print(f"Exported {len(meraki_data)} Meraki networks to mx_inventory_live.json")

cursor.close()
conn.close()