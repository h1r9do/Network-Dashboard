#!/usr/bin/env python3
"""
Build Live Meraki JSON with Fresh IPs and ARIN Data
Bypasses database completely - gets fresh data directly from Meraki API and ARIN
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
OUTPUT_FILE = "/tmp/live_meraki_with_arin.json"

# Rate limiting
REQUESTS_PER_SECOND = 10
REQUEST_DELAY = 1.0 / REQUESTS_PER_SECOND

def get_arin_provider(ip_address):
    """Get ARIN provider information for an IP address"""
    if not ip_address or ip_address in ['', 'None', 'null']:
        return "Unknown"
    
    # Handle private IPs
    if ip_address.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
        return "Private IP"
    
    try:
        url = f'https://rdap.arin.net/registry/ip/{ip_address}'
        response = requests.get(url, timeout=10)
        
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

def get_dsr_circuits():
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
                ip_address_start,
                status
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
                'ip': row[4],
                'status': row[5]
            })
        
        cursor.close()
        conn.close()
        
        return circuits
    except Exception as e:
        print(f"Error getting DSR circuits: {e}")
        return {}

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

def get_all_uplink_statuses(org_id):
    """Get uplink statuses for all appliances in the organization"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error getting uplink statuses: {e}")
        return []

def get_devices_for_network(network_id):
    """Get MX devices for a specific network"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        time.sleep(REQUEST_DELAY)  # Rate limiting
        response = requests.get(f"{BASE_URL}/networks/{network_id}/devices", headers=headers)
        response.raise_for_status()
        devices = response.json()
        
        # Filter for MX devices only
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        return mx_devices
    except Exception as e:
        print(f"   ⚠️  Error getting devices for network {network_id}: {e}")
        return []

def match_dsr_by_ip(wan_ip, site_circuits):
    """Match DSR circuit by IP address"""
    if not wan_ip or not site_circuits:
        return None
    
    for circuit in site_circuits:
        if circuit['ip'] and str(circuit['ip']).strip() == str(wan_ip).strip():
            return circuit
    
    return None

def process_network(network, uplink_lookup, dsr_circuits):
    """Process a single network to build enriched data"""
    network_name = network['name']
    network_id = network['id']
    
    # Skip excluded networks (same logic as before)
    if any(tag in network_name.lower() for tag in ['hub', 'lab', 'voice', 'test']):
        return None
    
    # Get MX devices
    mx_devices = get_devices_for_network(network_id)
    if not mx_devices:
        return None
    
    mx_device = mx_devices[0]  # Take first MX device
    
    # Get uplink data for this network
    uplink_data = uplink_lookup.get(network_id)
    if not uplink_data:
        return None
    
    uplinks = uplink_data.get('uplinks', [])
    if len(uplinks) < 2:
        return None  # Need at least 2 uplinks
    
    # Extract WAN IPs
    wan1_ip = uplinks[0].get('publicIp', '') if len(uplinks) > 0 else ''
    wan2_ip = uplinks[1].get('publicIp', '') if len(uplinks) > 1 else ''
    
    # Get ARIN data for both IPs
    print(f"🔍 {network_name}: Getting ARIN data...")
    wan1_arin = get_arin_provider(wan1_ip)
    time.sleep(0.5)  # ARIN rate limiting
    wan2_arin = get_arin_provider(wan2_ip)
    time.sleep(0.5)  # ARIN rate limiting
    
    # Get DSR circuits for this site
    site_circuits = dsr_circuits.get(network_name, [])
    
    # Match by IP to DSR circuits (accommodate flipped circuits)
    wan1_dsr = match_dsr_by_ip(wan1_ip, site_circuits)
    wan2_dsr = match_dsr_by_ip(wan2_ip, site_circuits)
    
    # Build network entry
    network_entry = {
        "network_name": network_name,
        "network_id": network_id,
        "device_serial": mx_device.get('serial', ''),
        "device_model": mx_device.get('model', ''),
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
    
    # Log results
    dsr_info = f"{len(site_circuits)} DSR circuits"
    if wan1_dsr:
        dsr_info += f", WAN1→{wan1_dsr['provider']} (IP match)"
    if wan2_dsr:
        dsr_info += f", WAN2→{wan2_dsr['provider']} (IP match)"
    
    print(f"   ✅ {network_name}: WAN1={wan1_arin}, WAN2={wan2_arin} ({dsr_info})")
    
    return network_entry

def main():
    """Main processing function"""
    print("🔄 Building Live Meraki JSON with Fresh ARIN Data")
    print("=" * 80)
    
    # Validate API key
    if not MERAKI_API_KEY:
        print("❌ MERAKI_API_KEY not found in environment")
        return
    
    # Get organization
    print("🔍 Getting Meraki organization...")
    org_id = get_organization_id()
    if not org_id:
        return
    
    print(f"✅ Found organization: {org_id}")
    
    # Get networks
    print("🔍 Getting networks...")
    networks = get_networks(org_id)
    print(f"✅ Found {len(networks)} networks")
    
    # Get all uplink statuses
    print("🔍 Getting uplink statuses for all appliances...")
    all_uplinks = get_all_uplink_statuses(org_id)
    print(f"✅ Found {len(all_uplinks)} appliances with uplink data")
    
    # Create lookup for uplinks by network ID
    uplink_lookup = {}
    for uplink_data in all_uplinks:
        network_id = uplink_data.get('networkId')
        if network_id:
            uplink_lookup[network_id] = uplink_data
    
    # Get DSR circuits
    print("🔍 Getting DSR circuits from database...")
    dsr_circuits = get_dsr_circuits()
    print(f"✅ Found DSR circuits for {len(dsr_circuits)} sites")
    
    # Process all networks
    print("\n🔄 Processing networks...")
    print("=" * 80)
    
    live_data = []
    processed = 0
    skipped = 0
    
    for network in networks:
        network_name = network['name']
        
        # Skip non-store networks
        if any(tag in network_name.lower() for tag in ['hub', 'lab', 'voice', 'test']):
            skipped += 1
            continue
        
        result = process_network(network, uplink_lookup, dsr_circuits)
        if result:
            live_data.append(result)
            processed += 1
        else:
            print(f"   ⚠️  {network_name}: No data available")
            skipped += 1
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(live_data, f, indent=2)
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print(f"   Total networks: {len(networks)}")
    print(f"   Networks processed: {processed}")
    print(f"   Networks skipped: {skipped}")
    print(f"   Output written to: {OUTPUT_FILE}")
    print(f"\n✅ Live Meraki JSON with fresh ARIN data generated successfully!")

if __name__ == "__main__":
    main()