#!/usr/bin/env python3
"""
Apply Complete MX Port Configuration
====================================

This script applies the complete MX port configuration from AZP 30 to TST 01.

Usage:
    python3 apply_mx_ports_complete.py

Author: Claude
Date: July 2025
"""

import os
import json
import requests
import time
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

# TST 01 network
TARGET_NETWORK = 'L_3790904986339115852'

# Port configurations from AZP 30
PORT_CONFIGS = [
    {
        "port": 3,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "1,101,201,300,301,900,803"
    },
    {
        "port": 4,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 300,
        "allowedVlans": "1,101,201,300,301,800,801,802,803"
    },
    {
        "port": 5,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "1,101,201,300,301,800,801,802,803"
    },
    {
        "port": 6,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "1,101,201,300,301,800,801,802,803"
    },
    {
        "port": 7,
        "enabled": False,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "all"
    },
    {
        "port": 8,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 802,
        "allowedVlans": "802"
    },
    {
        "port": 9,
        "enabled": True,
        "type": "access",
        "vlan": 801
    },
    {
        "port": 10,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "1,101,201,300,301"
    },
    {
        "port": 11,
        "enabled": False,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 1,
        "allowedVlans": "all"
    },
    {
        "port": 12,
        "enabled": True,
        "type": "trunk",
        "dropUntaggedTraffic": False,
        "nativeVlan": 800,
        "allowedVlans": "800,802"
    }
]

def log(message, level="INFO"):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        log(f"API Error: {e}", "ERROR")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            log(f"Response: {e.response.text}", "ERROR")
        return None

def configure_port(port_number, config):
    """Configure a single MX port"""
    url = f"{BASE_URL}/networks/{TARGET_NETWORK}/appliance/ports/{port_number}"
    
    # Build configuration data
    data = {}
    
    # If disabled, just disable it
    if not config.get('enabled', True):
        data = {'enabled': False}
    else:
        data['enabled'] = True
        data['type'] = config['type']
        
        if config['type'] == 'access':
            data['vlan'] = config['vlan']
        elif config['type'] == 'trunk':
            data['dropUntaggedTraffic'] = config.get('dropUntaggedTraffic', False)
            data['vlan'] = config.get('nativeVlan', 1)  # Native VLAN
            data['allowedVlans'] = config.get('allowedVlans', 'all')
    
    log(f"Configuring port {port_number}: {json.dumps(data)}")
    result = make_api_request(url, method='PUT', data=data)
    
    if result:
        log(f"  ✓ Port {port_number} configured successfully")
        return True
    else:
        log(f"  ✗ Failed to configure port {port_number}", "ERROR")
        return False

def main():
    print("🔧 Applying MX Port Configuration to TST 01")
    print("=" * 60)
    
    log(f"Target network: {TARGET_NETWORK}")
    log(f"Ports to configure: {len(PORT_CONFIGS)}")
    
    success_count = 0
    failed_ports = []
    
    for config in PORT_CONFIGS:
        port_num = config['port']
        log(f"\nProcessing port {port_num}...")
        
        if configure_port(port_num, config):
            success_count += 1
        else:
            failed_ports.append(port_num)
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    log(f"Configuration Summary:")
    log(f"  Successful: {success_count}/{len(PORT_CONFIGS)} ports")
    
    if failed_ports:
        log(f"  Failed ports: {failed_ports}", "WARNING")
    
    if success_count == len(PORT_CONFIGS):
        print("\n✅ MX port configuration completed successfully!")
        print("   All 10 ports configured with AZP 30 settings")
    else:
        print(f"\n⚠️  MX port configuration partially complete: {success_count}/{len(PORT_CONFIGS)} ports")

if __name__ == "__main__":
    main()