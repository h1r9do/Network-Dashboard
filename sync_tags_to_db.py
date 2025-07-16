#!/usr/bin/env python3
"""
Quick sync of tags from Meraki API to database for verification
"""

import os
import requests
import sys
from dotenv import load_dotenv
from config import Config
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')

if not api_key:
    print("Error: MERAKI_API_KEY not found")
    sys.exit(1)

headers = {'X-Cisco-Meraki-API-Key': api_key}

# Test devices we know were updated
test_devices = [
    'Q2KY-52S4-M3GY',  # ILC 41 - Full-Service-Store
    'Q2JN-GYQE-Q9FQ',  # NMACALLCNTR - Call-Center
    'Q2QN-HDZ2-LMDR',  # MID W00 - Regional-Office, Warehouse
    'Q2QN-LB6S-CYET',  # AZP_00 - Regional-Office
]

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

print("Syncing tags for test devices...")

for device_serial in test_devices:
    print(f"\nProcessing {device_serial}:")
    
    # Get current tags from Meraki
    url = f'https://api.meraki.com/api/v1/devices/{device_serial}'
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            current_tags = data.get('tags', [])
            device_name = data.get('name', 'Unknown')
            print(f"  Device: {device_name}")
            print(f"  Meraki tags: {current_tags}")
            
            # Update database
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE meraki_inventory 
                    SET device_tags = :tags, last_updated = NOW()
                    WHERE device_serial = :serial
                """), {"tags": current_tags, "serial": device_serial})
                conn.commit()
            print(f"  ✓ Updated database")
        else:
            print(f"  ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\n✅ Sync complete!")