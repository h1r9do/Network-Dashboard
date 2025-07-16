#!/usr/bin/env python3
"""
Test fix for AZP 08 - Push corrected notes and verify
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"

def normalize_provider(provider):
    """Normalize provider names"""
    if not provider or str(provider).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    provider_lower = provider_str.lower()
    
    # Special provider detection
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('spacex') or 'spacex' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm', 'vzg')):
        return "VZW Cell"
    
    return provider_str

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

def main():
    """Test fix on AZP 08"""
    print("🧪 Testing Fix on AZP 08")
    print("=" * 60)
    
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Step 1: Get AZP 08 data from our live file
    live_data_file = "/tmp/live_meraki_all_except_55.json"
    azp08_data = None
    
    if os.path.exists(live_data_file):
        with open(live_data_file, 'r') as f:
            live_data = json.load(f)
        
        for site in live_data:
            if site['network_name'] == 'AZP 08':
                azp08_data = site
                break
    
    if not azp08_data:
        print("❌ AZP 08 not found in live data")
        return
    
    print("📊 Found AZP 08 in live data:")
    wan1 = azp08_data['wan1']
    wan2 = azp08_data['wan2']
    
    # Determine providers and speeds
    wan1_provider = ""
    wan1_speed = ""
    wan2_provider = ""
    wan2_speed = ""
    
    # WAN1
    if wan1.get('dsr_match'):
        wan1_provider = normalize_provider(wan1['dsr_match']['provider'])
        wan1_speed = reformat_speed(wan1['dsr_match'].get('speed', ''), wan1_provider)
    elif wan1.get('arin_provider') and wan1['arin_provider'] not in ['Unknown', 'Private IP', 'No IP']:
        wan1_provider = normalize_provider(wan1['arin_provider'])
        wan1_speed = reformat_speed('', wan1_provider)
    
    # WAN2
    if wan2.get('dsr_match'):
        wan2_provider = normalize_provider(wan2['dsr_match']['provider'])
        wan2_speed = reformat_speed(wan2['dsr_match'].get('speed', ''), wan2_provider)
    elif wan2.get('arin_provider') and wan2['arin_provider'] not in ['Unknown', 'Private IP', 'No IP']:
        wan2_provider = normalize_provider(wan2['arin_provider'])
        wan2_speed = reformat_speed('', wan2_provider)
    
    print(f"   WAN1: {wan1_provider} / {wan1_speed}")
    print(f"   WAN2: {wan2_provider} / {wan2_speed}")
    
    # Step 2: Format the notes properly
    notes_lines = []
    
    # WAN1
    if wan1_provider or wan1_speed:
        notes_lines.append("WAN 1")
        if wan1_provider:
            notes_lines.append(wan1_provider)
        if wan1_speed:
            notes_lines.append(wan1_speed)
    
    # WAN2
    if wan2_provider or wan2_speed:
        notes_lines.append("WAN 2")
        if wan2_provider:
            notes_lines.append(wan2_provider)
        if wan2_speed:
            notes_lines.append(wan2_speed)
    
    # Join with actual newlines
    corrected_notes = "\n".join(notes_lines)
    
    print("\n📝 Notes to apply:")
    print("=" * 40)
    print(corrected_notes)
    print("=" * 40)
    print(f"\n🔍 Raw representation: {repr(corrected_notes)}")
    
    # Step 3: Get AZP 08 device serial
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    orgs = response.json()
    org_id = None
    for org in orgs:
        if org['name'] == ORG_NAME:
            org_id = org['id']
            break
    
    # Get networks
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    
    # Find AZP 08
    azp08_network_id = None
    for network in networks:
        if network['name'] == 'AZP 08':
            azp08_network_id = network['id']
            break
    
    if not azp08_network_id:
        print("❌ AZP 08 network not found")
        return
    
    # Get devices
    response = requests.get(f"{BASE_URL}/networks/{azp08_network_id}/devices", headers=headers)
    devices = response.json()
    
    # Find MX device
    mx_device = None
    for device in devices:
        if device.get('model', '').startswith('MX'):
            mx_device = device
            break
    
    if not mx_device:
        print("❌ No MX device found")
        return
    
    device_serial = mx_device['serial']
    print(f"\n📊 Device serial: {device_serial}")
    
    # Step 4: Update the device
    update_data = {"notes": corrected_notes}
    response = requests.put(
        f"{BASE_URL}/devices/{device_serial}",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        print("✅ Successfully updated AZP 08 notes!")
    else:
        print(f"❌ Error updating: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Step 5: Wait a moment then pull the notes back
    print("\n⏳ Waiting 3 seconds before verification...")
    time.sleep(3)
    
    # Pull the device info again
    response = requests.get(f"{BASE_URL}/devices/{device_serial}", headers=headers)
    if response.status_code == 200:
        device_data = response.json()
        updated_notes = device_data.get('notes', '')
        
        print("\n📝 Verified notes from Meraki:")
        print("=" * 40)
        print(updated_notes)
        print("=" * 40)
        print(f"\n🔍 Raw representation: {repr(updated_notes)}")
        
        # Check for issues
        if '\\n' in updated_notes:
            print("\n❌ Still has literal \\n characters!")
        elif '\n' not in updated_notes and 'WAN' in updated_notes:
            print("\n⚠️  No newlines found!")
        else:
            print("\n✅ Notes are properly formatted with newlines!")
    else:
        print(f"❌ Error retrieving device: {response.status_code}")

if __name__ == "__main__":
    main()