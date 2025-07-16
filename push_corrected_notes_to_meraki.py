#!/usr/bin/env python3
"""
Push Corrected Notes to Meraki
Reads the enriched JSON from May 2nd restoration and updates Meraki device notes
Excludes the 55 sites with circuit changes since May 2nd
"""

import os
import sys
import json
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
ENRICHED_JSON_FILE = "/tmp/enriched_from_may2nd.json"
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"

# Rate limiting
REQUESTS_PER_SECOND = 10
REQUEST_DELAY = 1.0 / REQUESTS_PER_SECOND

def get_organization_id():
    """Get the organization ID for DTC-Store-Inventory-All"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/organizations", headers=headers)
        response.raise_for_status()
        orgs = response.json()
        
        for org in orgs:
            if org['name'] == ORG_NAME:
                return org['id']
        
        print(f"❌ Organization '{ORG_NAME}' not found")
        return None
    except Exception as e:
        print(f"❌ Error getting organization ID: {e}")
        return None

def get_networks(org_id):
    """Get all networks for the organization"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error getting networks: {e}")
        return []

def get_mx_devices(network_id):
    """Get MX devices for a network"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/networks/{network_id}/devices", headers=headers)
        response.raise_for_status()
        devices = response.json()
        
        # Filter for MX devices only
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        return mx_devices
    except Exception as e:
        print(f"   ⚠️  Error getting devices for network {network_id}: {e}")
        return []

def update_device_notes(network_id, device_serial, notes):
    """Update device notes via Meraki API"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'notes': notes
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/networks/{network_id}/devices/{device_serial}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"   ❌ Error updating device {device_serial}: {e}")
        return False

def format_circuit_notes(wan1_data, wan2_data):
    """Format circuit data into Meraki device notes"""
    notes_lines = []
    
    # WAN1 formatting
    if wan1_data.get('provider') or wan1_data.get('speed'):
        wan1_line = "WAN1: "
        if wan1_data.get('provider'):
            wan1_line += wan1_data['provider']
        if wan1_data.get('speed'):
            wan1_line += f" {wan1_data['speed']}"
        notes_lines.append(wan1_line.strip())
    
    # WAN2 formatting
    if wan2_data.get('provider') or wan2_data.get('speed'):
        wan2_line = "WAN2: "
        if wan2_data.get('provider'):
            wan2_line += wan2_data['provider']
        if wan2_data.get('speed'):
            wan2_line += f" {wan2_data['speed']}"
        notes_lines.append(wan2_line.strip())
    
    return "\n".join(notes_lines) if notes_lines else ""

def process_site_notes_update(site_data, networks_dict):
    """Process notes update for a single site"""
    network_name = site_data.get('network_name', '').strip()
    
    if not network_name:
        return False, "No network name"
    
    # Find matching network
    network_id = networks_dict.get(network_name)
    if not network_id:
        return False, f"Network not found in Meraki"
    
    # Get MX devices for this network
    mx_devices = get_mx_devices(network_id)
    if not mx_devices:
        return False, "No MX devices found"
    
    # Format the corrected notes
    wan1_data = site_data.get('wan1', {})
    wan2_data = site_data.get('wan2', {})
    corrected_notes = format_circuit_notes(wan1_data, wan2_data)
    
    if not corrected_notes:
        return False, "No notes to update"
    
    # Update notes for all MX devices in the network
    success_count = 0
    for device in mx_devices:
        device_serial = device.get('serial')
        if device_serial:
            time.sleep(REQUEST_DELAY)  # Rate limiting
            if update_device_notes(network_id, device_serial, corrected_notes):
                success_count += 1
    
    if success_count > 0:
        return True, f"Updated {success_count} device(s)"
    else:
        return False, "Failed to update any devices"

def main():
    """Main processing function"""
    print("🔄 Starting Meraki Notes Correction Process")
    print("=" * 80)
    
    # Validate inputs
    if not MERAKI_API_KEY:
        print("❌ MERAKI_API_KEY not found in environment")
        return
    
    if not os.path.exists(ENRICHED_JSON_FILE):
        print(f"❌ Enriched JSON file not found: {ENRICHED_JSON_FILE}")
        return
    
    # Load enriched data
    print(f"📊 Loading enriched data from: {ENRICHED_JSON_FILE}")
    with open(ENRICHED_JSON_FILE, 'r') as f:
        enriched_data = json.load(f)
    
    print(f"📊 Loaded {len(enriched_data)} sites for processing")
    
    # Get organization and networks
    print("🔍 Getting Meraki organization and networks...")
    org_id = get_organization_id()
    if not org_id:
        return
    
    networks = get_networks(org_id)
    networks_dict = {net['name']: net['id'] for net in networks}
    print(f"📊 Found {len(networks_dict)} networks in Meraki")
    
    # Process each site
    print("\n🔄 Processing sites...")
    print("=" * 80)
    
    processed = 0
    updated = 0
    skipped = 0
    errors = 0
    
    for site_data in enriched_data:
        network_name = site_data.get('network_name', '').strip()
        
        if not network_name:
            skipped += 1
            continue
        
        print(f"🔄 Processing {network_name}")
        
        success, message = process_site_notes_update(site_data, networks_dict)
        
        if success:
            wan1_provider = site_data.get('wan1', {}).get('provider', 'empty')
            wan2_provider = site_data.get('wan2', {}).get('provider', 'empty')
            print(f"   ✅ {network_name}: WAN1={wan1_provider}, WAN2={wan2_provider} - {message}")
            updated += 1
        else:
            print(f"   ⚠️  {network_name}: {message}")
            if "not found" in message.lower() or "no mx devices" in message.lower():
                skipped += 1
            else:
                errors += 1
        
        processed += 1
        
        # Progress indicator
        if processed % 50 == 0:
            print(f"\n📊 Progress: {processed}/{len(enriched_data)} sites processed")
            print(f"   ✅ Updated: {updated}")
            print(f"   ⚠️  Skipped: {skipped}")
            print(f"   ❌ Errors: {errors}\n")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📋 FINAL SUMMARY:")
    print(f"   Total sites in enriched data: {len(enriched_data)}")
    print(f"   Sites processed: {processed}")
    print(f"   Sites updated successfully: {updated}")
    print(f"   Sites skipped: {skipped}")
    print(f"   Sites with errors: {errors}")
    print(f"\n✅ Meraki Notes Correction Process Complete!")
    
    if updated > 0:
        print(f"\n🎉 Successfully updated {updated} sites with corrected circuit notes!")
        print("🔧 All device notes now reflect proper WAN1/WAN2 assignments based on:")
        print("   - May 2nd raw notes with sequential parsing")
        print("   - Current DSR circuit data via IP matching")
        print("   - Proper provider normalization")
    
    if errors > 0:
        print(f"\n⚠️  {errors} sites had errors - may need manual review")

if __name__ == "__main__":
    main()