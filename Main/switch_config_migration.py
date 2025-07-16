#!/usr/bin/env python3
"""
Switch Configuration Migration Script
====================================

This script extracts switch configurations from source networks and deploys
them to target networks with VLAN ID remapping.

Features:
- Extract switch port configurations
- Apply VLAN ID remapping to port configurations
- Deploy configurations to target switches
- Handle switch stacks and individual switches
- Preserve port settings (PoE, STP, link negotiation, etc.)

Usage:
    python3 switch_config_migration.py --extract --network-id <source_network> --output <config_file>
    python3 switch_config_migration.py --deploy --network-id <target_network> --config <config_file> --vlan-mapping <mapping_file>

Author: Claude
Date: July 2025
Version: 1.0
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

# Standard VLAN mapping for remapping switch ports
STANDARD_VLAN_MAPPING = {
    1: 100,      # Data
    101: 200,    # Voice  
    300: 300,    # Net Mgmt
    301: 301,    # Scanner
    801: 400,    # IoT
    201: 410,    # Ccard
    800: 800,    # Guest
    803: 803,    # IoT Wireless
    900: 900,    # Mgmt
    802: 400     # IOT Network -> Map to IoT (400)
}

class SwitchConfigMigrator:
    def __init__(self, network_id):
        """Initialize the switch configuration migrator"""
        self.network_id = network_id
        self.log_entries = []
        self.start_time = datetime.now()
        
        self.log(f"Switch Config Migrator initialized for {network_id}")
    
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
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.log(f"API Error: {e}", "ERROR")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}", "ERROR")
            return None
    
    def get_network_devices(self):
        """Get all devices in the network"""
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        return self.make_api_request(url) or []
    
    def get_switch_ports(self, device_serial):
        """Get switch port configuration for a device"""
        url = f"{BASE_URL}/devices/{device_serial}/switch/ports"
        return self.make_api_request(url) or []
    
    def update_switch_port(self, device_serial, port_id, port_config):
        """Update switch port configuration"""
        url = f"{BASE_URL}/devices/{device_serial}/switch/ports/{port_id}"
        return self.make_api_request(url, method='PUT', data=port_config)
    
    def extract_switch_configs(self):
        """Extract complete switch configurations from the network"""
        self.log("Extracting switch configurations...")
        
        devices = self.get_network_devices()
        switch_devices = [d for d in devices if d.get('model', '').startswith('MS')]
        
        self.log(f"Found {len(switch_devices)} switch devices")
        
        switch_configs = {}
        
        for device in switch_devices:
            serial = device['serial']
            model = device.get('model', 'Unknown')
            name = device.get('name', serial)
            
            self.log(f"Extracting config from {name} ({model}, {serial})")
            
            # Get port configurations
            ports = self.get_switch_ports(serial)
            if ports:
                switch_configs[serial] = {
                    'device_info': {
                        'serial': serial,
                        'name': name,
                        'model': model,
                        'mac': device.get('mac'),
                        'lanIp': device.get('lanIp'),
                        'firmware': device.get('firmware')
                    },
                    'ports': ports
                }
                self.log(f"  ✓ Extracted {len(ports)} port configurations")
            else:
                self.log(f"  ✗ Failed to extract ports for {serial}", "ERROR")
        
        return switch_configs
    
    def apply_vlan_mapping(self, switch_configs, vlan_mapping=None):
        """Apply VLAN ID mapping to switch port configurations"""
        if vlan_mapping is None:
            vlan_mapping = STANDARD_VLAN_MAPPING
        
        self.log("Applying VLAN ID mapping to switch configurations...")
        
        updated_configs = {}
        total_ports_updated = 0
        
        for serial, config in switch_configs.items():
            device_name = config['device_info']['name']
            self.log(f"Processing {device_name} ({serial})")
            
            updated_ports = []
            ports_modified = 0
            
            for port in config['ports']:
                updated_port = port.copy()
                
                # Update access VLAN
                if 'vlan' in port and port['vlan'] in vlan_mapping:
                    old_vlan = port['vlan']
                    new_vlan = vlan_mapping[old_vlan]
                    updated_port['vlan'] = new_vlan
                    ports_modified += 1
                    self.log(f"  Port {port['portId']}: Access VLAN {old_vlan} → {new_vlan}")
                
                # Update voice VLAN
                if 'voiceVlan' in port and port['voiceVlan'] in vlan_mapping:
                    old_voice_vlan = port['voiceVlan']
                    new_voice_vlan = vlan_mapping[old_voice_vlan]
                    updated_port['voiceVlan'] = new_voice_vlan
                    ports_modified += 1
                    self.log(f"  Port {port['portId']}: Voice VLAN {old_voice_vlan} → {new_voice_vlan}")
                
                # Update trunk VLANs (if specific VLANs listed)
                if port.get('type') == 'trunk' and 'allowedVlans' in port:
                    if port['allowedVlans'] != 'all':
                        # Parse and remap specific VLAN list
                        try:
                            vlan_list = []
                            for vlan_range in port['allowedVlans'].split(','):
                                vlan_range = vlan_range.strip()
                                if '-' in vlan_range:
                                    # Handle ranges like "10-20"
                                    start, end = map(int, vlan_range.split('-'))
                                    for vlan_id in range(start, end + 1):
                                        if vlan_id in vlan_mapping:
                                            vlan_list.append(str(vlan_mapping[vlan_id]))
                                        else:
                                            vlan_list.append(str(vlan_id))
                                else:
                                    # Single VLAN
                                    vlan_id = int(vlan_range)
                                    if vlan_id in vlan_mapping:
                                        vlan_list.append(str(vlan_mapping[vlan_id]))
                                    else:
                                        vlan_list.append(str(vlan_id))
                            
                            new_allowed_vlans = ','.join(sorted(set(vlan_list), key=int))
                            if new_allowed_vlans != port['allowedVlans']:
                                updated_port['allowedVlans'] = new_allowed_vlans
                                ports_modified += 1
                                self.log(f"  Port {port['portId']}: Allowed VLANs {port['allowedVlans']} → {new_allowed_vlans}")
                        except ValueError as e:
                            self.log(f"  Port {port['portId']}: Could not parse VLAN list '{port['allowedVlans']}': {e}", "WARNING")
                
                updated_ports.append(updated_port)
            
            updated_configs[serial] = {
                'device_info': config['device_info'],
                'ports': updated_ports
            }
            
            self.log(f"  ✓ Updated {ports_modified} ports on {device_name}")
            total_ports_updated += ports_modified
        
        self.log(f"VLAN mapping complete: {total_ports_updated} total port updates")
        return updated_configs
    
    def deploy_switch_configs(self, switch_configs, target_devices=None):
        """Deploy switch configurations to target network"""
        self.log("Deploying switch configurations...")
        
        # Get target devices if not provided
        if target_devices is None:
            target_devices = self.get_network_devices()
        
        target_switches = {d['serial']: d for d in target_devices if d.get('model', '').startswith('MS')}
        
        self.log(f"Target network has {len(target_switches)} switch devices")
        
        deployment_results = {}
        
        for source_serial, config in switch_configs.items():
            source_name = config['device_info']['name']
            source_model = config['device_info']['model']
            
            # Find matching target device (by model and position or manual mapping)
            target_serial = None
            target_device = None
            
            # First try to find exact serial match
            if source_serial in target_switches:
                target_serial = source_serial
                target_device = target_switches[source_serial]
                self.log(f"Found exact serial match: {source_serial}")
            else:
                # Try to find device by model (for development/testing)
                matching_models = [d for d in target_switches.values() if d.get('model') == source_model]
                if matching_models:
                    target_device = matching_models[0]  # Take first match
                    target_serial = target_device['serial']
                    self.log(f"Matched by model: {source_name} ({source_model}) → {target_device.get('name', target_serial)}")
                else:
                    self.log(f"No matching target device found for {source_name} ({source_model})", "WARNING")
                    continue
            
            # Deploy port configurations
            self.log(f"Deploying {len(config['ports'])} ports to {target_device.get('name', target_serial)}")
            
            successful_ports = 0
            failed_ports = 0
            
            for port in config['ports']:
                port_id = port['portId']
                
                # Remove read-only fields
                port_config = {k: v for k, v in port.items() if k not in ['portId', 'schedule']}
                
                result = self.update_switch_port(target_serial, port_id, port_config)
                if result:
                    successful_ports += 1
                else:
                    failed_ports += 1
                    self.log(f"  ✗ Failed to update port {port_id}", "ERROR")
                
                # Rate limiting
                time.sleep(0.1)
            
            deployment_results[source_serial] = {
                'target_serial': target_serial,
                'target_name': target_device.get('name', target_serial),
                'successful_ports': successful_ports,
                'failed_ports': failed_ports,
                'total_ports': len(config['ports'])
            }
            
            self.log(f"  ✓ {successful_ports}/{len(config['ports'])} ports deployed successfully")
            if failed_ports > 0:
                self.log(f"  ⚠️  {failed_ports} ports failed to deploy", "WARNING")
        
        return deployment_results
    
    def save_config(self, switch_configs, filename):
        """Save switch configurations to JSON file"""
        config_data = {
            'extraction_time': datetime.now().isoformat(),
            'network_id': self.network_id,
            'switch_count': len(switch_configs),
            'total_ports': sum(len(config['ports']) for config in switch_configs.values()),
            'switches': switch_configs
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        self.log(f"Configuration saved to {filename}")
        return filename

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Switch Configuration Migration Tool')
    parser.add_argument('--network-id', required=True, help='Network ID')
    parser.add_argument('--extract', action='store_true', help='Extract switch configurations')
    parser.add_argument('--deploy', action='store_true', help='Deploy switch configurations')
    parser.add_argument('--config', help='Configuration file (for deploy mode)')
    parser.add_argument('--output', help='Output file (for extract mode)')
    parser.add_argument('--vlan-mapping', help='VLAN mapping JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if not args.extract and not args.deploy:
        print("❌ Must specify either --extract or --deploy")
        return
    
    print("🔧 Switch Configuration Migration Tool")
    print("=" * 50)
    
    migrator = SwitchConfigMigrator(args.network_id)
    
    if args.extract:
        # Extract mode
        print(f"📥 Extracting switch configurations from network {args.network_id}")
        
        switch_configs = migrator.extract_switch_configs()
        
        if switch_configs:
            # Apply VLAN mapping
            if args.vlan_mapping:
                with open(args.vlan_mapping, 'r') as f:
                    vlan_mapping = json.load(f)
                switch_configs = migrator.apply_vlan_mapping(switch_configs, vlan_mapping)
            else:
                switch_configs = migrator.apply_vlan_mapping(switch_configs)
            
            # Save configuration
            output_file = args.output or f"switch_config_{args.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            migrator.save_config(switch_configs, output_file)
            
            print(f"✅ Extraction complete: {len(switch_configs)} switches saved to {output_file}")
        else:
            print("❌ No switch configurations extracted")
    
    elif args.deploy:
        # Deploy mode
        if not args.config:
            print("❌ Must specify --config file for deploy mode")
            return
        
        print(f"📤 Deploying switch configurations to network {args.network_id}")
        
        # Load configuration
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            switch_configs = config_data['switches']
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return
        
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            print(f"Would deploy configurations for {len(switch_configs)} switches:")
            for serial, config in switch_configs.items():
                device_info = config['device_info']
                print(f"  {device_info['name']} ({device_info['model']}, {serial}): {len(config['ports'])} ports")
        else:
            # Deploy configurations
            results = migrator.deploy_switch_configs(switch_configs)
            
            print(f"\n📊 Deployment Results:")
            total_success = 0
            total_failed = 0
            
            for source_serial, result in results.items():
                print(f"  {result['target_name']}: {result['successful_ports']}/{result['total_ports']} ports deployed")
                total_success += result['successful_ports']
                total_failed += result['failed_ports']
            
            if total_failed == 0:
                print(f"\n🎉 ✅ DEPLOYMENT COMPLETED SUCCESSFULLY!")
                print(f"All {total_success} ports deployed successfully")
            else:
                print(f"\n⚠️  🔶 DEPLOYMENT COMPLETED WITH WARNINGS")
                print(f"Success: {total_success} ports, Failed: {total_failed} ports")

if __name__ == "__main__":
    main()