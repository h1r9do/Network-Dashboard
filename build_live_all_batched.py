#!/usr/bin/env python3
"""
Build Live Meraki Data in Batches - All Sites Except the 55 Changed
Processes in batches of 100 sites to avoid timeouts
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
OUTPUT_FILE = "/tmp/live_meraki_all_except_55.json"
CHANGED_SITES_FILE = "/tmp/sites_with_circuit_changes.txt"
BATCH_SIZE = 100
START_BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 0

def load_changed_sites():
    """Load the 55 sites with circuit changes to exclude"""
    changed_sites = set()
    
    if os.path.exists(CHANGED_SITES_FILE):
        with open(CHANGED_SITES_FILE, 'r') as f:
            content = f.read().strip()
            # Parse comma-separated sites
            sites = [site.strip() for site in content.split(',')]
            changed_sites = set(sites)
    
    return changed_sites

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
    """Process sites in batches"""
    print(f"🔄 Building Live Meraki JSON - Batch starting at {START_BATCH}")
    print("=" * 60)
    
    # Load sites to exclude
    changed_sites = load_changed_sites()
    print(f"✅ Loaded {len(changed_sites)} sites to exclude")
    
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
    
    # Filter out hub/lab/voice/test networks and changed sites
    store_networks = []
    for network in networks:
        name = network['name']
        # Skip non-store networks
        if any(tag in name.lower() for tag in ['hub', 'lab', 'voice', 'test', 'bsm']):
            continue
        # Skip changed sites
        if name in changed_sites:
            continue
        
        store_networks.append(network)
    
    print(f"✅ Found {len(store_networks)} store networks total")
    
    # Get batch to process
    end_batch = min(START_BATCH + BATCH_SIZE, len(store_networks))
    batch_networks = store_networks[START_BATCH:end_batch]
    
    print(f"📊 Processing batch: {START_BATCH} to {end_batch} ({len(batch_networks)} networks)")
    
    # Get all uplink statuses
    print("🔄 Getting all uplink statuses...")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses", headers=headers)
    all_uplinks = response.json()
    
    # Create lookup for uplinks by network ID
    uplink_lookup = {}
    for uplink_data in all_uplinks:
        network_id = uplink_data.get('networkId')
        if network_id:
            uplink_lookup[network_id] = uplink_data.get('uplinks', [])
    
    # Get all DSR circuits
    dsr_circuits = get_all_dsr_circuits()
    print(f"✅ Found DSR circuits for {len(dsr_circuits)} sites")
    
    # Load existing data if continuing
    live_data = []
    if START_BATCH > 0 and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            live_data = json.load(f)
        print(f"📊 Loaded {len(live_data)} existing entries")
    
    # Process batch
    processed = 0
    sites_without_provider = []
    
    for i, network in enumerate(batch_networks):
        network_name = network['name']
        network_id = network['id']
        
        # Get uplinks for this network
        uplinks = uplink_lookup.get(network_id, [])
        if len(uplinks) < 2:
            continue
        
        # Extract WAN IPs
        wan1_ip = uplinks[0].get('publicIp', '') if len(uplinks) > 0 else ''
        wan2_ip = uplinks[1].get('publicIp', '') if len(uplinks) > 1 else ''
        
        if not wan1_ip and not wan2_ip:
            sites_without_provider.append(network_name)
            continue
        
        # Get ARIN data (with rate limiting)
        wan1_arin = get_arin_provider(wan1_ip) if wan1_ip else "No IP"
        time.sleep(0.2)  # ARIN rate limiting
        wan2_arin = get_arin_provider(wan2_ip) if wan2_ip else "No IP"
        time.sleep(0.2)  # ARIN rate limiting
        
        # Get DSR circuits for this site
        site_circuits = dsr_circuits.get(network_name, [])
        
        # Match by IP to DSR circuits (handles flipped circuits)
        wan1_dsr = match_dsr_by_ip(wan1_ip, site_circuits)
        wan2_dsr = match_dsr_by_ip(wan2_ip, site_circuits)
        
        # Check if site has no provider information
        wan1_has_provider = wan1_dsr or (wan1_arin and wan1_arin not in ["Unknown", "Private IP", "No IP"] and not wan1_arin.startswith("ARIN Error"))
        wan2_has_provider = wan2_dsr or (wan2_arin and wan2_arin not in ["Unknown", "Private IP", "No IP"] and not wan2_arin.startswith("ARIN Error"))
        
        if not wan1_has_provider and not wan2_has_provider:
            sites_without_provider.append(network_name)
            print(f"   ❌ {network_name}: No provider information available")
        
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
        processed += 1
        
        # Progress update
        if i % 10 == 0:
            print(f"   ✅ Progress: {i+1}/{len(batch_networks)} - {network_name}")
    
    # Save output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(live_data, f, indent=2)
    
    print(f"\n📋 BATCH SUMMARY:")
    print(f"   Batch processed: {START_BATCH} to {end_batch}")
    print(f"   Sites processed in batch: {processed}")
    print(f"   Total sites in file: {len(live_data)}")
    print(f"   Sites without provider in batch: {len(sites_without_provider)}")
    
    if sites_without_provider:
        print(f"\n❌ Sites without provider information in this batch:")
        for site in sorted(sites_without_provider)[:10]:  # Show first 10
            print(f"   - {site}")
        if len(sites_without_provider) > 10:
            print(f"   ... and {len(sites_without_provider) - 10} more")
    
    print(f"\n✅ Batch completed!")
    
    # Suggest next batch
    if end_batch < len(store_networks):
        print(f"\n📝 To continue, run: python3 {sys.argv[0]} {end_batch}")
    else:
        print(f"\n✅ All sites processed! Total: {len(live_data)} sites")

if __name__ == "__main__":
    main()