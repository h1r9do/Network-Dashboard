#!/usr/bin/env python3
"""
Apply MX Port Configuration
===========================

This script applies MX appliance port configuration from a source network
to a target network.

Usage:
    python3 apply_mx_ports_config.py --network-id <target> --port-config <ports.json>

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import time
import argparse
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

class MXPortConfigurator:
    def __init__(self, network_id):
        """Initialize the MX port configurator"""
        self.network_id = network_id
        self.log_entries = []
        self.start_time = datetime.now()
        
        self.log(f"MX Port Configurator initialized for {network_id}")
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)
    
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with error handling"""
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS, timeout=30)
            
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            self.log(f"API Error: {e}", "ERROR")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}", "ERROR")
            return None
    
    def get_current_ports(self):
        """Get current port configuration"""
        self.log("\nGetting current port configuration...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports"
        result = self.make_api_request(url)
        
        if result:
            self.log(f"  Found {len(result)} ports currently configured")
            return result
        return []
    
    def configure_port(self, port_number, port_config):
        """Configure a single MX port"""
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_number}"
        
        # If port is disabled, just disable it first
        if not port_config.get('enabled', True):
            disable_data = {'enabled': False}
            result = self.make_api_request(url, method='PUT', data=disable_data)
            return result is not None
        
        # Clean up the config
        config_data = {
            'enabled': port_config.get('enabled', True),
            'type': port_config.get('type', 'access'),
            'dropUntaggedTraffic': port_config.get('dropUntaggedTraffic', False)
        }
        
        # Add VLAN if access port
        if config_data['type'] == 'access':
            if 'vlan' in port_config:
                config_data['vlan'] = port_config['vlan']
            else:
                config_data['vlan'] = 1  # Default to VLAN 1
        
        # Add allowed VLANs and native VLAN if trunk port
        if config_data['type'] == 'trunk':
            # Set allowed VLANs
            if 'allowedVlans' in port_config:
                config_data['allowedVlans'] = port_config['allowedVlans']
            else:
                config_data['allowedVlans'] = 'all'
            
            # Set native VLAN - required for trunk ports
            if 'nativeVlan' in port_config:
                config_data['nativeVlan'] = port_config['nativeVlan']
            else:
                # Default native VLAN to 1
                config_data['nativeVlan'] = 1
        
        # Add access policy if present
        if 'accessPolicy' in port_config:
            config_data['accessPolicy'] = port_config['accessPolicy']
        
        result = self.make_api_request(url, method='PUT', data=config_data)
        return result is not None
    
    def apply_port_configuration(self, port_configs):
        """Apply port configuration from source"""
        self.log("\nApplying MX port configuration...")
        
        success_count = 0
        for port in port_configs:
            port_num = port['number']
            
            # Skip ports 1-2 (WAN ports)
            if port_num in [1, 2]:
                self.log(f"  Skipping port {port_num} (WAN port)")
                continue
            
            self.log(f"  Configuring port {port_num}...")
            
            # Build port details string
            details = []
            if port.get('enabled'):
                details.append("enabled")
            else:
                details.append("disabled")
            
            details.append(f"type={port.get('type', 'access')}")
            
            if port.get('type') == 'access':
                details.append(f"VLAN={port.get('vlan', 'none')}")
            elif port.get('type') == 'trunk':
                details.append(f"allowed={port.get('allowedVlans', 'all')}")
                if 'nativeVlan' in port:
                    details.append(f"native={port['nativeVlan']}")
            
            self.log(f"    Settings: {', '.join(details)}")
            
            if self.configure_port(port_num, port):
                success_count += 1
                self.log(f"    ✓ Port {port_num} configured successfully")
            else:
                self.log(f"    ✗ Failed to configure port {port_num}", "ERROR")
            
            time.sleep(0.5)  # Rate limiting
        
        self.log(f"\n✓ Configured {success_count}/{len(port_configs)} ports successfully")
        return success_count == len(port_configs)
    
    def verify_configuration(self, expected_configs):
        """Verify the applied configuration"""
        self.log("\nVerifying port configuration...")
        
        current_ports = self.get_current_ports()
        if not current_ports:
            self.log("  ✗ Could not retrieve current port configuration", "ERROR")
            return False
        
        # Create lookup by port number
        current_by_num = {p['number']: p for p in current_ports}
        
        mismatches = []
        for expected in expected_configs:
            port_num = expected['number']
            
            # Skip WAN ports
            if port_num in [1, 2]:
                continue
            
            current = current_by_num.get(port_num)
            if not current:
                mismatches.append(f"Port {port_num}: Not found")
                continue
            
            # Check key settings
            if current.get('enabled') != expected.get('enabled'):
                mismatches.append(f"Port {port_num}: enabled mismatch")
            
            if current.get('type') != expected.get('type'):
                mismatches.append(f"Port {port_num}: type mismatch")
            
            if expected.get('type') == 'access':
                if current.get('vlan') != expected.get('vlan'):
                    mismatches.append(f"Port {port_num}: VLAN mismatch")
            
        if mismatches:
            self.log("  ✗ Configuration mismatches found:", "WARNING")
            for mismatch in mismatches:
                self.log(f"    - {mismatch}", "WARNING")
            return False
        
        self.log("  ✓ All ports configured correctly")
        return True
    
    def generate_summary(self, port_configs):
        """Generate configuration summary"""
        self.log("\n" + "="*60)
        self.log("MX PORT CONFIGURATION SUMMARY")
        self.log("="*60)
        
        # Count by type
        enabled_count = sum(1 for p in port_configs if p.get('enabled', True))
        access_count = sum(1 for p in port_configs if p.get('type') == 'access')
        trunk_count = sum(1 for p in port_configs if p.get('type') == 'trunk')
        
        self.log(f"Total ports configured: {len(port_configs)}")
        self.log(f"Enabled ports: {enabled_count}")
        self.log(f"Access ports: {access_count}")
        self.log(f"Trunk ports: {trunk_count}")
        
        # Show port details
        self.log("\nPort Details:")
        for port in sorted(port_configs, key=lambda p: p['number']):
            port_num = port['number']
            status = "Enabled" if port.get('enabled', True) else "Disabled"
            port_type = port.get('type', 'access')
            
            if port_type == 'access':
                vlan = port.get('vlan', 'none')
                self.log(f"  Port {port_num}: {status}, Access, VLAN {vlan}")
            else:
                allowed = port.get('allowedVlans', 'all')
                native = port.get('nativeVlan', 'none')
                self.log(f"  Port {port_num}: {status}, Trunk, Allowed: {allowed}, Native: {native}")

def main():
    parser = argparse.ArgumentParser(description='Apply MX Port Configuration')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--port-config', required=True, help='Port configuration JSON file')
    
    args = parser.parse_args()
    
    print("🔧 MX Port Configuration Tool")
    print("=" * 60)
    
    # Load port configuration
    with open(args.port_config, 'r') as f:
        port_configs = json.load(f)
    
    print(f"📋 Configuration Summary:")
    print(f"  Source ports: {len(port_configs)}")
    print(f"  Target network: {args.network_id}")
    
    # Create configurator and apply
    configurator = MXPortConfigurator(args.network_id)
    
    # Apply configuration
    if configurator.apply_port_configuration(port_configs):
        # Verify configuration
        configurator.verify_configuration(port_configs)
        
        # Generate summary
        configurator.generate_summary(port_configs)
        
        print("\n✅ MX port configuration completed successfully!")
    else:
        print("\n❌ MX port configuration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()