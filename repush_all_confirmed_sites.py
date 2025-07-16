#!/usr/bin/env python3
"""
Repush all confirmed sites with the correct multi-line format to Meraki
This ensures all sites have the proper format: "WAN 1\nProvider\nSpeed\nWAN 2\nProvider\nSpeed"
"""
import os
import sys
import json
import requests
import psycopg2
import re
import time
from datetime import datetime
from dotenv import load_dotenv
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"

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

def get_network_devices(network_id):
    """Get devices for a network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting devices for network {network_id}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception getting devices for network {network_id}: {e}")
        return []

def update_device_notes(device_serial, notes):
    """Update device notes via Meraki API"""
    url = f"{BASE_URL}/devices/{device_serial}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {"notes": notes}
    
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"Error updating device {device_serial}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception updating device {device_serial}: {e}")
        return False

def build_notes_string(wan1_provider, wan1_speed, wan2_provider, wan2_speed, wan1_confirmed, wan2_confirmed):
    """Build the multi-line notes string in correct format"""
    notes_parts = []
    
    # Add WAN 1 if confirmed and has data
    if wan1_confirmed and wan1_provider and wan1_speed:
        notes_parts.extend([
            "WAN 1",
            wan1_provider,
            wan1_speed
        ])
    
    # Add WAN 2 if confirmed and has data
    if wan2_confirmed and wan2_provider and wan2_speed:
        notes_parts.extend([
            "WAN 2", 
            wan2_provider,
            wan2_speed
        ])
    
    return "\n".join(notes_parts) if notes_parts else ""

def main():
    print("=== Repushing all confirmed sites with correct format ===")
    
    # Get all confirmed enriched circuits with MX devices
    cursor.execute("""
        SELECT DISTINCT ec.network_name, ec.wan1_provider, ec.wan1_speed, ec.wan1_monthly_cost,
               ec.wan2_provider, ec.wan2_speed, ec.wan2_monthly_cost,
               ec.wan1_confirmed, ec.wan2_confirmed,
               mi.device_serial, mi.network_id
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE mi.device_model LIKE 'MX%'
        AND (ec.wan1_confirmed = TRUE OR ec.wan2_confirmed = TRUE)
        AND ec.network_name NOT ILIKE '%hub%'
        AND ec.network_name NOT ILIKE '%lab%'
        AND ec.network_name NOT ILIKE '%voice%'
        AND ec.network_name NOT ILIKE '%test%'
        AND ec.network_name NOT ILIKE '%datacenter%'
        AND ec.network_name NOT ILIKE '%store in a box%'
        ORDER BY ec.network_name
    """)
    
    confirmed_sites = cursor.fetchall()
    print(f"Found {len(confirmed_sites)} confirmed sites to repush")
    
    success_count = 0
    error_count = 0
    processed_sites = set()  # Track to avoid duplicates
    
    for row in confirmed_sites:
        network_name = row[0]
        
        # Skip if we already processed this site (in case of duplicate MX devices)
        if network_name in processed_sites:
            continue
        processed_sites.add(network_name)
        
        wan1_provider = row[1] or ""
        wan1_speed = row[2] or ""
        wan1_cost = row[3] or ""
        wan2_provider = row[4] or ""
        wan2_speed = row[5] or ""
        wan2_cost = row[6] or ""
        wan1_confirmed = row[7]
        wan2_confirmed = row[8]
        device_serial = row[9]
        network_id = row[10]
        
        print(f"\n--- Processing {network_name} ({device_serial}) ---")
        print(f"WAN1: {wan1_provider} - {wan1_speed} (Confirmed: {wan1_confirmed})")
        print(f"WAN2: {wan2_provider} - {wan2_speed} (Confirmed: {wan2_confirmed})")
        
        # Build the correct notes format
        notes = build_notes_string(wan1_provider, wan1_speed, wan2_provider, wan2_speed, 
                                   wan1_confirmed, wan2_confirmed)
        
        if not notes:
            print(f"  No confirmed data to push for {network_name}")
            continue
        
        print(f"  Notes format:")
        for line in notes.split('\n'):
            print(f"    {line}")
        
        # Update the device notes
        if update_device_notes(device_serial, notes):
            print(f"  ✓ Successfully updated {network_name}")
            success_count += 1
            
            # Update the database to mark as pushed
            cursor.execute("""
                UPDATE enriched_circuits
                SET pushed_to_meraki = TRUE,
                    pushed_date = CURRENT_TIMESTAMP
                WHERE network_name = %s
            """, (network_name,))
        else:
            print(f"  ✗ Failed to update {network_name}")
            error_count += 1
            
            # Do not update push status for failed attempts
            # Let them be retried later
        
        # Add small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Commit all database updates
    conn.commit()
    
    print(f"\n=== Summary ===")
    print(f"Total sites processed: {len(processed_sites)}")
    print(f"Successful pushes: {success_count}")
    print(f"Failed pushes: {error_count}")
    print(f"✓ All confirmed sites repushed with correct format!")

if __name__ == "__main__":
    main()
    cursor.close()
    conn.close()