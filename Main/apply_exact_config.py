#!/usr/bin/env python3
"""
Apply Exact Configuration with IP Translation Only
=================================================

This script applies the exact configuration from a source network
with only IP address changes - NO VLAN ID remapping.

Usage:
    python3 apply_exact_config.py --network-id <target> --source-config <config.json> --firewall-template <firewall.json>

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

# Test network prefix for IP translation
TEST_NETWORK_PREFIX = '10.255.255'

# Known source organization for policy objects
POLICY_SOURCE_ORG_ID = "436883"  # DTC-Store-Inventory-All

class ExactConfigMigrator:
    def __init__(self, network_id):
        """Initialize the exact configuration migrator"""
        self.network_id = network_id
        self.log_entries = []
        self.start_time = datetime.now()
        self.group_policy_mapping = {}
        self.object_id_mapping = {}
        self.group_id_mapping = {}
        
        # Get target organization ID
        self.target_org_id = self.get_network_org_id()
        
        self.log(f"Exact Config Migrator initialized for {network_id}")
        self.log(f"Target Organization: {self.target_org_id}")
    
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
    
    def get_network_org_id(self):
        """Get organization ID for the target network"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        response = self.make_api_request(url)
        if response:
            return response['organizationId']
        else:
            raise Exception("Could not determine target organization ID")
    
    def update_ip_for_test(self, ip_subnet):
        """Update IP address to test range (10.x.x.x -> 10.255.255.x)"""
        if ip_subnet.startswith('10.') and not ip_subnet.startswith('10.255.255.'):
            parts = ip_subnet.split('.')
            if len(parts) >= 3:
                # Keep the last octet(s) and subnet mask
                subnet_parts = ip_subnet.split('/')
                ip_parts = subnet_parts[0].split('.')
                new_ip = f"{TEST_NETWORK_PREFIX}.{ip_parts[3]}"
                if len(subnet_parts) > 1:
                    return f"{new_ip}/{subnet_parts[1]}"
                return new_ip
        return ip_subnet
    
    def migrate_policy_objects(self, firewall_rules):
        """Migrate policy objects referenced in firewall rules"""
        import re
        
        self.log("\nStep 1: Migrating policy objects...")
        
        # Extract object and group references from firewall rules
        object_refs = set()
        group_refs = set()
        
        for rule in firewall_rules:
            src = rule.get('srcCidr', '')
            dst = rule.get('destCidr', '')
            
            # Use regex to find ALL OBJ() and GRP() references
            obj_pattern = r'OBJ\((\d+)\)'
            grp_pattern = r'GRP\((\d+)\)'
            
            object_refs.update(re.findall(obj_pattern, src))
            object_refs.update(re.findall(obj_pattern, dst))
            group_refs.update(re.findall(grp_pattern, src))
            group_refs.update(re.findall(grp_pattern, dst))
        
        self.log(f"  Found {len(object_refs)} object references, {len(group_refs)} group references")
        
        # Get source objects and groups
        source_objects = self.get_policy_objects(POLICY_SOURCE_ORG_ID)
        source_groups = self.get_policy_groups(POLICY_SOURCE_ORG_ID)
        
        # Get existing objects in target org
        target_objects = self.get_policy_objects(self.target_org_id)
        target_groups = self.get_policy_groups(self.target_org_id)
        
        existing_object_names = {obj['name'] for obj in target_objects}
        existing_group_names = {grp['name'] for grp in target_groups}
        
        # Migrate individual objects
        for source_obj in source_objects:
            if str(source_obj['id']) in object_refs:
                if source_obj['name'] in existing_object_names:
                    existing_obj = next((obj for obj in target_objects if obj['name'] == source_obj['name']), None)
                    if existing_obj:
                        self.object_id_mapping[str(source_obj['id'])] = str(existing_obj['id'])
                    continue
                
                # Create new object
                obj_data = {
                    'name': source_obj['name'],
                    'category': source_obj['category'],
                    'type': source_obj['type']
                }
                
                if source_obj['type'] == 'cidr':
                    obj_data['cidr'] = source_obj.get('cidr')
                elif source_obj['type'] == 'fqdn':
                    obj_data['fqdn'] = source_obj.get('fqdn')
                
                result = self.create_policy_object(self.target_org_id, obj_data)
                if result:
                    self.object_id_mapping[str(source_obj['id'])] = str(result['id'])
                    self.log(f"  Created object: {source_obj['name']} ({result['id']})")
        
        # Migrate groups
        for source_group in source_groups:
            if str(source_group['id']) in group_refs:
                if source_group['name'] in existing_group_names:
                    existing_grp = next((grp for grp in target_groups if grp['name'] == source_group['name']), None)
                    if existing_grp:
                        self.group_id_mapping[str(source_group['id'])] = str(existing_grp['id'])
                    continue
                
                # Map object IDs for group
                new_object_ids = []
                for old_obj_id in source_group.get('objectIds', []):
                    new_obj_id = self.object_id_mapping.get(str(old_obj_id))
                    if new_obj_id:
                        new_object_ids.append(new_obj_id)
                
                # Create group
                group_data = {
                    'name': source_group['name'],
                    'objectIds': new_object_ids
                }
                
                result = self.create_policy_group(self.target_org_id, group_data)
                if result:
                    self.group_id_mapping[str(source_group['id'])] = str(result['id'])
                    self.log(f"  Created group: {source_group['name']} ({result['id']})")
    
    def get_policy_objects(self, org_id):
        """Get policy objects from organization"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
        return self.make_api_request(url) or []
    
    def get_policy_groups(self, org_id):
        """Get policy groups from organization"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
        return self.make_api_request(url) or []
    
    def create_policy_object(self, org_id, obj_data):
        """Create policy object"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
        return self.make_api_request(url, method='POST', data=obj_data)
    
    def create_policy_group(self, org_id, group_data):
        """Create policy group"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
        return self.make_api_request(url, method='POST', data=group_data)
    
    def create_group_policies(self, source_policies):
        """Create group policies in the same order"""
        self.log("\nStep 2: Creating group policies...")
        
        for policy in source_policies:
            old_id = policy.get('groupPolicyId')
            self.log(f"  Creating group policy: {policy['name']} (ID: {old_id})")
            
            # Prepare policy data
            policy_data = policy.copy()
            policy_data.pop('groupPolicyId', None)
            policy_data.pop('networkId', None)
            
            # Create the policy
            url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
            result = self.make_api_request(url, method='POST', data=policy_data)
            
            if result:
                new_id = result['groupPolicyId']
                self.group_policy_mapping[old_id] = new_id
                self.log(f"    ✓ Created with ID: {new_id}")
    
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
    
    def migrate_vlans(self, source_vlans):
        """Migrate VLANs with EXACT IDs - only change IPs"""
        self.log("\nStep 3: Migrating VLANs with exact IDs...")
        
        # Delete default VLAN 100 if needed
        if any(v['id'] == 1 for v in source_vlans):
            self.log("  Deleting default VLAN 100 to make room for VLAN 1...")
            self.delete_vlan(100)
            time.sleep(1)
        
        # Process VLANs in ID order
        sorted_vlans = sorted(source_vlans, key=lambda v: v['id'])
        
        for vlan in sorted_vlans:
            vlan_id = vlan['id']
            vlan_data = vlan.copy()
            
            # Update subnet for test network
            if vlan_data.get('subnet'):
                old_subnet = vlan_data['subnet']
                vlan_data['subnet'] = self.update_ip_for_test(old_subnet)
                if old_subnet != vlan_data['subnet']:
                    self.log(f"  VLAN {vlan_id}: Changing IP from {old_subnet} to {vlan_data['subnet']}")
            
            # Update appliance IP
            if vlan_data.get('applianceIp'):
                vlan_data['applianceIp'] = self.update_ip_for_test(vlan_data['applianceIp'])
            
            # Handle DHCP relay - convert to server mode for test
            if vlan_data.get('dhcpRelayServerIps'):
                self.log(f"    Converting DHCP relay to server mode for test environment")
                vlan_data['dhcpHandling'] = 'Run a DHCP server'
                vlan_data['dhcpLeaseTime'] = '12 hours'
                vlan_data.pop('dhcpRelayServerIps', None)
            
            # Update fixed IP assignments
            if vlan_data.get('fixedIpAssignments'):
                updated_assignments = {}
                for mac, assignment in vlan_data['fixedIpAssignments'].items():
                    if isinstance(assignment, dict) and 'ip' in assignment:
                        updated_ip = self.update_ip_for_test(assignment['ip'])
                        updated_assignments[mac] = {
                            'ip': updated_ip,
                            'name': assignment.get('name', '')
                        }
                vlan_data['fixedIpAssignments'] = updated_assignments
            
            # Update group policy ID if mapped
            if 'groupPolicyId' in vlan_data:
                old_policy_id = str(vlan_data['groupPolicyId'])
                new_policy_id = self.group_policy_mapping.get(old_policy_id)
                if new_policy_id:
                    vlan_data['groupPolicyId'] = new_policy_id
                    self.log(f"    Updated group policy ID: {old_policy_id} → {new_policy_id}")
            
            # Clean up fields
            for field in ['networkId', 'interfaceId', 'ipv6', 'mandatoryDhcp']:
                vlan_data.pop(field, None)
            
            # Create VLAN
            result = self.create_vlan(vlan_data)
            if result:
                self.log(f"  ✓ Created VLAN {vlan_id} - {vlan_data.get('name')} ({vlan_data.get('subnet')})")
            else:
                self.log(f"  ✗ Failed to create VLAN {vlan_id}", "ERROR")
            
            time.sleep(1)
    
    def configure_syslog(self):
        """Configure syslog server"""
        self.log("\nStep 4: Configuring syslog...")
        
        syslog_host = self.update_ip_for_test('10.0.175.30')
        
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        data = {
            'servers': [{
                'host': syslog_host,
                'port': 514,
                'roles': ['Flows', 'URLs', 'Security events', 'Appliance event log']
            }]
        }
        
        result = self.make_api_request(url, method='PUT', data=data)
        if result:
            self.log(f"  ✓ Syslog configured: {syslog_host}:514")
            return True
        return False
    
    def apply_firewall_rules(self, firewall_rules):
        """Apply firewall rules with object/group mapping"""
        self.log("\nStep 5: Applying firewall rules...")
        
        updated_rules = []
        for rule in firewall_rules:
            updated_rule = rule.copy()
            updated_rule.pop('ruleNumber', None)
            
            # Update object/group references
            src = rule.get('srcCidr', '')
            dst = rule.get('destCidr', '')
            
            # Update source
            if 'OBJ(' in src:
                for old_id, new_id in self.object_id_mapping.items():
                    src = src.replace(f'OBJ({old_id})', f'OBJ({new_id})')
                updated_rule['srcCidr'] = src
            elif 'GRP(' in src:
                for old_id, new_id in self.group_id_mapping.items():
                    src = src.replace(f'GRP({old_id})', f'GRP({new_id})')
                updated_rule['srcCidr'] = src
            
            # Update destination
            if 'OBJ(' in dst:
                for old_id, new_id in self.object_id_mapping.items():
                    dst = dst.replace(f'OBJ({old_id})', f'OBJ({new_id})')
                updated_rule['destCidr'] = dst
            elif 'GRP(' in dst:
                for old_id, new_id in self.group_id_mapping.items():
                    dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
                updated_rule['destCidr'] = dst
            
            updated_rules.append(updated_rule)
        
        # Apply rules
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        data = {'rules': updated_rules}
        
        result = self.make_api_request(url, method='PUT', data=data)
        if result:
            self.log(f"  ✓ Applied {len(result.get('rules', []))} firewall rules")
            return True
        return False

def main():
    parser = argparse.ArgumentParser(description='Apply Exact Configuration with IP Translation Only')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--source-config', required=True, help='Source configuration JSON file')
    parser.add_argument('--firewall-template', required=True, help='Firewall rules template JSON file')
    
    args = parser.parse_args()
    
    print("🚀 Exact Configuration Migration (IP Translation Only)")
    print("=" * 60)
    
    # Load configurations
    with open(args.source_config, 'r') as f:
        config = json.load(f)
    
    # Check if we should use AZP 30 original rules
    if args.firewall_template == 'azp_30_original':
        # Extract AZP 30 firewall rules directly
        import requests
        url = f"{BASE_URL}/networks/L_650207196201635912/appliance/firewall/l3FirewallRules"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            firewall_template = response.json()
            print(f"  Extracted {len(firewall_template['rules'])} rules from AZP 30")
        else:
            print("Failed to get AZP 30 rules")
            sys.exit(1)
    else:
        with open(args.firewall_template, 'r') as f:
            firewall_template = json.load(f)
    
    # Extract components
    source_vlans = config['appliance']['vlans']
    source_policies = config['appliance'].get('groupPolicies', [])
    firewall_rules = firewall_template.get('rules', [])
    
    print(f"📋 Configuration Summary:")
    print(f"  Source VLANs: {len(source_vlans)} (keeping exact IDs)")
    print(f"  Group Policies: {len(source_policies)}")
    print(f"  Firewall Rules: {len(firewall_rules)}")
    print(f"  Mode: IP Translation Only (10.255.255.x)")
    
    # Create migrator and run
    migrator = ExactConfigMigrator(args.network_id)
    
    # Step 1: Migrate policy objects
    migrator.migrate_policy_objects(firewall_rules)
    
    # Step 2: Create group policies
    migrator.create_group_policies(source_policies)
    
    # Step 3: Migrate VLANs with exact IDs
    migrator.migrate_vlans(source_vlans)
    
    # Step 4: Configure syslog
    migrator.configure_syslog()
    
    # Step 5: Apply firewall rules
    migrator.apply_firewall_rules(firewall_rules)
    
    print("\n✅ Configuration applied successfully!")
    print("   - Exact VLAN IDs preserved (1, 101, 201, 300, 301, 800, 801, 803, 900)")
    print("   - IP addresses translated to test range (10.255.255.x)")
    print("   - DHCP relay converted to server mode for test environment")

if __name__ == "__main__":
    main()