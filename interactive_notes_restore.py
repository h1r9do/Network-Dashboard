#!/usr/bin/env python3
"""
Interactive notes restoration - one site at a time with manual verification
"""

import os
import sys
import json
import requests
import time
from dotenv import load_dotenv
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def make_api_request(url, method="GET", data=None):
    headers = get_headers()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        
        response.raise_for_status()
        
        if method == "GET":
            return response.json()
        else:
            return {"success": True}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_site_info(site_name):
    """Get all info for a specific site"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get device info and enriched data
    cursor.execute("""
        SELECT 
            mi.device_serial,
            mi.network_name,
            mi.device_model,
            COALESCE(ec.wan1_provider, '') as wan1_provider,
            COALESCE(ec.wan1_speed, '') as wan1_speed,
            COALESCE(ec.wan2_provider, '') as wan2_provider,
            COALESCE(ec.wan2_speed, '') as wan2_speed,
            COALESCE(mi.wan1_provider_label, '') as wan1_provider_label,
            COALESCE(mi.wan2_provider_label, '') as wan2_provider_label
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
        WHERE mi.network_name = %s
        AND mi.device_model LIKE 'MX%%'
        LIMIT 1
    """, (site_name,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result:
        return None
    
    device_serial, network_name, device_model, w1p, w1s, w2p, w2s, w1p_label, w2p_label = result
    
    return {
        "device_serial": device_serial,
        "network_name": network_name,
        "device_model": device_model,
        "wan1_provider": w1p or "",
        "wan1_speed": w1s or "",
        "wan2_provider": w2p or "",
        "wan2_speed": w2s or "",
        "wan1_provider_label": w1p_label or "",
        "wan2_provider_label": w2p_label or ""
    }

def get_current_notes(device_serial):
    """Get current notes from Meraki device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    device_info = make_api_request(device_url)
    
    if "error" in device_info:
        return f"ERROR: {device_info['error']}"
    
    return device_info.get("notes", "") or ""

def format_expected_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Format expected clean notes"""
    lines = []
    
    # WAN 1 section
    if wan1_provider or wan1_speed:
        lines.append("WAN 1")
        if wan1_provider:
            lines.append(wan1_provider)
        if wan1_speed:
            lines.append(wan1_speed)
    
    # WAN 2 section
    if wan2_provider or wan2_speed:
        lines.append("WAN 2")
        if wan2_provider:
            lines.append(wan2_provider)
        if wan2_speed:
            lines.append(wan2_speed)
    
    return "\n".join(lines) if lines else ""

def update_device_notes(device_serial, new_notes):
    """Update notes for device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    data = {"notes": new_notes}
    
    result = make_api_request(device_url, method="PUT", data=data)
    return result

def process_site(site_name):
    """Process a single site with manual verification"""
    print(f"\n{'='*60}")
    print(f"PROCESSING SITE: {site_name}")
    print(f"{'='*60}")
    
    # Get site info
    site_info = get_site_info(site_name)
    if not site_info:
        print(f"❌ ERROR: Site '{site_name}' not found in database")
        return False
    
    device_serial = site_info["device_serial"]
    
    print(f"Device Serial: {device_serial}")
    print(f"Device Model: {site_info['device_model']}")
    print()
    
    # Get current notes
    print("📥 CURRENT NOTES FROM MERAKI DEVICE:")
    current_notes = get_current_notes(device_serial)
    if current_notes.startswith("ERROR"):
        print(f"❌ {current_notes}")
        return False
    
    print(f'"{current_notes}"')
    print()
    print("Current notes formatted:")
    print(current_notes.replace('\n', '\n'))
    print()
    
    # Show database data
    print("📊 DATABASE PROCESSED DATA:")
    print(f"WAN1 Provider: '{site_info['wan1_provider']}'")
    print(f"WAN1 Speed: '{site_info['wan1_speed']}'")
    print(f"WAN2 Provider: '{site_info['wan2_provider']}'")
    print(f"WAN2 Speed: '{site_info['wan2_speed']}'")
    print()
    print(f"Provider Labels: WAN1='{site_info['wan1_provider_label']}', WAN2='{site_info['wan2_provider_label']}'")
    print()
    
    # Generate expected notes
    expected_notes = format_expected_notes(
        site_info["wan1_provider"],
        site_info["wan1_speed"],
        site_info["wan2_provider"],
        site_info["wan2_speed"]
    )
    
    print("📤 EXPECTED CLEAN NOTES TO PUSH:")
    print(f'"{expected_notes}"')
    print()
    print("Expected notes formatted:")
    print(expected_notes.replace('\n', '\n'))
    print()
    
    # Check if update needed
    needs_update = current_notes.strip() != expected_notes.strip()
    
    if not needs_update:
        print("✅ ALREADY CORRECT - No update needed")
        return True
    
    print("🔍 ANALYSIS:")
    print(f"  Current length: {len(current_notes)} chars")
    print(f"  Expected length: {len(expected_notes)} chars")
    print(f"  Update needed: {needs_update}")
    print()
    
    # Manual verification
    while True:
        choice = input("🤔 Do you want to update this device? (y/n/s/q): ").lower().strip()
        
        if choice == 'y':
            print("🚀 Updating device...")
            result = update_device_notes(device_serial, expected_notes)
            
            if "error" in result:
                print(f"❌ Update failed: {result['error']}")
                return False
            else:
                print("✅ Update successful!")
                
                # Verify the update
                print("🔍 Verifying update...")
                time.sleep(2)
                new_notes = get_current_notes(device_serial)
                if new_notes == expected_notes:
                    print("✅ Verification successful - notes match expected")
                else:
                    print("⚠️  Verification warning - notes don't match exactly")
                    print(f"Expected: {expected_notes}")
                    print(f"Actual: {new_notes}")
                
                return True
                
        elif choice == 'n':
            print("❌ Skipping update")
            return False
            
        elif choice == 's':
            print("⏭️  Skipping this site")
            return True
            
        elif choice == 'q':
            print("🛑 Quitting")
            exit(0)
            
        else:
            print("Please enter y (yes), n (no), s (skip), or q (quit)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 interactive_notes_restore.py <SITE_NAME>")
        print("Example: python3 interactive_notes_restore.py 'CAL 17'")
        sys.exit(1)
    
    site_name = sys.argv[1]
    success = process_site(site_name)
    
    if success:
        print(f"\n✅ Completed processing for {site_name}")
    else:
        print(f"\n❌ Failed to process {site_name}")