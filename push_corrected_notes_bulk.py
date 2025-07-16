#!/usr/bin/env python3
"""
Push Corrected Notes to Meraki for All Updated Stores
Processes all sites from live data, excluding the 55 changed sites
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
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
LIVE_DATA_FILE = "/tmp/live_meraki_all_except_55.json"
CHANGED_SITES_FILE = "/tmp/sites_with_circuit_changes.txt"

def load_changed_sites():
    """Load the 55 sites with circuit changes to exclude"""
    changed_sites = set()
    
    if os.path.exists(CHANGED_SITES_FILE):
        with open(CHANGED_SITES_FILE, 'r') as f:
            content = f.read().strip()
            sites = [site.strip() for site in content.split(',')]
            changed_sites = set(sites)
    
    return changed_sites

def normalize_provider(provider):
    """Normalize provider names"""
    if not provider or str(provider).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    # Remove common prefixes and suffixes
    provider_clean = provider_str
    
    provider_lower = provider_clean.lower()
    
    # Special provider detection
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('spacex') or 'spacex' in provider_lower:
        return "Starlink"  # SpaceX Services, Inc. = Starlink
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm', 'vzg')):
        return "VZW Cell"
    
    return provider_clean

def reformat_speed(speed, provider):
    """Reformat speed with special cases"""
    provider_lower = str(provider).lower()
    
    # Cell providers always get "Cell" speed
    if any(term in provider_lower for term in ['vzw cell', 'verizon', 'digi', 'inseego', 'vzw', 'vzg']):
        return "Cell"
    
    # Starlink always gets "Satellite" speed  
    if 'starlink' in provider_lower or 'spacex' in provider_lower:
        return "Satellite"
    
    # If no speed provided, return empty
    if not speed or str(speed).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    return str(speed)

def is_valid_arin_provider(arin_provider):
    """Check if ARIN provider data is useful"""
    if not arin_provider:
        return False
    arin_lower = arin_provider.lower()
    # Exclude non-useful ARIN responses
    if any(term in arin_lower for term in ['private ip', 'unknown', 'unallocated', 'reserved', 'private customer', 'no ip']):
        return False
    if arin_lower.startswith('arin error'):
        return False
    return True

def determine_final_provider_and_speed(dsr_match, arin_provider):
    """Determine final provider and speed using priority: DSR > ARIN"""
    if dsr_match:
        # Priority 1: DSR circuit match
        provider = normalize_provider(dsr_match['provider'])
        speed = reformat_speed(dsr_match.get('speed', ''), provider)
        return provider, speed
    elif is_valid_arin_provider(arin_provider):
        # Priority 2: ARIN provider data
        provider = normalize_provider(arin_provider)
        speed = reformat_speed('', provider)  # ARIN providers get standard speeds
        return provider, speed
    else:
        # No useful data
        return "", ""

def format_circuit_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Format circuit data into Meraki device notes"""
    notes_lines = []
    
    # WAN1 formatting
    if wan1_provider or wan1_speed:
        notes_lines.append("WAN 1")
        if wan1_provider:
            notes_lines.append(wan1_provider)
        if wan1_speed:
            notes_lines.append(wan1_speed)
    
    # WAN2 formatting
    if wan2_provider or wan2_speed:
        notes_lines.append("WAN 2")
        if wan2_provider:
            notes_lines.append(wan2_provider)
        if wan2_speed:
            notes_lines.append(wan2_speed)
    
    return "\n".join(notes_lines) if notes_lines else ""

def main():
    """Push corrected notes to all sites"""
    print("🚀 Pushing Corrected Notes to Meraki")
    print("=" * 60)
    
    # Load changed sites to exclude
    changed_sites = load_changed_sites()
    print(f"✅ Excluding {len(changed_sites)} sites with circuit changes")
    
    # Load live data
    if not os.path.exists(LIVE_DATA_FILE):
        print(f"❌ Live data file not found: {LIVE_DATA_FILE}")
        return
    
    with open(LIVE_DATA_FILE, 'r') as f:
        live_data = json.load(f)
    
    print(f"📊 Processing {len(live_data)} sites")
    
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Get organization
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    orgs = response.json()
    org_id = None
    for org in orgs:
        if org['name'] == ORG_NAME:
            org_id = org['id']
            break
    
    print(f"✅ Organization: {org_id}")
    
    # Get all networks for lookup
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    
    # Create network lookup by name
    network_lookup = {net['name']: net['id'] for net in networks}
    
    # Get all devices in one call
    print("🔄 Getting all devices...")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/devices", headers=headers)
    all_devices = response.json()
    
    # Create device lookup by network ID
    device_lookup = {}
    for device in all_devices:
        if device.get('model', '').startswith('MX'):
            network_id = device.get('networkId')
            if network_id:
                device_lookup[network_id] = device
    
    print(f"✅ Found {len(device_lookup)} MX devices")
    
    # Process sites
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for site_data in live_data:
        network_name = site_data['network_name']
        
        # Skip changed sites
        if network_name in changed_sites:
            print(f"   ⏭️  Skipping {network_name} (circuit changed)")
            skipped_count += 1
            continue
        
        # Get network ID
        network_id = network_lookup.get(network_name)
        if not network_id:
            print(f"   ⚠️  {network_name}: Network not found")
            continue
        
        # Get device
        device = device_lookup.get(network_id)
        if not device:
            print(f"   ⚠️  {network_name}: No MX device found")
            continue
        
        device_serial = device['serial']
        
        # Determine providers and speeds
        wan1_data = site_data['wan1']
        wan2_data = site_data['wan2']
        
        wan1_provider, wan1_speed = determine_final_provider_and_speed(
            wan1_data.get('dsr_match'),
            wan1_data.get('arin_provider')
        )
        
        wan2_provider, wan2_speed = determine_final_provider_and_speed(
            wan2_data.get('dsr_match'),
            wan2_data.get('arin_provider')
        )
        
        # Format notes
        corrected_notes = format_circuit_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed)
        
        if not corrected_notes:
            print(f"   ⚠️  {network_name}: No notes to update")
            continue
        
        # Update device notes
        try:
            update_data = {"notes": corrected_notes}
            response = requests.put(
                f"{BASE_URL}/devices/{device_serial}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                print(f"   ✅ {network_name}: Updated with {wan1_provider}/{wan2_provider}")
                updated_count += 1
            else:
                print(f"   ❌ {network_name}: Error {response.status_code} - {response.text}")
                error_count += 1
            
            # Rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"   ❌ {network_name}: Exception - {str(e)}")
            error_count += 1
    
    print(f"\n📋 SUMMARY:")
    print(f"   Sites updated: {updated_count}")
    print(f"   Sites skipped (circuit changes): {skipped_count}")
    print(f"   Errors: {error_count}")
    print(f"\n✅ Notes push completed!")

if __name__ == "__main__":
    main()