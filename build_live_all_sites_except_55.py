#!/usr/bin/env python3
"""
Build Live Meraki Data for All Sites Except the 55 Changed Sites
Collects fresh IP and ARIN data for all sites minus the known good ones
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

def load_changed_sites():
    """Load the 55 sites with circuit changes to exclude"""
    changed_sites = set()
    
    if os.path.exists(CHANGED_SITES_FILE):
        with open(CHANGED_SITES_FILE, 'r') as f:
            content = f.read().strip()
            # Parse comma-separated sites
            sites = [site.strip() for site in content.split(',')]
            changed_sites = set(sites)
    
    print(f"✅ Loaded {len(changed_sites)} sites to exclude")
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
    """Process all sites except the 55 changed ones"""
    print("🔄 Building Live Meraki JSON - All Sites Except 55 Changed")
    print("=" * 60)
    
    # Load sites to exclude
    changed_sites = load_changed_sites()
    
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
            print(f"   ⏭️  Skipping {name} (circuit changed)")
            continue
        
        store_networks.append(network)
    
    print(f"✅ Found {len(store_networks)} store networks to process")
    
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
    
    print(f"✅ Found uplink data for {len(uplink_lookup)} networks")
    
    # Get all DSR circuits
    dsr_circuits = get_all_dsr_circuits()
    print(f"✅ Found DSR circuits for {len(dsr_circuits)} sites")
    
    # Process all store networks
    print(f"\n🔄 Processing {len(store_networks)} sites...")
    print("=" * 60)
    
    live_data = []
    processed = 0
    sites_without_provider = []
    
    for i, network in enumerate(store_networks):
        network_name = network['name']
        network_id = network['id']
        
        # Progress indicator
        if i % 50 == 0:
            print(f"\n📊 Progress: {i}/{len(store_networks)} sites processed...")
        
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
        
        # Log results for every 10th site
        if i % 10 == 0:
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
    
    print(f"\n📋 SUMMARY:")
    print(f"   Sites processed: {processed}")
    print(f"   Sites excluded (circuit changes): {len(changed_sites)}")
    print(f"   Sites without provider information: {len(sites_without_provider)}")
    print(f"   Output: {OUTPUT_FILE}")
    
    if sites_without_provider:
        print(f"\n❌ Sites without provider information ({len(sites_without_provider)}):")
        for site in sorted(sites_without_provider):
            print(f"   - {site}")
    
    print(f"\n✅ Live Meraki batch completed!")

if __name__ == "__main__":
    main()