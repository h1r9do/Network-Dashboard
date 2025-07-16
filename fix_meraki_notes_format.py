#!/usr/bin/env python3
"""
Fix Meraki device notes format for all MX devices
Converts from old format: WAN1: Provider Speed
To new format:
WAN 1
Provider
Speed
"""
import requests
import os
import psycopg2
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'

# Get database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(
    host=host,
    port=int(port),
    database=database,
    user=user,
    password=password
)
cursor = conn.cursor()

def get_headers():
    return {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }

def get_device_notes(serial):
    """Get current notes from a device"""
    try:
        url = f'{BASE_URL}/devices/{serial}'
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code == 429:  # Rate limited
            time.sleep(2)
            return get_device_notes(serial)
            
        if response.status_code == 200:
            device = response.json()
            return device.get('notes', '')
        else:
            print(f"Error getting device {serial}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception getting device {serial}: {e}")
        return None

def parse_old_format(notes):
    """Parse old format notes and extract WAN info"""
    if not notes:
        return None
        
    wan1_info = {'provider': '', 'speed': ''}
    wan2_info = {'provider': '', 'speed': ''}
    
    lines = notes.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('WAN1:'):
            # Extract provider and speed from "WAN1: Provider Speed"
            parts = line.replace('WAN1:', '').strip().split(' ', 1)
            if len(parts) >= 1:
                wan1_info['provider'] = parts[0]
            if len(parts) >= 2:
                wan1_info['speed'] = parts[1]
        elif line.startswith('WAN2:'):
            # Extract provider and speed from "WAN2: Provider Speed"
            parts = line.replace('WAN2:', '').strip().split(' ', 1)
            if len(parts) >= 1:
                wan2_info['provider'] = parts[0]
            if len(parts) >= 2:
                wan2_info['speed'] = parts[1]
    
    # Fix cases where speed is Cell but provider is N/A or blank
    if wan1_info['speed'] == 'Cell' and (not wan1_info['provider'] or wan1_info['provider'] == 'N/A'):
        wan1_info['provider'] = 'Cell'
    if wan2_info['speed'] == 'Cell' and (not wan2_info['provider'] or wan2_info['provider'] == 'N/A'):
        wan2_info['provider'] = 'Cell'
    
    # Only return if we found WAN info
    if wan1_info['provider'] or wan2_info['provider']:
        return {'wan1': wan1_info, 'wan2': wan2_info}
    
    return None

def format_new_notes(wan_data):
    """Format WAN data into new notes format"""
    notes_parts = []
    
    if wan_data['wan1']['provider'] and wan_data['wan1']['speed']:
        notes_parts.extend([
            "WAN 1",
            wan_data['wan1']['provider'],
            wan_data['wan1']['speed']
        ])
    
    if wan_data['wan2']['provider'] and wan_data['wan2']['speed']:
        notes_parts.extend([
            "WAN 2",
            wan_data['wan2']['provider'],
            wan_data['wan2']['speed']
        ])
    
    return '\n'.join(notes_parts)

def update_device_notes(serial, new_notes):
    """Update device notes via Meraki API"""
    try:
        url = f'{BASE_URL}/devices/{serial}'
        data = {'notes': new_notes}
        response = requests.put(url, headers=get_headers(), json=data, timeout=30)
        
        if response.status_code == 429:  # Rate limited
            time.sleep(2)
            return update_device_notes(serial, new_notes)
            
        if response.status_code == 200:
            return True
        else:
            print(f"Error updating device {serial}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Exception updating device {serial}: {e}")
        return False

# Main execution
print("Getting all MX devices from database...")
cursor.execute("""
    SELECT DISTINCT network_name, device_serial, device_model
    FROM meraki_inventory
    WHERE device_model LIKE 'MX%'
    AND network_name NOT ILIKE '%hub%'
    AND network_name NOT ILIKE '%voice%'
    AND network_name NOT ILIKE '%lab%'
    AND network_name NOT ILIKE '%test%'
    AND network_name NOT ILIKE '%datacenter%'
    ORDER BY network_name
""")

devices = cursor.fetchall()
print(f"Found {len(devices)} MX devices to check")

# Store all device notes
all_device_notes = []
devices_to_fix = []

print("\nPulling notes from all devices...")
for i, (network_name, device_serial, device_model) in enumerate(devices):
    if i % 10 == 0:
        print(f"Progress: {i}/{len(devices)} devices...")
    
    notes = get_device_notes(device_serial)
    
    device_info = {
        'network_name': network_name,
        'device_serial': device_serial,
        'device_model': device_model,
        'current_notes': notes,
        'needs_fix': False,
        'new_notes': None
    }
    
    # Check if notes need fixing
    if notes and ':' in notes and 'WAN' in notes:
        # Check if it's the old format (contains colon after WAN)
        if 'WAN1:' in notes or 'WAN2:' in notes:
            parsed = parse_old_format(notes)
            if parsed:
                new_notes = format_new_notes(parsed)
                device_info['needs_fix'] = True
                device_info['new_notes'] = new_notes
                devices_to_fix.append(device_info)
    
    all_device_notes.append(device_info)
    
    # Rate limit compliance
    time.sleep(0.1)

# Save all notes to file for backup
backup_file = f'/var/log/meraki_notes_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(backup_file, 'w') as f:
    json.dump(all_device_notes, f, indent=2)
print(f"\nBacked up all device notes to: {backup_file}")

# Display devices that need fixing
print(f"\nFound {len(devices_to_fix)} devices with old format notes that need fixing:")
for device in devices_to_fix[:10]:  # Show first 10
    print(f"\n{device['network_name']} ({device['device_serial']}):")
    print("Current notes:")
    print(device['current_notes'])
    print("New notes:")
    print(device['new_notes'])
    print("-" * 40)

if len(devices_to_fix) > 10:
    print(f"\n... and {len(devices_to_fix) - 10} more devices")

# Ask for confirmation
response = input(f"\nDo you want to update {len(devices_to_fix)} devices? (yes/no): ")

if response.lower() == 'yes':
    print("\nUpdating devices...")
    success_count = 0
    error_count = 0
    
    for i, device in enumerate(devices_to_fix):
        print(f"Updating {device['network_name']} ({i+1}/{len(devices_to_fix)})...")
        
        if update_device_notes(device['device_serial'], device['new_notes']):
            success_count += 1
            print(f"  ✓ Success")
        else:
            error_count += 1
            print(f"  ✗ Failed")
        
        # Rate limit compliance
        time.sleep(0.5)
    
    print(f"\nUpdate complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
else:
    print("\nUpdate cancelled.")

cursor.close()
conn.close()