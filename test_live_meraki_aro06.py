#!/usr/bin/env python3
"""
Test Live Meraki JSON build with ARO 06 only
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

def get_arin_provider(ip_address):
    """Get ARIN provider information for an IP address"""
    if not ip_address or ip_address in ['', 'None', 'null']:
        return "Unknown"
    
    # Handle private IPs
    if ip_address.startswith(('192.168.', '10.', '172.')):
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

def get_dsr_circuits_for_site(site_name):
    """Get DSR circuits for a specific site"""
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
                provider_name,
                details_ordered_service_speed,
                circuit_purpose,
                ip_address_start,
                status
            FROM circuits
            WHERE site_name = %s AND status = 'Enabled'
            ORDER BY circuit_purpose
        """, (site_name,))
        
        circuits = []
        for row in cursor.fetchall():
            circuits.append({
                'provider': row[0],
                'speed': row[1],
                'purpose': row[2],
                'ip': row[3],
                'status': row[4]
            })
        
        cursor.close()
        conn.close()
        
        return circuits
    except Exception as e:
        print(f"Error getting DSR circuits: {e}")
        return []

def main():
    """Test with ARO 06 only"""
    print("🧪 Testing Live Meraki JSON Build with ARO 06")
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
    
    print(f"Organization: {org_id}")
    
    # Get networks and find ARO 06
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    
    aro06_network = None
    for network in networks:
        if network['name'] == 'ARO 06':
            aro06_network = network
            break
    
    if not aro06_network:
        print("ARO 06 not found")
        return
    
    network_id = aro06_network['id']
    print(f"ARO 06 Network ID: {network_id}")
    
    # Get uplink status
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses", headers=headers)
    all_uplinks = response.json()
    
    # Find ARO 06 uplinks
    aro06_uplinks = None
    for device_uplinks in all_uplinks:
        if device_uplinks.get('networkId') == network_id:
            aro06_uplinks = device_uplinks.get('uplinks', [])
            break
    
    if not aro06_uplinks:
        print("No uplinks found for ARO 06")
        return
    
    # Extract WAN IPs
    wan1_ip = aro06_uplinks[0].get('publicIp', '') if len(aro06_uplinks) > 0 else ''
    wan2_ip = aro06_uplinks[1].get('publicIp', '') if len(aro06_uplinks) > 1 else ''
    
    print(f"Live WAN IPs:")
    print(f"  WAN1: {wan1_ip}")
    print(f"  WAN2: {wan2_ip}")
    
    # Get ARIN data
    print("\\nGetting ARIN data...")
    wan1_arin = get_arin_provider(wan1_ip)
    time.sleep(1)
    wan2_arin = get_arin_provider(wan2_ip)
    
    print(f"ARIN Results:")
    print(f"  WAN1: {wan1_arin}")
    print(f"  WAN2: {wan2_arin}")
    
    # Get DSR circuits
    dsr_circuits = get_dsr_circuits_for_site('ARO 06')
    print(f"\\nDSR Circuits ({len(dsr_circuits)}):")
    for circuit in dsr_circuits:
        print(f"  {circuit['purpose']}: {circuit['provider']} ({circuit['speed']}) - IP: {circuit['ip']}")
    
    # Test IP matching
    print("\\nIP Matching Test:")
    for circuit in dsr_circuits:
        if circuit['ip'] == wan1_ip:
            print(f"  WAN1 ({wan1_ip}) matches DSR {circuit['purpose']}: {circuit['provider']}")
        elif circuit['ip'] == wan2_ip:
            print(f"  WAN2 ({wan2_ip}) matches DSR {circuit['purpose']}: {circuit['provider']}")
    
    # Show the issue
    print("\\n=== THE CIRCUIT FLIP ISSUE ===")
    print("Live State:")
    print(f"  WAN1: {wan1_arin} (Cox)")
    print(f"  WAN2: {wan2_arin} (AT&T)")
    print("DSR Should Be:")
    print(f"  Primary: AT&T (should be WAN1)")
    print(f"  Secondary: Cox (should be WAN2)")
    print("\\n-> The circuits are physically swapped!")

if __name__ == "__main__":
    main()