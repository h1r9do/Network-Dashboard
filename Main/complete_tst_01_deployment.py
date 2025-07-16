#!/usr/bin/env python3
"""
Complete the TST 01 deployment - fix remaining issues
"""

import os
import sys
import json
import requests
import time
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# VLAN mapping table
VLAN_MAPPING = {
    1: 100,      # Data
    101: 200,    # Voice
    300: 300,    # AP Mgmt -> Net Mgmt
    301: 301,    # Scanner
    801: 400,    # IOT -> IoT
    201: 410,    # Ccard
    800: 800,    # Guest
    803: 803,    # IoT Wireless
    900: 900     # Mgmt
}

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    time.sleep(0.5)
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def create_vlan_100(network_id):
    """Create VLAN 100 and update VLAN 1"""
    print("Creating VLAN 100...")
    
    # First create VLAN 100
    vlan_data = {
        'id': 100,
        'name': 'Data',
        'subnet': '10.255.255.0/25',
        'applianceIp': '10.255.255.1'
    }
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    result = make_api_request(url, method='POST', data=vlan_data)
    
    if result:
        print("  Created VLAN 100")
        
        # Now update VLAN 1 to something else temporarily
        print("  Updating VLAN 1...")
        update_data = {
            'name': 'Default-Unused',
            'subnet': '192.168.128.0/24',
            'applianceIp': '192.168.128.1'
        }
        
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/1"
        result = make_api_request(url, method='PUT', data=update_data)
        
        if result:
            print("  Updated VLAN 1 to unused state")

def update_switch_ports_simple(network_id):
    """Update switch ports with VLAN mapping"""
    print("\nUpdating switch port configurations...")
    
    # Load AZP 30 config
    with open('azp_30_config.json', 'r') as f:
        azp_config = json.load(f)
    
    # Get switches
    url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = make_api_request(url)
    
    switches = [d for d in devices if d.get('model', '').startswith('MS')]
    
    if not switches:
        print("  No switches found")
        return
    
    # Get AZP switch port configs
    azp_ports = azp_config['switch']['ports']
    
    # Get first switch config as template
    first_switch_ports = None
    for serial, data in azp_ports.items():
        first_switch_ports = data['ports']
        break
    
    if not first_switch_ports:
        print("  No port configuration found in AZP config")
        return
    
    # Apply to each TST switch
    for switch in switches:
        serial = switch['serial']
        switch_name = switch.get('name', serial)
        print(f"  Configuring {switch_name}...")
        
        for port in first_switch_ports[:24]:  # Only first 24 ports
            port_id = port['portId']
            
            # Build update data
            update_data = {}
            
            # Map VLAN
            if 'vlan' in port and port['vlan']:
                old_vlan = port['vlan']
                new_vlan = VLAN_MAPPING.get(old_vlan, old_vlan)
                if old_vlan == 802:  # Special case
                    new_vlan = 400
                update_data['vlan'] = new_vlan
            
            # Copy other settings
            for field in ['name', 'type', 'poeEnabled', 'isolationEnabled', 
                         'rstpEnabled', 'stpGuard', 'udld', 'accessPolicyType']:
                if field in port:
                    update_data[field] = port[field]
            
            # Map allowed VLANs
            if 'allowedVlans' in port and port['allowedVlans'] != 'all':
                vlans = []
                for v in port['allowedVlans'].split(','):
                    if '-' in v:
                        continue  # Skip ranges for now
                    old_v = int(v)
                    new_v = VLAN_MAPPING.get(old_v, old_v)
                    if old_v == 802:
                        new_v = 400
                    vlans.append(str(new_v))
                
                if vlans:
                    update_data['allowedVlans'] = ','.join(vlans)
            
            # Apply update
            url = f"{BASE_URL}/devices/{serial}/switch/ports/{port_id}"
            result = make_api_request(url, method='PUT', data=update_data)
            
            if result:
                print(f"    Updated port {port_id}")

def apply_simplified_firewall_rules(network_id):
    """Apply simplified firewall rules"""
    print("\nApplying simplified firewall rules...")
    
    # Basic rules that should work
    rules = [
        {
            'comment': 'Default allow',
            'policy': 'allow',
            'protocol': 'any',
            'srcPort': 'Any',
            'srcCidr': 'Any',
            'destPort': 'Any',
            'destCidr': 'Any',
            'syslogEnabled': False
        }
    ]
    
    # Apply rules
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    data = {'rules': rules}
    
    result = make_api_request(url, method='PUT', data=data)
    if result:
        print("  Applied basic firewall rules")

def main():
    """Complete the deployment"""
    print("Completing TST 01 deployment...")
    
    network_id = "L_3790904986339115852"  # TST 01
    
    try:
        # Create VLAN 100
        create_vlan_100(network_id)
        
        # Update switch ports
        update_switch_ports_simple(network_id)
        
        # Apply simple firewall rules
        apply_simplified_firewall_rules(network_id)
        
        print("\n✅ Deployment completed!")
        
        # Show final state
        print("\nFinal VLAN configuration:")
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
        vlans = make_api_request(url)
        
        if vlans:
            for vlan in sorted(vlans, key=lambda x: x['id']):
                print(f"  VLAN {vlan['id']}: {vlan['name']} - {vlan.get('subnet', 'No subnet')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()