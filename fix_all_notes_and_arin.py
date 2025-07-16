#!/usr/bin/env python3
"""
Comprehensive fix for all notes and ARIN data
1. Fix notes format (remove literal \n)
2. Update ARIN data from live collection
3. Push to Meraki devices
4. Update database with correct format
"""

import os
import json
import requests
import psycopg2
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
LIVE_DATA_FILE = "/tmp/live_meraki_all_except_55.json"

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

def is_valid_arin_provider(arin_provider):
    """Check if ARIN provider data is useful"""
    if not arin_provider:
        return False
    arin_lower = arin_provider.lower()
    if any(term in arin_lower for term in ['private ip', 'unknown', 'unallocated', 'reserved', 'no ip']):
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
        speed = reformat_speed('', provider)
        return provider, speed
    else:
        # No useful data
        return "", ""

def format_notes_with_newlines(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Format notes with actual newlines (not literal \n)"""
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
    return "\n".join(notes_lines) if notes_lines else ""

def main():
    """Fix all notes and ARIN data"""
    print("🔧 Comprehensive Fix for Notes and ARIN Data")
    print("=" * 60)
    
    # Load live data
    if not os.path.exists(LIVE_DATA_FILE):
        print(f"❌ Live data file not found: {LIVE_DATA_FILE}")
        print("   Please run build_live_meraki_batch.py first")
        return
    
    with open(LIVE_DATA_FILE, 'r') as f:
        live_data = json.load(f)
    
    print(f"📊 Loaded {len(live_data)} sites from live data")
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    # Get Meraki API headers
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
    
    # Get all networks
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    network_lookup = {net['name']: net['id'] for net in networks}
    
    # Get all devices
    print("🔄 Getting all devices...")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/devices", headers=headers)
    all_devices = response.json()
    
    # Create device lookup
    device_lookup = {}
    for device in all_devices:
        if device.get('model', '').startswith('MX'):
            network_id = device.get('networkId')
            if network_id:
                device_lookup[network_id] = device
    
    print(f"✅ Found {len(device_lookup)} MX devices")
    
    # Process each site
    updated_count = 0
    db_updated_count = 0
    error_count = 0
    
    for site_data in live_data:
        network_name = site_data['network_name']
        
        # Get network and device
        network_id = network_lookup.get(network_name)
        if not network_id:
            continue
        
        device = device_lookup.get(network_id)
        if not device:
            continue
        
        device_serial = device['serial']
        
        # Determine providers and speeds from live data
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
        
        # Format notes with real newlines
        corrected_notes = format_notes_with_newlines(wan1_provider, wan1_speed, wan2_provider, wan2_speed)
        
        if not corrected_notes:
            continue
        
        print(f"\n🔄 Processing {network_name}:")
        print(f"   WAN1: {wan1_provider} / {wan1_speed}")
        print(f"   WAN2: {wan2_provider} / {wan2_speed}")
        
        # 1. Update Meraki device
        try:
            update_data = {"notes": corrected_notes}
            response = requests.put(
                f"{BASE_URL}/devices/{device_serial}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                print(f"   ✅ Updated Meraki device")
                updated_count += 1
            else:
                print(f"   ❌ Meraki error: {response.status_code}")
                error_count += 1
            
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Meraki exception: {str(e)}")
            error_count += 1
        
        # 2. Update database - meraki_inventory table
        try:
            # Update notes with proper format and ARIN data
            cursor.execute("""
                UPDATE meraki_inventory 
                SET device_notes = %s,
                    wan1_arin_provider = %s,
                    wan2_arin_provider = %s,
                    last_updated = %s
                WHERE network_name = %s
            """, (
                corrected_notes,
                wan1_data.get('arin_provider', 'Unknown'),
                wan2_data.get('arin_provider', 'Unknown'),
                datetime.now(),
                network_name
            ))
            
            # Update enriched_circuits table (uses network_name not site_name)
            cursor.execute("""
                UPDATE enriched_circuits 
                SET wan1_provider = %s,
                    wan1_speed = %s,
                    wan2_provider = %s,
                    wan2_speed = %s,
                    wan1_arin_org = %s,
                    wan2_arin_org = %s,
                    last_updated = %s
                WHERE network_name = %s
            """, (
                wan1_provider,
                wan1_speed,
                wan2_provider,
                wan2_speed,
                wan1_data.get('arin_provider', 'Unknown'),
                wan2_data.get('arin_provider', 'Unknown'),
                datetime.now(),
                network_name
            ))
            
            conn.commit()
            db_updated_count += 1
            print(f"   ✅ Updated database")
            
        except Exception as e:
            print(f"   ❌ Database error: {str(e)}")
            conn.rollback()
    
    # Close database
    cursor.close()
    conn.close()
    
    print(f"\n📋 SUMMARY:")
    print(f"   Sites processed: {len(live_data)}")
    print(f"   Meraki devices updated: {updated_count}")
    print(f"   Database records updated: {db_updated_count}")
    print(f"   Errors: {error_count}")
    print(f"\n✅ Fix completed!")

if __name__ == "__main__":
    main()