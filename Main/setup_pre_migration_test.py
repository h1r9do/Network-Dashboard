#!/usr/bin/env python3
"""
Setup Pre-Migration Test Environment
Creates TST 01 with legacy VLAN configuration for testing migration
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

# Pre-migration VLAN configuration
PRE_MIGRATION_VLANS = [
    {
        'id': 1,
        'name': 'Data',
        'subnet': '10.255.255.0/25',
        'applianceIp': '10.255.255.1',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 101,
        'name': 'Voice',
        'subnet': '10.255.255.129/27',
        'applianceIp': '10.255.255.129',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 201,
        'name': 'Ccard',
        'subnet': '10.255.255.161/28',
        'applianceIp': '10.255.255.161',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 300,
        'name': 'AP Mgmt',
        'subnet': '10.255.255.177/28',
        'applianceIp': '10.255.255.177',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 301,
        'name': 'Scanner',
        'subnet': '10.255.255.193/28',
        'applianceIp': '10.255.255.193',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 800,
        'name': 'Guest',
        'subnet': '172.13.0.0/30',
        'applianceIp': '172.13.0.1',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 801,
        'name': 'IOT',
        'subnet': '172.13.0.4/30',
        'applianceIp': '172.13.0.5',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 803,
        'name': 'IoT Wireless',
        'subnet': '172.22.0.0/24',
        'applianceIp': '172.22.0.1',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    },
    {
        'id': 900,
        'name': 'Mgmt',
        'subnet': '10.255.255.252/30',
        'applianceIp': '10.255.255.253',
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': 'upstream_dns'
    }
]

class PreMigrationSetup:
    def __init__(self, network_id, network_name):
        self.network_id = network_id
        self.network_name = network_name
        
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
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
            return None
    
    def clear_network(self):
        """Clear existing VLANs (except management)"""
        self.log("Clearing existing VLANs...")
        
        # Clear firewall rules first
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': []})
        if result:
            self.log("  ✓ Firewall rules cleared")
        
        # Get current VLANs
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        current_vlans = self.make_api_request(url)
        
        if not current_vlans:
            self.log("Failed to get current VLANs", "ERROR")
            return False
        
        # Delete all VLANs except management (900)
        for vlan in current_vlans:
            if vlan['id'] != 900:
                self.log(f"  Deleting VLAN {vlan['id']}...")
                url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{vlan['id']}"
                self.make_api_request(url, method='DELETE')
                time.sleep(1)
        
        return True
    
    def create_pre_migration_vlans(self):
        """Create pre-migration VLAN configuration"""
        self.log("Creating pre-migration VLAN configuration...")
        
        for vlan_config in PRE_MIGRATION_VLANS:
            if vlan_config['id'] == 900:
                # Skip management VLAN - already exists
                continue
                
            self.log(f"  Creating VLAN {vlan_config['id']}: {vlan_config['name']}")
            
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
            result = self.make_api_request(url, method='POST', data=vlan_config)
            
            if not result:
                self.log(f"    ✗ Failed to create VLAN {vlan_config['id']}", "ERROR")
            else:
                self.log(f"    ✓ Created VLAN {vlan_config['id']}")
            
            time.sleep(1)
    
    def add_sample_firewall_rules(self):
        """Add some sample firewall rules with VLAN references for testing"""
        self.log("Adding sample firewall rules for testing...")
        
        sample_rules = [
            {
                "comment": "Allow Data VLAN to internet",
                "policy": "allow",
                "protocol": "tcp",
                "srcPort": "Any",
                "srcCidr": "VLAN(1).*",
                "destPort": "80,443",
                "destCidr": "Any",
                "syslogEnabled": False
            },
            {
                "comment": "Allow Voice VLAN to PBX",
                "policy": "allow",
                "protocol": "udp",
                "srcPort": "Any",
                "srcCidr": "VLAN(101).*",
                "destPort": "5060",
                "destCidr": "10.0.0.0/8",
                "syslogEnabled": False
            },
            {
                "comment": "Allow Scanner to Data VLAN",
                "policy": "allow",
                "protocol": "any",
                "srcPort": "Any",
                "srcCidr": "VLAN(301).*",
                "destPort": "Any",
                "destCidr": "VLAN(1).*",
                "syslogEnabled": False
            },
            {
                "comment": "Allow Credit Card to external services",
                "policy": "allow",
                "protocol": "tcp",
                "srcPort": "Any",
                "srcCidr": "VLAN(201).*",
                "destPort": "443",
                "destCidr": "Any",
                "syslogEnabled": True
            },
            {
                "comment": "IoT internet access",
                "policy": "allow",
                "protocol": "tcp",
                "srcPort": "Any",
                "srcCidr": "VLAN(801).*",
                "destPort": "80,443",
                "destCidr": "Any",
                "syslogEnabled": False
            },
            {
                "comment": "Default rule",
                "policy": "allow",
                "protocol": "Any",
                "srcPort": "Any",
                "srcCidr": "Any",
                "destPort": "Any",
                "destCidr": "Any",
                "syslogEnabled": False
            }
        ]
        
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': sample_rules})
        
        if result:
            self.log(f"  ✓ Added {len(sample_rules)} sample firewall rules")
        else:
            self.log("  ✗ Failed to add sample firewall rules", "ERROR")
    
    def run_setup(self):
        """Run complete pre-migration setup"""
        self.log("="*60)
        self.log(f"SETTING UP PRE-MIGRATION TEST ENVIRONMENT")
        self.log(f"Network: {self.network_name} ({self.network_id})")
        self.log("="*60)
        
        try:
            # Clear existing configuration
            if not self.clear_network():
                return False
            
            # Create pre-migration VLANs
            self.create_pre_migration_vlans()
            
            # Add sample firewall rules
            self.add_sample_firewall_rules()
            
            self.log("="*60)
            self.log("✅ PRE-MIGRATION SETUP COMPLETED!")
            self.log("="*60)
            self.log("TST 01 now has legacy VLAN configuration:")
            self.log("  - VLAN 1 (Data)")
            self.log("  - VLAN 101 (Voice)")
            self.log("  - VLAN 201 (Credit Card)")
            self.log("  - VLAN 301 (Scanner)")
            self.log("  - VLAN 801 (IoT)")
            self.log("  - VLAN 800 (Guest)")
            self.log("  - Sample firewall rules with VLAN references")
            self.log("")
            self.log("Ready for VLAN migration testing!")
            
            return True
            
        except Exception as e:
            self.log(f"Setup failed: {e}", "ERROR")
            return False

def main():
    tst01_id = "L_3790904986339115852"
    
    print("🔧 Pre-Migration Test Environment Setup")
    print("=" * 60)
    print("This will configure TST 01 with legacy VLAN numbers for testing:")
    print("  - VLAN 1, 101, 201, 301, 801, 800, 803, 900")
    print("  - Test IP ranges (10.255.255.x)")
    print("  - Sample firewall rules with VLAN references")
    print("=" * 60)
    
    if not os.getenv('SKIP_CONFIRMATION'):
        confirm = input("Proceed with pre-migration setup? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Setup cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    setup = PreMigrationSetup(tst01_id, "TST 01")
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()