#!/usr/bin/env python3
"""
Debug script to check ARIN refresh functionality for CAL 24
"""

import requests
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

def debug_cal24_arin():
    """Debug ARIN refresh process for CAL 24"""
    
    site_name = "CAL 24"
    meraki_api_key = os.getenv('MERAKI_API_KEY')
    
    if not meraki_api_key:
        print("ERROR: Meraki API key not found!")
        return
    
    print(f"Debugging ARIN refresh for {site_name}")
    print("="*80)
    
    # Step 1: Get organization ID
    org_name = "DTC-Store-Inventory-All"
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key,
        'Content-Type': 'application/json'
    }
    
    print("Step 1: Getting organization ID...")
    try:
        orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
        orgs_response.raise_for_status()
        org_id = None
        for org in orgs_response.json():
            if org.get('name') == org_name:
                org_id = org['id']
                print(f"✓ Found organization: {org_name} (ID: {org_id})")
                break
        
        if not org_id:
            print("✗ Organization not found!")
            return
    except Exception as e:
        print(f"✗ Error getting organizations: {e}")
        return
    
    # Step 2: Get networks to find CAL 24
    print("\nStep 2: Finding CAL 24 network...")
    try:
        networks_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/networks"
        networks_response = requests.get(networks_url, headers=headers, timeout=30)
        networks_response.raise_for_status()
        
        cal24_network = None
        for network in networks_response.json():
            if network.get('name') == site_name:
                cal24_network = network
                print(f"✓ Found network: {network['name']} (ID: {network['id']})")
                break
        
        if not cal24_network:
            print(f"✗ Network '{site_name}' not found!")
            # Show similar networks
            print("\nSimilar networks found:")
            for network in networks_response.json():
                if 'CAL' in network.get('name', ''):
                    print(f"  - {network['name']}")
            return
            
    except Exception as e:
        print(f"✗ Error getting networks: {e}")
        return
    
    # Step 3: Get devices in the network
    print("\nStep 3: Getting devices in CAL 24 network...")
    try:
        devices_url = f"https://api.meraki.com/api/v1/networks/{cal24_network['id']}/devices"
        devices_response = requests.get(devices_url, headers=headers, timeout=30)
        devices_response.raise_for_status()
        
        mx_device = None
        for device in devices_response.json():
            if device.get('model', '').startswith('MX'):
                mx_device = device
                print(f"✓ Found MX device: {device['model']} (Serial: {device['serial']})")
                break
        
        if not mx_device:
            print("✗ No MX device found in network!")
            return
            
    except Exception as e:
        print(f"✗ Error getting devices: {e}")
        return
    
    # Step 4: Get uplink status
    print("\nStep 4: Getting uplink status...")
    try:
        uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
        response = requests.get(uplink_url, headers=headers, timeout=30)
        response.raise_for_status()
        all_uplinks = response.json()
        
        # Find uplinks for our device
        wan1_ip = None
        wan2_ip = None
        wan1_public_ip = None
        wan2_public_ip = None
        
        for device_status in all_uplinks:
            if device_status.get('serial') == mx_device['serial']:
                print(f"✓ Found uplink status for device {mx_device['serial']}")
                uplinks = device_status.get('uplinks', [])
                for uplink in uplinks:
                    print(f"\n  Uplink: {uplink.get('interface')}")
                    print(f"    Status: {uplink.get('status')}")
                    print(f"    Interface IP: {uplink.get('ip')}")
                    print(f"    Public IP: {uplink.get('publicIp')}")
                    print(f"    Gateway: {uplink.get('gateway')}")
                    print(f"    DNS: {uplink.get('dns')}")
                    
                    if uplink.get('interface') == 'wan1':
                        wan1_ip = uplink.get('ip')
                        wan1_public_ip = uplink.get('publicIp')
                    elif uplink.get('interface') == 'wan2':
                        wan2_ip = uplink.get('ip')
                        wan2_public_ip = uplink.get('publicIp')
                break
        
        if not wan1_ip and not wan2_ip and not wan1_public_ip and not wan2_public_ip:
            print("✗ No IP addresses found for device!")
            return
            
    except Exception as e:
        print(f"✗ Error getting uplink status: {e}")
        return
    
    # Step 5: Query ARIN for provider information
    print("\nStep 5: Querying ARIN for provider information...")
    
    def query_arin_rdap(ip, label):
        if not ip or ip == '0.0.0.0':
            print(f"  {label}: No IP address")
            return 'Unknown'
        
        print(f"\n  Querying ARIN for {label}: {ip}")
        try:
            arin_url = f"https://rdap.arin.net/registry/ip/{ip}"
            arin_response = requests.get(arin_url, timeout=10)
            print(f"    ARIN Response Status: {arin_response.status_code}")
            
            if arin_response.status_code == 200:
                arin_data = arin_response.json()
                
                # Show some debug info
                if 'name' in arin_data:
                    print(f"    Network Name: {arin_data['name']}")
                if 'handle' in arin_data:
                    print(f"    Handle: {arin_data['handle']}")
                
                # Extract organization name
                if 'entities' in arin_data:
                    for entity in arin_data['entities']:
                        if 'vcardArray' in entity:
                            for vcard in entity['vcardArray'][1]:
                                if vcard[0] == 'fn':
                                    provider = vcard[3]
                                    print(f"    ✓ Provider: {provider}")
                                    return provider
                
                print("    ✗ No provider name found in ARIN response")
                return 'Unknown'
            else:
                print(f"    ✗ ARIN query failed: {arin_response.status_code}")
                return 'Unknown'
        except Exception as e:
            print(f"    ✗ Error querying ARIN: {e}")
            return 'Unknown'
    
    # Query all IPs we found
    wan1_arin_provider = query_arin_rdap(wan1_public_ip or wan1_ip, "WAN1")
    wan2_arin_provider = query_arin_rdap(wan2_public_ip or wan2_ip, "WAN2")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print(f"Site: {site_name}")
    print(f"Device Serial: {mx_device['serial']}")
    print(f"WAN1 IP: {wan1_public_ip or wan1_ip or 'N/A'}")
    print(f"WAN1 ARIN Provider: {wan1_arin_provider}")
    print(f"WAN2 IP: {wan2_public_ip or wan2_ip or 'N/A'}")
    print(f"WAN2 ARIN Provider: {wan2_arin_provider}")
    print("="*80)

if __name__ == "__main__":
    debug_cal24_arin()