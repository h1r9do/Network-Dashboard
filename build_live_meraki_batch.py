#!/usr/bin/env python3
"""
Build Live Meraki JSON in Batches
Process first 50 sites to test the logic
"""

import os
import sys
import json
import requests
import time
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
OUTPUT_FILE = "/tmp/live_meraki_batch_50.json"

def get_arin_provider(ip_address):
    """Get ARIN provider information for an IP address"""
    if not ip_address or ip_address in ['', 'None', 'null']:
        return "Unknown"
    
    # Handle private IPs
    if ip_address.startswith(('192.168.', '10.', '172.')):
        return "Private IP"
    
    try:
        url = f'https://rdap.arin.net/registry/ip/{ip_address}'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract organization/provider name
            provider = "Unknown"
            
            # Try different paths to find the provider name
            if 'entities' in data:
                for entity in data['entities']:
                    if 'vcardArray' in entity:
                        vcard = entity['vcardArray'][1]
                        for field in vcard:
                            if field[0] == 'fn':
                                provider = field[3]
                                break
                    if provider != "Unknown":
                        break
            
            # Alternative: check the name field directly
            if provider == "Unknown" and 'name' in data:
                provider = data['name']
                
            return provider
        else:
            return f"ARIN Error {response.status_code}"
            
    except Exception as e:
        return f"ARIN Error: {str(e)}"

def get_all_dsr_circuits():
    """Get all enabled DSR circuits from database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                site_name,
                provider_name,
                details_ordered_service_speed,
                circuit_purpose,
                ip_address_start
            FROM circuits
            WHERE status = 'Enabled'
            ORDER BY site_name, circuit_purpose
        """)
        
        circuits = {}
        for row in cursor.fetchall():
            site_name = row[0]
            if site_name not in circuits:
                circuits[site_name] = []
            
            circuits[site_name].append({
                'provider': row[1],
                'speed': row[2],
                'purpose': row[3],
                'ip': row[4]
            })
        
        cursor.close()
        conn.close()
        
        return circuits
    except Exception as e:
        print(f"Error getting DSR circuits: {e}")
        return {}

def match_dsr_by_ip(wan_ip, site_circuits):
    """Match DSR circuit by IP address (handles flipped circuits)"""
    if not wan_ip or not site_circuits:
        return None
    
    for circuit in site_circuits:
        if circuit['ip'] and str(circuit['ip']).strip() == str(wan_ip).strip():
            return circuit
    
    return None

def main():
    """Process first 50 sites"""
    print("🔄 Building Live Meraki JSON - First 50 Sites")
    print("=" * 60)
    
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
    
    # Get networks
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    
    # Filter out hub/lab/voice/test networks
    store_networks = []
    for network in networks:
        name = network['name']
        if not any(tag in name.lower() for tag in ['hub', 'lab', 'voice', 'test', 'bsm']):
            store_networks.append(network)
    
    print(f"✅ Found {len(store_networks)} store networks")
    
    # Get all uplink statuses
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses", headers=headers)
    all_uplinks = response.json()
    
    # Create lookup for uplinks by network ID
    uplink_lookup = {}
    for uplink_data in all_uplinks:
        network_id = uplink_data.get('networkId')
        if network_id:
            uplink_lookup[network_id] = uplink_data.get('uplinks', [])
    
    print(f"✅ Found uplink data for {len(uplink_lookup)} networks")
    
    # Get all DSR circuits
    dsr_circuits = get_all_dsr_circuits()
    print(f"✅ Found DSR circuits for {len(dsr_circuits)} sites")
    
    # Process first 50 store networks
    print("\\n🔄 Processing first 50 sites...")
    print("=" * 60)
    
    live_data = []
    processed = 0
    
    for network in store_networks[:50]:
        network_name = network['name']
        network_id = network['id']
        
        # Get uplinks for this network
        uplinks = uplink_lookup.get(network_id, [])
        if len(uplinks) < 2:
            print(f"   ⚠️  {network_name}: Less than 2 uplinks")
            continue
        
        # Extract WAN IPs
        wan1_ip = uplinks[0].get('publicIp', '') if len(uplinks) > 0 else ''
        wan2_ip = uplinks[1].get('publicIp', '') if len(uplinks) > 1 else ''
        
        if not wan1_ip and not wan2_ip:
            print(f"   ⚠️  {network_name}: No public IPs")
            continue
        
        # Get ARIN data (with rate limiting)
        wan1_arin = get_arin_provider(wan1_ip) if wan1_ip else "No IP"
        time.sleep(0.3)  # ARIN rate limiting
        wan2_arin = get_arin_provider(wan2_ip) if wan2_ip else "No IP"
        time.sleep(0.3)  # ARIN rate limiting
        
        # Get DSR circuits for this site
        site_circuits = dsr_circuits.get(network_name, [])
        
        # Match by IP to DSR circuits (handles flipped circuits)
        wan1_dsr = match_dsr_by_ip(wan1_ip, site_circuits)
        wan2_dsr = match_dsr_by_ip(wan2_ip, site_circuits)
        
        # Build entry
        entry = {
            "network_name": network_name,
            "wan1": {
                "ip": wan1_ip,
                "arin_provider": wan1_arin,
                "status": uplinks[0].get('status', '') if len(uplinks) > 0 else '',
                "dsr_match": wan1_dsr
            },
            "wan2": {
                "ip": wan2_ip,
                "arin_provider": wan2_arin,
                "status": uplinks[1].get('status', '') if len(uplinks) > 1 else '',
                "dsr_match": wan2_dsr
            },
            "dsr_circuits": site_circuits,
            "collected_at": datetime.now().isoformat()
        }
        
        live_data.append(entry)
        
        # Log results
        dsr_info = f"{len(site_circuits)} DSR"
        if wan1_dsr:
            dsr_info += f", WAN1→{wan1_dsr['provider']}"
        if wan2_dsr:
            dsr_info += f", WAN2→{wan2_dsr['provider']}"
        
        print(f"   ✅ {network_name}: {wan1_arin[:15]} / {wan2_arin[:15]} ({dsr_info})")
        processed += 1
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(live_data, f, indent=2)
    
    print(f"\\n📋 SUMMARY:")
    print(f"   Sites processed: {processed}")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"\\n✅ Live Meraki batch completed!")

if __name__ == "__main__":
    main()