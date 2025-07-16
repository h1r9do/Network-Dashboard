#!/usr/bin/env python3
"""
Extract AZP 30 Switch Configuration without VLAN remapping
"""

import os
import sys
import json
import requests
from datetime import datetime
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

NETWORK_ID = "L_650207196201635912"  # AZP 30 network

def make_api_request(url, method='GET'):
    """Make API request with error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None

def get_network_devices():
    """Get all devices in the network"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/devices"
    return make_api_request(url) or []

def get_switch_ports(device_serial):
    """Get switch port configuration for a device"""
    url = f"{BASE_URL}/devices/{device_serial}/switch/ports"
    return make_api_request(url) or []

def extract_switch_configs():
    """Extract complete switch configurations from the network"""
    print("Extracting switch configurations from AZP 30...")
    
    devices = get_network_devices()
    switch_devices = [d for d in devices if d.get('model', '').startswith('MS')]
    
    print(f"Found {len(switch_devices)} switch devices")
    
    switch_configs = {}
    
    for device in switch_devices:
        serial = device['serial']
        model = device.get('model', 'Unknown')
        name = device.get('name', serial)
        
        print(f"Extracting config from {name} ({model}, {serial})")
        
        # Get port configurations
        ports = get_switch_ports(serial)
        if ports:
            # Process port data to include all relevant information
            processed_ports = []
            for port in ports:
                port_data = {
                    'portId': port.get('portId'),
                    'name': port.get('name', ''),
                    'enabled': port.get('enabled', True),
                    'type': port.get('type', 'access'),
                    'vlan': port.get('vlan'),
                    'voiceVlan': port.get('voiceVlan'),
                    'allowedVlans': port.get('allowedVlans'),
                    'poeEnabled': port.get('poeEnabled', True),
                    'isolationEnabled': port.get('isolationEnabled', False),
                    'rstpEnabled': port.get('rstpEnabled', True),
                    'stpGuard': port.get('stpGuard', 'disabled'),
                    'linkNegotiation': port.get('linkNegotiation', 'Auto negotiate'),
                    'accessPolicyType': port.get('accessPolicyType', 'Open'),
                    'stickyMacAllowList': port.get('stickyMacAllowList', []),
                    'stickyMacAllowListLimit': port.get('stickyMacAllowListLimit'),
                    'stormControlEnabled': port.get('stormControlEnabled', False),
                    'udld': port.get('udld', 'Alert only'),
                    'portScheduleId': port.get('portScheduleId'),
                    'tags': port.get('tags', [])
                }
                processed_ports.append(port_data)
            
            switch_configs[serial] = {
                'device_info': {
                    'serial': serial,
                    'name': name,
                    'model': model,
                    'mac': device.get('mac'),
                    'lanIp': device.get('lanIp'),
                    'firmware': device.get('firmware'),
                    'tags': device.get('tags', [])
                },
                'ports': processed_ports
            }
            print(f"  ✓ Extracted {len(ports)} port configurations")
        else:
            print(f"  ✗ Failed to extract ports for {serial}")
    
    return switch_configs

def save_config(switch_configs, filename):
    """Save switch configurations to JSON file"""
    config_data = {
        'extraction_time': datetime.now().isoformat(),
        'network_id': NETWORK_ID,
        'network_name': 'AZP 30',
        'switch_count': len(switch_configs),
        'total_ports': sum(len(config['ports']) for config in switch_configs.values()),
        'switches': switch_configs,
        'vlan_remapping_applied': False,
        'notes': 'Original configuration without VLAN remapping'
    }
    
    with open(filename, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\nConfiguration saved to {filename}")
    
    # Print summary
    print("\nConfiguration Summary:")
    print(f"- Network: AZP 30 ({NETWORK_ID})")
    print(f"- Switches: {len(switch_configs)}")
    print(f"- Total Ports: {config_data['total_ports']}")
    
    for serial, config in switch_configs.items():
        info = config['device_info']
        print(f"\n  {info['name']} ({info['model']}):")
        print(f"    - Serial: {serial}")
        print(f"    - Ports: {len(config['ports'])}")
        
        # Count port types
        access_ports = sum(1 for p in config['ports'] if p['type'] == 'access')
        trunk_ports = sum(1 for p in config['ports'] if p['type'] == 'trunk')
        print(f"    - Access Ports: {access_ports}")
        print(f"    - Trunk Ports: {trunk_ports}")
        
        # Count VLANs in use
        vlans = set()
        for port in config['ports']:
            if port.get('vlan'):
                vlans.add(port['vlan'])
            if port.get('voiceVlan'):
                vlans.add(port['voiceVlan'])
        print(f"    - VLANs in use: {sorted(vlans)}")

def main():
    """Main execution function"""
    print("🔧 AZP 30 Switch Configuration Extractor")
    print("=" * 50)
    
    # Extract configurations
    switch_configs = extract_switch_configs()
    
    if switch_configs:
        # Save original configuration
        output_file = f"azp_30_switch_config_original_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_config(switch_configs, output_file)
        print(f"\n✅ Extraction complete!")
    else:
        print("\n❌ No switch configurations extracted")

if __name__ == "__main__":
    main()