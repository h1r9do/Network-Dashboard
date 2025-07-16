#!/usr/bin/env python3
"""
Copy Production Configuration to Test Network
Copies complete configuration from NEO 07 to TST 01 for realistic testing
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

class ProductionConfigCopier:
    def __init__(self, source_network_id, source_name, target_network_id, target_name):
        self.source_network_id = source_network_id
        self.source_name = source_name
        self.target_network_id = target_network_id
        self.target_name = target_name
        self.log_entries = []
        
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
    
    def backup_target_network(self):
        """Create backup of target network before changes"""
        self.log(f"Creating backup of {self.target_name}...")
        
        backup_data = {}
        
        # Backup VLANs
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
        backup_data['vlans'] = self.make_api_request(url)
        
        # Backup firewall rules
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        backup_data['firewall_rules'] = self.make_api_request(url)
        
        # Backup MX ports
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/ports"
        backup_data['mx_ports'] = self.make_api_request(url)
        
        # Save backup
        backup_filename = f"production_copy_backup_{self.target_network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        self.log(f"Backup saved to {backup_filename}")
        return backup_filename
    
    def get_source_configuration(self):
        """Get complete configuration from source network"""
        self.log(f"Retrieving configuration from {self.source_name}...")
        
        config = {}
        
        # Get VLANs
        url = f"{BASE_URL}/networks/{self.source_network_id}/appliance/vlans"
        config['vlans'] = self.make_api_request(url)
        self.log(f"Retrieved {len(config['vlans'])} VLANs")
        
        # Get firewall rules
        url = f"{BASE_URL}/networks/{self.source_network_id}/appliance/firewall/l3FirewallRules"
        config['firewall_rules'] = self.make_api_request(url)
        self.log(f"Retrieved {len(config['firewall_rules']['rules'])} firewall rules")
        
        # Get group policies
        url = f"{BASE_URL}/networks/{self.source_network_id}/groupPolicies"
        config['group_policies'] = self.make_api_request(url)
        self.log(f"Retrieved {len(config['group_policies'])} group policies")
        
        # Get MX ports
        url = f"{BASE_URL}/networks/{self.source_network_id}/appliance/ports"
        config['mx_ports'] = self.make_api_request(url)
        self.log(f"Retrieved {len(config['mx_ports'])} MX ports")
        
        return config
    
    def clear_target_configuration(self):
        """Clear existing configuration from target network"""
        self.log(f"Clearing existing configuration from {self.target_name}...")
        
        # Clear firewall rules
        self.log("Clearing firewall rules...")
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': []})
        if result:
            self.log("  ✓ Firewall rules cleared")
        
        # Delete VLANs (except management)
        self.log("Clearing VLANs...")
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
        current_vlans = self.make_api_request(url)
        
        for vlan in current_vlans:
            if vlan['id'] != 900:  # Keep management VLAN
                self.log(f"  Deleting VLAN {vlan['id']}...")
                delete_url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans/{vlan['id']}"
                self.make_api_request(delete_url, method='DELETE')
                time.sleep(1)
    
    def apply_source_configuration(self, config):
        """Apply source configuration to target network"""
        self.log(f"Applying {self.source_name} configuration to {self.target_name}...")
        
        # Apply VLANs with test IP ranges
        self.log("Creating VLANs with test IP ranges...")
        for vlan in config['vlans']:
            if vlan['id'] != 900:  # Skip management VLAN
                vlan_data = vlan.copy()
                
                # Convert to test IP ranges
                if vlan_data.get('subnet'):
                    original_subnet = vlan_data['subnet']
                    # Convert 10.24.38.x to 10.255.255.x
                    test_subnet = original_subnet.replace('10.24.38.', '10.255.255.')
                    vlan_data['subnet'] = test_subnet
                    
                    # Update appliance IP
                    if vlan_data.get('applianceIp'):
                        test_ip = vlan_data['applianceIp'].replace('10.24.38.', '10.255.255.')
                        vlan_data['applianceIp'] = test_ip
                
                # Remove interfaceId if present
                if 'interfaceId' in vlan_data:
                    del vlan_data['interfaceId']
                
                self.log(f"  Creating VLAN {vlan_data['id']}: {vlan_data['name']}")
                url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
                result = self.make_api_request(url, method='POST', data=vlan_data)
                time.sleep(1)
        
        # Apply firewall rules
        self.log("Applying firewall rules...")
        firewall_rules = config['firewall_rules']['rules']
        
        # Update VLAN references in firewall rules for test environment
        updated_rules = []
        for rule in firewall_rules:
            new_rule = rule.copy()
            
            # Update source CIDR
            if 'srcCidr' in new_rule:
                src = new_rule['srcCidr']
                # Convert IP references to test range
                src = src.replace('10.24.38.', '10.255.255.')
                new_rule['srcCidr'] = src
            
            # Update destination CIDR
            if 'destCidr' in new_rule:
                dst = new_rule['destCidr']
                # Convert IP references to test range
                dst = dst.replace('10.24.38.', '10.255.255.')
                new_rule['destCidr'] = dst
            
            updated_rules.append(new_rule)
        
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': updated_rules})
        if result:
            self.log(f"  ✓ Applied {len(updated_rules)} firewall rules")
        
        # Apply MX port configurations
        self.log("Configuring MX ports...")
        for port in config['mx_ports']:
            port_num = port['number']
            
            # Prepare port configuration
            port_config = {
                'enabled': port.get('enabled', True),
                'type': port.get('type', 'access'),
                'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False)
            }
            
            # Add VLAN configuration
            if port.get('vlan'):
                port_config['vlan'] = port['vlan']
            
            # Add allowed VLANs for trunk ports
            if port.get('allowedVlans'):
                port_config['allowedVlans'] = port['allowedVlans']
            
            self.log(f"  Configuring MX port {port_num}")
            url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/ports/{port_num}"
            result = self.make_api_request(url, method='PUT', data=port_config)
            time.sleep(1)
    
    def run_copy(self):
        """Run the complete configuration copy process"""
        self.log("="*60)
        self.log(f"COPYING PRODUCTION CONFIGURATION")
        self.log(f"Source: {self.source_name} ({self.source_network_id})")
        self.log(f"Target: {self.target_name} ({self.target_network_id})")
        self.log("="*60)
        
        try:
            # Step 1: Backup target
            backup_file = self.backup_target_network()
            
            # Step 2: Get source configuration
            source_config = self.get_source_configuration()
            
            # Step 3: Clear target
            self.clear_target_configuration()
            
            # Step 4: Apply source configuration
            self.apply_source_configuration(source_config)
            
            self.log("="*60)
            self.log("✅ PRODUCTION CONFIGURATION COPY COMPLETED!")
            self.log("="*60)
            self.log(f"TST 01 now has NEO 07 configuration with test IP ranges")
            self.log(f"Backup saved: {backup_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Configuration copy failed: {e}", "ERROR")
            return False

def main():
    # NEO 07 (source) to TST 01 (target)
    neo07_id = "L_3790904986339115847"
    tst01_id = "L_3790904986339115852"
    
    print("🔧 Production Configuration Copy Tool")
    print("=" * 60)
    print("This will copy NEO 07 configuration to TST 01 for realistic testing")
    print("- VLANs with test IP ranges (10.255.255.x)")
    print("- All 55 firewall rules")
    print("- MX port configurations")
    print("=" * 60)
    
    confirm = input("Proceed with copying NEO 07 config to TST 01? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    copier = ProductionConfigCopier(neo07_id, "NEO 07", tst01_id, "TST 01")
    success = copier.run_copy()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()