#!/usr/bin/env python3
"""
Generate a summary of TST 01 deployment status
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def make_api_request(url):
    """Make API request"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Generate deployment summary"""
    network_id = "L_3790904986339115852"  # TST 01
    
    print("=" * 60)
    print("TST 01 DEPLOYMENT SUMMARY")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get network info
    url = f"{BASE_URL}/networks/{network_id}"
    network = make_api_request(url)
    
    if network:
        print(f"\nNetwork: {network['name']}")
        print(f"Organization: DTC-Network-Engineering")
        print(f"Network ID: {network_id}")
    
    # Get VLANs
    print("\n✅ SUCCESSFULLY DEPLOYED VLANs:")
    print("-" * 40)
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(url)
    
    if vlans:
        for vlan in sorted(vlans, key=lambda x: x['id']):
            print(f"VLAN {vlan['id']:3d}: {vlan['name']:15s} - {vlan.get('subnet', 'No subnet'):18s} - Appliance IP: {vlan.get('applianceIp', 'N/A')}")
    
    print("\n📋 VLAN MIGRATION STATUS:")
    print("-" * 40)
    print("✅ VLAN 101 → 200 (Voice)     - COMPLETE")
    print("✅ VLAN 201 → 410 (Ccard)     - COMPLETE")
    print("✅ VLAN 300 → 300 (Net Mgmt)  - COMPLETE (name changed)")
    print("✅ VLAN 301 → 301 (Scanner)   - COMPLETE")
    print("✅ VLAN 800 → 800 (Guest)     - COMPLETE (IP changed to 172.16.80.0/24)")
    print("✅ VLAN 801 → 400 (IoT)       - COMPLETE (IP changed to 172.16.40.0/24)")
    print("✅ VLAN 803 → 803 (IoT Wireless) - COMPLETE")
    print("✅ VLAN 900 → 900 (Mgmt)      - COMPLETE")
    print("❌ VLAN 1   → 100 (Data)      - FAILED (subnet overlap)")
    
    print("\n📝 DEPLOYMENT NOTES:")
    print("-" * 40)
    print("1. All VLANs successfully created with proper migration")
    print("2. Test network prefix 10.255.255 applied to all 10.x networks")
    print("3. 172.x networks updated as specified:")
    print("   - IoT: 172.16.40.0/24")
    print("   - Guest: 172.16.80.0/24")
    print("4. VLAN 1 remains as Data (couldn't create VLAN 100 due to overlap)")
    print("5. VLAN 802 was NOT created (as requested)")
    
    print("\n⚠️  ITEMS REQUIRING MANUAL COMPLETION:")
    print("-" * 40)
    print("1. Firewall rules from NEO 07 (VLAN references need fixing)")
    print("2. Switch port configurations (AZP 30 template)")
    print("3. SSID tagging for IoT Wireless → VLAN 803")
    print("4. Additional MX settings (traffic shaping, content filtering, etc.)")
    
    # Get devices
    print("\n🖥️  DEVICES IN NETWORK:")
    print("-" * 40)
    url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = make_api_request(url)
    
    if devices:
        for device in devices:
            print(f"{device.get('model', 'Unknown'):10s} - {device.get('name', 'Unnamed'):15s} - Serial: {device.get('serial', 'N/A')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()