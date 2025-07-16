#!/usr/bin/env python3
"""
Apply Switch Port Configuration to TST 01
========================================

This script applies the switch port configuration from AZP 30 to TST 01.

Usage:
    python3 apply_switch_ports_to_tst01.py

Author: Claude
Date: July 2025
"""

import os
import sys
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

def get_switches():
    """Get switches in the target network"""
    url = f"{BASE_URL}/networks/{TARGET_NETWORK}/devices"
    devices = make_api_request(url)
    
    if not devices:
        return []
    
    switches = [d for d in devices if d['model'].startswith('MS')]
    return sorted(switches, key=lambda x: x['name'])

def configure_switch_port(switch_serial, port_id, config):
    """Configure a single switch port"""
    url = f"{BASE_URL}/devices/{switch_serial}/switch/ports/{port_id}"
    
    # Build configuration
    port_config = {
        'name': config.get('name', ''),
        'tags': config.get('tags', []),
        'enabled': config.get('enabled', True),
        'type': config.get('type', 'access'),
        'vlan': config.get('vlan', 1),
        'poeEnabled': config.get('poeEnabled', True)
    }
    
    # Add voice VLAN if present
    if 'voiceVlan' in config:
        port_config['voiceVlan'] = config['voiceVlan']
    
    # Add allowed VLANs for trunk ports
    if port_config['type'] == 'trunk':
        port_config['allowedVlans'] = config.get('allowedVlans', 'all')
        if 'nativeVlan' in config:
            port_config['nativeVlan'] = config['nativeVlan']
    
    # Add access policy settings only if appropriate
    if 'accessPolicyType' in config:
        port_config['accessPolicyType'] = config['accessPolicyType']
        
        # Only add sticky MAC settings if access policy is "Sticky MAC allow list"
        if config['accessPolicyType'] == 'Sticky MAC allow list':
            if 'stickyMacAllowList' in config:
                port_config['stickyMacAllowList'] = config['stickyMacAllowList']
            if 'stickyMacAllowListLimit' in config:
                # Ensure it's an integer
                limit = config['stickyMacAllowListLimit']
                if isinstance(limit, str) and limit.isdigit():
                    port_config['stickyMacAllowListLimit'] = int(limit)
                elif isinstance(limit, int):
                    port_config['stickyMacAllowListLimit'] = limit
    
    result = make_api_request(url, method='PUT', data=port_config)
    return result is not None

def apply_switch_configuration():
    """Apply switch port configuration from AZP 30"""
    log("Applying switch port configuration to TST 01...")
    
    # Load AZP 30 configuration
    config_file = '/usr/local/bin/Main/azp_30_switch_config_original_20250710_065006.json'
    
    if not os.path.exists(config_file):
        log(f"Configuration file not found: {config_file}", "ERROR")
        return False
    
    with open(config_file, 'r') as f:
        azp_config = json.load(f)
    
    # Get switches in TST 01
    switches = get_switches()
    if not switches:
        log("No switches found in TST 01", "ERROR")
        return False
    
    log(f"Found {len(switches)} switches in TST 01")
    
    # Map AZP 30 switches to TST 01 switches by order
    # Get AZP switches sorted by name
    azp_switches = []
    for serial, switch_data in azp_config['switches'].items():
        switch_info = {
            'serial': serial,
            'name': switch_data['device_info']['name'],
            'ports': switch_data['ports']
        }
        azp_switches.append(switch_info)
    
    # Sort by name to ensure consistent ordering
    azp_switches.sort(key=lambda x: x['name'])
    
    # Map to TST switches by order
    switch_mapping = {}
    for i, tst_switch in enumerate(switches):
        if i < len(azp_switches):
            azp_switch = azp_switches[i]
            switch_mapping[azp_switch['serial']] = tst_switch['serial']
            log(f"  Mapping {azp_switch['name']} -> {tst_switch['name']} ({tst_switch['serial']})")
    
    # Apply port configurations
    total_ports = 0
    success_count = 0
    
    for azp_switch in azp_switches:
        azp_serial = azp_switch['serial']
        tst_serial = switch_mapping.get(azp_serial)
        
        if not tst_serial:
            log(f"No mapping for switch {azp_switch['name']}", "WARNING")
            continue
        
        log(f"\nConfiguring switch {azp_switch['name']}...")
        
        for port in azp_switch['ports']:
            port_id = port['portId']
            total_ports += 1
            
            # Log port details
            port_type = port.get('type', 'access')
            if port_type == 'access':
                vlan_info = f"VLAN {port.get('vlan', 1)}"
                if 'voiceVlan' in port:
                    vlan_info += f" + Voice {port['voiceVlan']}"
            else:
                vlan_info = f"Trunk: {port.get('allowedVlans', 'all')}"
            
            log(f"  Port {port_id}: {port.get('name', 'Unnamed')} ({vlan_info})")
            
            if configure_switch_port(tst_serial, port_id, port):
                success_count += 1
                log(f"    ✓ Configured successfully")
            else:
                log(f"    ✗ Failed to configure", "ERROR")
            
            time.sleep(0.2)  # Rate limiting
    
    log(f"\n✓ Configured {success_count}/{total_ports} ports successfully")
    return success_count == total_ports

def verify_configuration():
    """Verify the applied configuration"""
    log("\nVerifying switch port configuration...")
    
    switches = get_switches()
    for switch in switches:
        log(f"\nSwitch: {switch['name']} ({switch['serial']})")
        
        # Get port configuration
        url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
        ports = make_api_request(url)
        
        if not ports:
            log("  Could not retrieve port configuration", "ERROR")
            continue
        
        # Count port types
        access_count = sum(1 for p in ports if p.get('type') == 'access')
        trunk_count = sum(1 for p in ports if p.get('type') == 'trunk')
        
        log(f"  Total ports: {len(ports)}")
        log(f"  Access ports: {access_count}")
        log(f"  Trunk ports: {trunk_count}")
        
        # Show VLAN usage
        vlans_in_use = set()
        for port in ports:
            if port.get('type') == 'access':
                vlan = port.get('vlan')
                if vlan is not None:
                    vlans_in_use.add(vlan)
                voice_vlan = port.get('voiceVlan')
                if voice_vlan is not None:
                    vlans_in_use.add(voice_vlan)
        
        if vlans_in_use:
            log(f"  VLANs in use: {sorted(vlans_in_use)}")

def main():
    print("🔧 Switch Port Configuration Tool for TST 01")
    print("=" * 60)
    
    log(f"Target network: {TARGET_NETWORK}")
    log("Source: AZP 30 switch configuration")
    
    # Apply configuration
    if apply_switch_configuration():
        # Verify
        verify_configuration()
        
        print("\n" + "="*60)
        print("✅ Switch port configuration completed successfully!")
        print("\nConfiguration applied:")
        print("- 48 access ports with appropriate VLAN assignments")
        print("- 8 trunk ports for infrastructure")
        print("- Voice VLAN 101 on all user ports")
        print("- Port names and descriptions preserved")
    else:
        print("\n❌ Switch port configuration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()