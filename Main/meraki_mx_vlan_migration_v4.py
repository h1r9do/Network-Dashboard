#!/usr/bin/env python3
"""
Meraki MX VLAN Migration Script v4
==================================

This script handles VLAN ID migrations for Meraki MX networks with two modes:
1. TEST MODE: Changes VLAN IDs AND IP addresses (for testing scenarios)
2. PRODUCTION MODE: Changes VLAN IDs but KEEPS the same IP addresses (for live sites)

New in v4:
- Configures syslog server before applying firewall rules
- Supports syslog configuration from source or default

Usage:
    python3 meraki_mx_vlan_migration_v4.py --network-id <network_id> --source-config <json_file> --firewall-template <json_file> --mode <test|production>

Example:
    python3 meraki_mx_vlan_migration_v4.py --network-id L_12345 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --mode test

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import time
import argparse
import ipaddress
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

# Standard VLAN mapping for Discount Tire stores
# This mapping is used for both TEST and PRODUCTION modes
STANDARD_VLAN_MAPPING = {
    1: 100,      # Data
    101: 200,    # Voice  
    300: 300,    # AP Mgmt -> Net Mgmt (name change only)
    301: 301,    # Scanner
    801: 400,    # IOT -> IoT
    201: 410,    # Ccard
    800: 800,    # Guest
    803: 803,    # IoT Wireless
    900: 900,    # Mgmt
    802: None    # IOT Network -> Remove (map to 400 on ports)
}

# IP changes for TEST MODE ONLY
# In PRODUCTION mode, these are ignored and original IPs are kept
TEST_MODE_IP_CHANGES = {
    400: {  # IoT (was 801)
        'old_subnet': '172.13.0.0/30',
        'new_subnet': '172.16.40.0/24',
        'new_appliance_ip': '172.16.40.1'
    },
    800: {  # Guest
        'old_subnet': '172.13.0.0/30', 
        'new_subnet': '172.16.80.0/24',
        'new_appliance_ip': '172.16.80.1'
    }
}

# Test network prefix for TEST MODE ONLY
TEST_NETWORK_PREFIX = '10.255.255'

# Default syslog server for Discount Tire
DEFAULT_SYSLOG_SERVER = {
    'host': '10.0.175.30',  # Adjust this to your actual syslog server
    'port': 514,
    'roles': ['Flows', 'URLs', 'Security events', 'Appliance event log']
}

class VLANMigrator:
    def __init__(self, network_id, mode='production'):
        """
        Initialize VLAN Migrator
        
        Args:
            network_id: Meraki network ID
            mode: 'test' or 'production' - determines IP handling
        """
        self.network_id = network_id
        self.mode = mode.lower()
        self.vlan_mapping = STANDARD_VLAN_MAPPING.copy()
        self.group_policy_mapping = {}  # Maps old policy IDs to new ones
        
        # Logging
        self.start_time = datetime.now()
        self.log_entries = []
        
        self.log(f"VLAN Migrator v4 initialized in {self.mode.upper()} mode")
        
    def log(self, message, level='INFO'):
        """Add log entry"""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
        self.log_entries.append(entry)
        print(entry)
        
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with error handling and rate limiting"""
        time.sleep(0.5)  # Basic rate limiting
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS, timeout=30)
                
            if response.status_code == 429:
                self.log("Rate limited, waiting 60 seconds...", "WARNING")
                time.sleep(60)
                return self.make_api_request(url, method, data)
                
            response.raise_for_status()
            
            if response.text:
                return response.json()
            return {}
            
        except Exception as e:
            self.log(f"Error {method} {url}: {e}", "ERROR")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}", "ERROR")
            return None
            
    def update_ip_for_test(self, ip_str):
        """
        Update IP address for test mode ONLY
        Production mode returns the original IP unchanged
        """
        if self.mode != 'test' or not ip_str or '/' not in ip_str:
            return ip_str
            
        try:
            ip_net = ipaddress.ip_network(ip_str, strict=False)
            if str(ip_net.network_address).startswith('10.'):
                # Replace first 3 octets with test prefix
                parts = str(ip_net.network_address).split('.')
                new_ip = f"{TEST_NETWORK_PREFIX}.{parts[3]}/{ip_net.prefixlen}"
                return new_ip
            return ip_str
        except:
            return ip_str
            
    def update_appliance_ip_for_test(self, ip_str):
        """
        Update appliance IP for test mode ONLY
        Production mode returns the original IP unchanged
        """
        if self.mode != 'test' or not ip_str:
            return ip_str
            
        try:
            if ip_str.startswith('10.'):
                parts = ip_str.split('.')
                return f"{TEST_NETWORK_PREFIX}.{parts[3]}"
            return ip_str
        except:
            return ip_str
            
    def get_current_vlans(self):
        """Get current VLAN configuration"""
        self.log("Fetching current VLAN configuration...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        return self.make_api_request(url) or []
        
    def delete_vlan(self, vlan_id):
        """Delete a VLAN"""
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{vlan_id}"
        return self.make_api_request(url, method='DELETE')
        
    def create_vlan(self, vlan_data):
        """Create a new VLAN"""
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        return self.make_api_request(url, method='POST', data=vlan_data)
        
    def update_vlan(self, vlan_id, vlan_data):
        """Update an existing VLAN"""
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{vlan_id}"
        return self.make_api_request(url, method='PUT', data=vlan_data)
        
    def create_group_policies(self, source_policies):
        """Create group policies before VLANs"""
        if not source_policies:
            self.log("No group policies to create")
            return
            
        self.log("\nCreating group policies...")
        
        for policy in source_policies:
            old_id = policy.get('groupPolicyId')
            self.log(f"  Creating group policy: {policy['name']} (ID: {old_id})")
            
            # Prepare policy data (remove ID, it's auto-assigned)
            policy_data = policy.copy()
            policy_data.pop('groupPolicyId', None)
            
            # Clean up any read-only fields
            policy_data.pop('networkId', None)
            
            # Create the policy
            url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
            result = self.make_api_request(url, method='POST', data=policy_data)
            
            if result:
                new_id = result.get('groupPolicyId')
                self.group_policy_mapping[old_id] = new_id
                self.log(f"    ✓ Created policy with new ID: {new_id}")
            else:
                self.log(f"    ✗ Failed to create policy", "ERROR")
                
            time.sleep(1)
            
    def clean_vlan_data(self, vlan_data):
        """Remove fields that can't be set via API"""
        fields_to_remove = [
            'networkId', 'mask', 'id',  # id removed here, added when creating
            'templateVlanType', 'cidr'
        ]
        
        for field in fields_to_remove:
            vlan_data.pop(field, None)
            
        return vlan_data
        
    def process_dhcp_settings(self, vlan_data):
        """
        Process and preserve DHCP settings
        Updates IPs based on mode but preserves all other DHCP configurations
        """
        # Update DHCP relay server IPs if present
        if vlan_data.get('dhcpRelayServerIps') and self.mode == 'test':
            updated_relay_ips = []
            for ip in vlan_data['dhcpRelayServerIps']:
                updated_ip = self.update_appliance_ip_for_test(ip)
                updated_relay_ips.append(updated_ip)
            vlan_data['dhcpRelayServerIps'] = updated_relay_ips
            self.log(f"    Updated DHCP relay servers: {updated_relay_ips}")
            
        # Process DHCP options if present
        if vlan_data.get('dhcpOptions'):
            self.log(f"    Preserving {len(vlan_data['dhcpOptions'])} DHCP options")
            
        # Process reserved IP ranges
        if vlan_data.get('reservedIpRanges') and self.mode == 'test':
            updated_ranges = []
            for range_data in vlan_data['reservedIpRanges']:
                if 'start' in range_data and 'end' in range_data:
                    # Update IP ranges for test mode
                    start = self.update_appliance_ip_for_test(range_data['start'])
                    end = self.update_appliance_ip_for_test(range_data['end'])
                    updated_ranges.append({
                        'start': start,
                        'end': end,
                        'comment': range_data.get('comment', '')
                    })
            vlan_data['reservedIpRanges'] = updated_ranges
            
        # Process fixed IP assignments
        if vlan_data.get('fixedIpAssignments') and self.mode == 'test':
            updated_assignments = {}
            for mac, assignment in vlan_data['fixedIpAssignments'].items():
                if isinstance(assignment, dict) and 'ip' in assignment:
                    updated_ip = self.update_appliance_ip_for_test(assignment['ip'])
                    updated_assignments[mac] = {
                        'ip': updated_ip,
                        'name': assignment.get('name', '')
                    }
                else:
                    updated_assignments[mac] = assignment
            vlan_data['fixedIpAssignments'] = updated_assignments
            
        # Log DHCP settings being preserved
        dhcp_settings = []
        if vlan_data.get('dhcpHandling'):
            dhcp_settings.append(f"handling={vlan_data['dhcpHandling']}")
        if vlan_data.get('dhcpLeaseTime'):
            dhcp_settings.append(f"lease={vlan_data['dhcpLeaseTime']}")
        if vlan_data.get('dnsNameservers'):
            dhcp_settings.append(f"DNS={vlan_data['dnsNameservers']}")
        if vlan_data.get('dhcpBootOptionsEnabled'):
            dhcp_settings.append("boot_options=enabled")
            
        if dhcp_settings:
            self.log(f"    DHCP settings: {', '.join(dhcp_settings)}")
            
        return vlan_data
        
    def process_vlan_data(self, vlan, new_vlan_id):
        """
        Process VLAN data for migration
        
        In TEST mode: Updates IPs according to TEST_MODE_IP_CHANGES
        In PRODUCTION mode: Keeps all IPs unchanged
        """
        vlan_data = vlan.copy()
        
        # Update VLAN name for specific cases
        if new_vlan_id == 300 and vlan['id'] == 300:
            vlan_data['name'] = 'Net Mgmt'
        elif new_vlan_id == 400:
            vlan_data['name'] = 'IoT'
            
        # Handle IP changes based on mode
        if self.mode == 'test':
            # TEST MODE: Apply IP changes
            if new_vlan_id in TEST_MODE_IP_CHANGES:
                ip_config = TEST_MODE_IP_CHANGES[new_vlan_id]
                vlan_data['subnet'] = ip_config['new_subnet']
                vlan_data['applianceIp'] = ip_config['new_appliance_ip']
                self.log(f"  TEST MODE: Changing IP from {vlan.get('subnet')} to {ip_config['new_subnet']}")
            else:
                # Update subnet for test network (10.x.x.x -> 10.255.255.x)
                if vlan_data.get('subnet'):
                    old_subnet = vlan_data['subnet']
                    vlan_data['subnet'] = self.update_ip_for_test(old_subnet)
                    if old_subnet != vlan_data['subnet']:
                        self.log(f"  TEST MODE: Changing IP from {old_subnet} to {vlan_data['subnet']}")
                        
                if vlan_data.get('applianceIp'):
                    vlan_data['applianceIp'] = self.update_appliance_ip_for_test(vlan_data['applianceIp'])
        else:
            # PRODUCTION MODE: Keep original IPs
            self.log(f"  PRODUCTION MODE: Keeping original IP {vlan.get('subnet')}")
            
        # Update group policy ID if mapped
        if 'groupPolicyId' in vlan_data:
            old_policy_id = vlan_data['groupPolicyId']
            new_policy_id = self.group_policy_mapping.get(old_policy_id)
            if new_policy_id:
                vlan_data['groupPolicyId'] = new_policy_id
                self.log(f"  Updated group policy ID: {old_policy_id} → {new_policy_id}")
            else:
                # Remove if no mapping exists
                vlan_data.pop('groupPolicyId', None)
                self.log(f"  Removed unmapped group policy ID: {old_policy_id}", "WARNING")
                
        # Process DHCP settings
        vlan_data = self.process_dhcp_settings(vlan_data)
        
        # Clean up data
        vlan_data = self.clean_vlan_data(vlan_data)
        
        return vlan_data
        
    def configure_syslog(self, syslog_config=None):
        """Configure syslog server for network"""
        self.log("\nStep 6: Configuring syslog server...")
        
        if not syslog_config:
            # Use default syslog configuration
            syslog_config = DEFAULT_SYSLOG_SERVER
            self.log(f"  Using default syslog server: {syslog_config['host']}:{syslog_config['port']}")
        
        # Update syslog IP for test mode
        if self.mode == 'test' and syslog_config.get('host', '').startswith('10.'):
            original_host = syslog_config['host']
            syslog_config['host'] = self.update_appliance_ip_for_test(original_host)
            self.log(f"  TEST MODE: Updated syslog server from {original_host} to {syslog_config['host']}")
        
        # Configure syslog via API
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        data = {
            'servers': [{
                'host': syslog_config['host'],
                'port': syslog_config.get('port', 514),
                'roles': syslog_config.get('roles', ['Flows', 'URLs', 'Security events', 'Appliance event log'])
            }]
        }
        
        result = self.make_api_request(url, method='PUT', data=data)
        if result:
            self.log(f"  ✓ Syslog server configured: {syslog_config['host']}:{syslog_config.get('port', 514)}")
            return True
        else:
            self.log("  ✗ Failed to configure syslog server", "ERROR")
            return False
        
    def translate_firewall_rule(self, rule):
        """
        Translate VLAN references in firewall rules
        Only needed when applying rules to sites with old VLAN numbering
        """
        new_rule = rule.copy()
        
        # Translate source CIDR
        if 'srcCidr' in rule and 'VLAN(' in rule['srcCidr']:
            src = rule['srcCidr']
            # Extract VLAN number
            vlan_num = int(src.split('VLAN(')[1].split(')')[0])
            # No translation needed since NEO 07 already uses new numbering
            # But this function is here for future use if needed
            new_rule['srcCidr'] = src
            
        # Translate destination CIDR
        if 'destCidr' in rule and 'VLAN(' in rule['destCidr']:
            dst = rule['destCidr']
            # Extract VLAN number
            vlan_num = int(dst.split('VLAN(')[1].split(')')[0])
            # No translation needed since NEO 07 already uses new numbering
            new_rule['destCidr'] = dst
            
        return new_rule
        
    def apply_firewall_rules(self, firewall_template):
        """Apply firewall rules from template"""
        self.log("\nStep 7: Applying firewall rules...")
        
        rules = firewall_template.get('rules', [])
        if not rules:
            self.log("No firewall rules to apply")
            return
            
        self.log(f"Applying {len(rules)} firewall rules from template...")
        
        # Translate rules if needed
        translated_rules = []
        for rule in rules:
            # Clean up rule (remove any read-only fields)
            clean_rule = rule.copy()
            clean_rule.pop('ruleNumber', None)  # Will be auto-assigned
            translated_rules.append(self.translate_firewall_rule(clean_rule))
            
        # Apply rules via API
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        data = {
            'rules': translated_rules
        }
        
        result = self.make_api_request(url, method='PUT', data=data)
        if result:
            self.log(f"  ✓ Successfully applied {len(translated_rules)} firewall rules")
        else:
            self.log(f"  ✗ Failed to apply firewall rules", "ERROR")
            
    def migrate_vlans(self, source_vlans, source_policies=None):
        """
        Perform VLAN migration
        
        Args:
            source_vlans: List of VLAN configurations to migrate
            source_policies: List of group policies to create first
        """
        self.log("Starting VLAN migration v4...")
        self.log(f"Mode: {self.mode.upper()}")
        
        # Step 0: Create group policies first
        if source_policies:
            self.create_group_policies(source_policies)
            
        # Step 1: Delete all existing VLANs except default
        self.log("\nStep 1: Cleaning up existing VLANs...")
        current_vlans = self.get_current_vlans()
        
        # Keep track of which VLAN is the last one (can't delete it)
        if len(current_vlans) == 1:
            last_vlan_id = current_vlans[0]['id']
        else:
            last_vlan_id = None
            
        for vlan in current_vlans:
            if vlan['id'] != 1 and vlan['id'] != last_vlan_id:
                self.log(f"  Deleting VLAN {vlan['id']} ({vlan['name']})")
                self.delete_vlan(vlan['id'])
                time.sleep(1)
                
        # Step 2: Process VLAN 1 -> 100 migration
        self.log("\nStep 2: Migrating default VLAN...")
        default_vlan = next((v for v in source_vlans if v['id'] == 1), None)
        
        if default_vlan:
            # Check if VLAN 1 exists
            current_vlans = self.get_current_vlans()
            vlan_1_exists = any(v['id'] == 1 for v in current_vlans)
            
            if vlan_1_exists:
                # Update VLAN 1 to temporary settings
                temp_data = {
                    'name': 'Temp',
                    'subnet': '192.168.1.0/24',
                    'applianceIp': '192.168.1.1'
                }
                self.log("  Moving VLAN 1 to temporary subnet...")
                self.update_vlan(1, temp_data)
                time.sleep(2)
            
            # Create VLAN 100 with migrated data
            vlan_100_data = self.process_vlan_data(default_vlan, 100)
            vlan_100_data['id'] = 100
            vlan_100_data['name'] = 'Data'
            
            self.log(f"  Creating VLAN 100 (Data) with subnet {vlan_100_data['subnet']}")
            result = self.create_vlan(vlan_100_data)
            if result:
                self.log("    ✓ Created VLAN 100")
            time.sleep(2)
            
            # Delete VLAN 1 if it exists
            if vlan_1_exists:
                self.log("  Deleting temporary VLAN 1...")
                self.delete_vlan(1)
                time.sleep(1)
                
        # Step 3: Create other VLANs
        self.log("\nStep 3: Creating remaining VLANs...")
        
        for vlan in source_vlans:
            old_vlan_id = vlan['id']
            
            # Skip default VLAN (already processed) and VLAN 802
            if old_vlan_id == 1 or old_vlan_id == 802:
                if old_vlan_id == 802:
                    self.log(f"  Skipping VLAN 802 (will be removed)")
                continue
                
            # Get new VLAN ID from mapping
            new_vlan_id = self.vlan_mapping.get(old_vlan_id)
            if new_vlan_id is None:
                self.log(f"  Skipping VLAN {old_vlan_id} - no mapping defined")
                continue
                
            self.log(f"\n  Creating VLAN {new_vlan_id} (was {old_vlan_id})")
            
            # Process VLAN data
            vlan_data = self.process_vlan_data(vlan, new_vlan_id)
            vlan_data['id'] = new_vlan_id
            
            # Create VLAN
            result = self.create_vlan(vlan_data)
            if result:
                self.log(f"    ✓ Created VLAN {new_vlan_id} - {vlan_data.get('name')} ({vlan_data.get('subnet')})")
            else:
                self.log(f"    ✗ Failed to create VLAN {new_vlan_id}", "ERROR")
                
            time.sleep(1)
            
        # Step 4: Clean up any remaining temporary VLANs
        if last_vlan_id and last_vlan_id not in [100, 200, 300, 301, 400, 410, 800, 803, 900]:
            self.log(f"\nStep 4: Cleaning up temporary VLAN {last_vlan_id}...")
            self.delete_vlan(last_vlan_id)
        else:
            self.log("\nStep 4: No temporary VLANs to clean up")
            
        # Step 5: Verify migration
        self.log("\nStep 5: Verifying migration...")
        final_vlans = self.get_current_vlans()
        
        self.log(f"\nMigration complete! Created {len(final_vlans)} VLANs:")
        for vlan in sorted(final_vlans, key=lambda x: x['id']):
            self.log(f"  VLAN {vlan['id']:3d}: {vlan['name']:15s} - {vlan.get('subnet', 'No subnet')}")
            
        return final_vlans
        
    def generate_report(self):
        """Generate migration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
VLAN Migration Report v4
========================
Network ID: {self.network_id}
Mode: {self.mode.upper()}
Duration: {duration}

Group Policy Mappings:
"""
        for old_id, new_id in self.group_policy_mapping.items():
            report += f"  Policy {old_id} → {new_id}\n"
            
        report += "\nMigration Log:\n"
        for entry in self.log_entries:
            report += entry + "\n"
            
        return report


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Meraki MX VLAN Migration Tool v4')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--source-config', required=True, help='Source configuration JSON file')
    parser.add_argument('--firewall-template', help='Firewall rules template JSON file')
    parser.add_argument('--syslog-server', help='Syslog server IP address')
    parser.add_argument('--syslog-port', type=int, default=514, help='Syslog server port (default: 514)')
    parser.add_argument('--mode', choices=['test', 'production'], default='production',
                       help='Migration mode: test (changes IPs) or production (keeps IPs)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Load source configuration
    try:
        with open(args.source_config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading source configuration: {e}")
        sys.exit(1)
        
    # Load firewall template if provided
    firewall_template = None
    if args.firewall_template:
        try:
            with open(args.firewall_template, 'r') as f:
                firewall_template = json.load(f)
                print(f"Loaded firewall template with {len(firewall_template.get('rules', []))} rules")
        except Exception as e:
            print(f"Error loading firewall template: {e}")
            sys.exit(1)
        
    # Extract VLANs and policies from config
    source_vlans = []
    source_policies = []
    
    if 'appliance' in config:
        if 'vlans' in config['appliance']:
            source_vlans = config['appliance']['vlans']
        if 'groupPolicies' in config['appliance']:
            source_policies = config['appliance']['groupPolicies']
    else:
        print("No appliance configuration found in source file")
        sys.exit(1)
        
    print(f"Found {len(source_vlans)} VLANs and {len(source_policies)} group policies in source configuration")
    
    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be made")
        print("\nVLANs that would be migrated:")
        for vlan in source_vlans:
            old_id = vlan['id']
            new_id = STANDARD_VLAN_MAPPING.get(old_id)
            if new_id:
                print(f"  VLAN {old_id} -> VLAN {new_id}")
        print("\nGroup policies that would be created:")
        for policy in source_policies:
            print(f"  {policy['name']} (ID: {policy['groupPolicyId']})")
        if firewall_template:
            print(f"\nFirewall rules that would be applied: {len(firewall_template.get('rules', []))}")
        if args.syslog_server:
            print(f"\nSyslog server: {args.syslog_server}:{args.syslog_port}")
        else:
            print(f"\nDefault syslog server: {DEFAULT_SYSLOG_SERVER['host']}:{DEFAULT_SYSLOG_SERVER['port']}")
        return
        
    # Create migrator and run migration
    migrator = VLANMigrator(args.network_id, args.mode)
    
    # Confirm before proceeding
    if not args.auto_confirm:
        print(f"\nWARNING: This will replace ALL VLANs in network {args.network_id}")
        print(f"Mode: {args.mode.upper()}")
        if args.mode == 'test':
            print("TEST MODE: IP addresses WILL be changed")
        else:
            print("PRODUCTION MODE: IP addresses will be preserved")
        if firewall_template:
            print(f"Firewall rules: {len(firewall_template.get('rules', []))} rules will be applied")
            
        response = input("\nProceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            return
            
    # Run migration
    try:
        # Migrate VLANs and group policies
        migrator.migrate_vlans(source_vlans, source_policies)
        
        # Configure syslog if firewall rules will be applied
        if firewall_template:
            syslog_config = None
            if args.syslog_server:
                syslog_config = {
                    'host': args.syslog_server,
                    'port': args.syslog_port,
                    'roles': ['Flows', 'URLs', 'Security events', 'Appliance event log']
                }
            
            # Configure syslog
            if migrator.configure_syslog(syslog_config):
                # Apply firewall rules only if syslog configuration succeeded
                migrator.apply_firewall_rules(firewall_template)
            else:
                print("\nWARNING: Skipping firewall rules due to syslog configuration failure")
        
        # Save report
        report = migrator.generate_report()
        report_file = f"vlan_migration_report_{args.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # If no arguments provided, show usage
    if len(sys.argv) == 1:
        print(__doc__)
        print("\nExample usage:")
        print("  python3 meraki_mx_vlan_migration_v4.py --network-id L_12345 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --mode test")
        print("  python3 meraki_mx_vlan_migration_v4.py --network-id L_12345 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --syslog-server 10.1.1.1 --mode production")
    else:
        main()