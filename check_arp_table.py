#!/usr/bin/env python3
"""
Check ARP table for ALB 03 to identify WAN2 connected device manufacturer
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# ALB 03 details
device_serial = 'Q2KY-FBAF-VTHH'
network_name = 'ALB 03'
wan2_ip = '192.168.0.151'

print("ALB 03 ARP Table Check")
print("=" * 50)

# Try to get ARP table
url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/arpTable'

print("\nCreating ARP table request...")
response = requests.post(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 201:
    result = response.json()
    arp_id = result.get('arpTableId')
    print(f"✅ ARP table request created! ID: {arp_id}")
    
    # Poll for results
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/arpTable/{arp_id}'
    
    print("\nWaiting for results...")
    time.sleep(5)
    
    for i in range(20):
        response = requests.get(result_url, headers=headers)
        
        if response.status_code == 200:
            arp_result = response.json()
            status = arp_result.get('status')
            print(f"  Status: {status}")
            
            if status == 'complete':
                print("\n✅ ARP TABLE RETRIEVED!\n")
                
                # Look for entries related to WAN interfaces
                if 'entries' in arp_result:
                    entries = arp_result.get('entries', [])
                    print(f"Found {len(entries)} ARP entries")
                    
                    # Look for gateway entries (typically .1 addresses)
                    print("\nLooking for WAN2 gateway (192.168.0.x)...")
                    print("-" * 70)
                    
                    wan2_entries = []
                    for entry in entries:
                        ip = entry.get('ip', '')
                        if ip.startswith('192.168.0.'):
                            wan2_entries.append(entry)
                            
                    if wan2_entries:
                        print(f"\nFound {len(wan2_entries)} entries on WAN2 subnet:")
                        for entry in wan2_entries:
                            ip = entry.get('ip')
                            mac = entry.get('mac')
                            last_updated = entry.get('lastUpdatedAt')
                            vlan = entry.get('vlanId', 'N/A')
                            
                            print(f"\n  IP: {ip}")
                            print(f"  MAC: {mac}")
                            print(f"  VLAN: {vlan}")
                            print(f"  Last seen: {last_updated}")
                            
                            # Identify manufacturer from MAC
                            if mac:
                                oui = mac[:8].upper()
                                print(f"  OUI: {oui}")
                                
                                # Common cellular modem manufacturers
                                oui_manufacturers = {
                                    '00:30:AB': 'Sierra Wireless',
                                    '00:1B:C5': 'Cisco/Cradlepoint',
                                    '00:30:44': 'Cradlepoint',
                                    '00:08:2F': 'Cradlepoint',
                                    '5C:86:13': 'Beijing Venustech (Verizon)',
                                    '00:15:FF': 'Novatel/Inseego',
                                    '18:E8:29': 'Ubiquiti Networks',
                                    '60:B9:33': 'Verizon Network Device',
                                    '00:0C:E6': 'Verizon Wireless',
                                }
                                
                                manufacturer = None
                                for oui_prefix, mfg in oui_manufacturers.items():
                                    if mac.upper().startswith(oui_prefix):
                                        manufacturer = mfg
                                        break
                                
                                if manufacturer:
                                    print(f"  🎯 Manufacturer: {manufacturer}")
                                    
                                    # Infer carrier from manufacturer
                                    if 'Verizon' in manufacturer:
                                        print(f"  📶 Likely carrier: VERIZON WIRELESS")
                                    elif 'Cradlepoint' in manufacturer:
                                        print(f"  📶 Multi-carrier device (check device config)")
                                else:
                                    print(f"  ❓ Unknown manufacturer")
                                    print(f"     (Could be consumer router or cellular modem)")
                    else:
                        print("\nNo entries found on WAN2 subnet (192.168.0.x)")
                    
                    # Also show all entries
                    print("\n\nAll ARP entries:")
                    print("-" * 70)
                    for entry in entries[:20]:  # First 20 entries
                        print(f"{entry.get('ip'):20} {entry.get('mac'):20} VLAN: {entry.get('vlanId', 'N/A')}")
                        
                else:
                    print("No ARP entries in response")
                    print(f"Full response: {json.dumps(arp_result, indent=2)}")
                
                break
            elif status == 'failed':
                print("\n❌ ARP table request failed!")
                print(json.dumps(arp_result, indent=2))
                break
        else:
            print(f"  Error: {response.status_code}")
        
        time.sleep(3)
    else:
        print("\n⏱️  Timeout waiting for results")

else:
    print(f"❌ Error: {response.text}")
    
    # Try alternative - check if it needs to be for a switch
    if "must be a switch" in response.text:
        print("\n⚠️  ARP table might only be available for switches, not MX devices")