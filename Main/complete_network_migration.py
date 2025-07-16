#!/usr/bin/env python3
"""
Complete Network Migration Script
================================

This script performs a complete Meraki MX network migration including:
- Policy object migration between organizations
- Group policy creation  
- VLAN migration with ID remapping
- Syslog server configuration
- Complete firewall rules deployment

Usage:
    python3 complete_network_migration.py --network-id <network_id> --source-config <json_file> --firewall-template <json_file> --mode <test|production>

Example:
    python3 complete_network_migration.py --network-id L_3790904986339115852 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --mode test

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
    'host': '10.0.175.30',
    'port': 514,
    'roles': ['Flows', 'URLs', 'Security events', 'Appliance event log']
}

# Known source organization for policy objects
POLICY_SOURCE_ORG_ID = "436883"  # DTC-Store-Inventory-All

class CompleteNetworkMigrator:
    def __init__(self, network_id, mode='production'):
        """Initialize the complete network migrator"""
        self.network_id = network_id
        self.mode = mode.lower()
        self.vlan_mapping = STANDARD_VLAN_MAPPING.copy()
        self.group_policy_mapping = {}
        self.object_id_mapping = {}
        self.group_id_mapping = {}
        
        # Get target organization ID
        self.target_org_id = self.get_network_org_id()
        
        # Logging
        self.start_time = datetime.now()
        self.log_entries = []
        
        self.log(f"Complete Network Migrator v1.0 initialized")
        self.log(f"Target Network: {network_id}")
        self.log(f"Target Organization: {self.target_org_id}")
        self.log(f"Mode: {self.mode.upper()}")
        
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
    
    def get_network_org_id(self):
        """Get organization ID for the target network"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        response = self.make_api_request(url)
        if response:
            return response['organizationId']
        else:
            raise Exception("Could not determine target organization ID")
    
    def discover_policy_object_references(self, firewall_rules):
        """Discover all policy object references in firewall rules"""
        import re
        
        self.log("\nStep 1: Discovering policy object references...")
        
        object_refs = set()
        group_refs = set()
        
        for rule in firewall_rules:
            src = rule.get('srcCidr', '')
            dst = rule.get('destCidr', '')
            
            # Use regex to find ALL OBJ() references (handles multiple objects in single rule)
            obj_pattern = r'OBJ\((\d+)\)'
            grp_pattern = r'GRP\((\d+)\)'
            
            # Find all objects in source and destination
            src_objects = re.findall(obj_pattern, src)
            dst_objects = re.findall(obj_pattern, dst)
            object_refs.update(src_objects + dst_objects)
            
            # Find all groups in source and destination
            src_groups = re.findall(grp_pattern, src)
            dst_groups = re.findall(grp_pattern, dst)
            group_refs.update(src_groups + dst_groups)
        
        self.log(f"  Found {len(object_refs)} policy object references")
        self.log(f"  Found {len(group_refs)} policy group references")
        
        return list(object_refs), list(group_refs)
    
    def migrate_policy_objects(self, target_object_ids, target_group_ids):
        """Migrate policy objects from source organization"""
        self.log("\nStep 2: Migrating policy objects...")
        
        # Get source objects and groups
        source_objects = self.get_policy_objects(POLICY_SOURCE_ORG_ID)
        source_groups = self.get_policy_groups(POLICY_SOURCE_ORG_ID)
        
        # Get existing objects in target org
        target_objects = self.get_policy_objects(self.target_org_id)
        target_groups = self.get_policy_groups(self.target_org_id)
        
        existing_object_names = {obj['name'] for obj in target_objects}
        existing_group_names = {grp['name'] for grp in target_groups}
        
        # Collect all dependent objects for groups
        all_dependent_ids = set()
        for source_group in source_groups:
            if str(source_group['id']) in target_group_ids:
                group_objects = source_group.get('objectIds', [])
                all_dependent_ids.update(str(obj_id) for obj_id in group_objects)
        
        # Create individual objects first
        all_needed_objects = set(target_object_ids) | all_dependent_ids
        
        for source_obj in source_objects:
            if str(source_obj['id']) in all_needed_objects:
                # Check if already exists
                if source_obj['name'] in existing_object_names:
                    existing_obj = next((obj for obj in target_objects if obj['name'] == source_obj['name']), None)
                    if existing_obj:
                        self.object_id_mapping[str(source_obj['id'])] = str(existing_obj['id'])
                    continue
                
                # Create new object
                obj_data = {
                    'name': source_obj['name'],
                    'category': source_obj['category'],
                    'type': source_obj['type'],
                    'cidr': source_obj.get('cidr'),
                    'fqdn': source_obj.get('fqdn'),
                    'mask': source_obj.get('mask'),
                    'ip': source_obj.get('ip')
                }
                obj_data = {k: v for k, v in obj_data.items() if v is not None}
                
                self.log(f"  Creating object: {source_obj['name']} ({source_obj['type']})")
                result = self.create_policy_object(self.target_org_id, obj_data)
                
                if result:
                    self.object_id_mapping[str(source_obj['id'])] = str(result['id'])
                    self.log(f"    ✓ Created with ID: {result['id']}")
                else:
                    self.log(f"    ✗ Failed to create object", "ERROR")
        
        # Create groups
        for source_group in source_groups:
            if str(source_group['id']) in target_group_ids:
                # Check if already exists
                if source_group['name'] in existing_group_names:
                    existing_grp = next((grp for grp in target_groups if grp['name'] == source_group['name']), None)
                    if existing_grp:
                        self.group_id_mapping[str(source_group['id'])] = str(existing_grp['id'])
                    continue
                
                # Map object IDs
                new_object_ids = []
                for old_obj_id in source_group.get('objectIds', []):
                    new_obj_id = self.object_id_mapping.get(str(old_obj_id))
                    if new_obj_id:
                        new_object_ids.append(new_obj_id)
                
                if not new_object_ids:
                    self.log(f"  ✗ No valid object IDs for group {source_group['name']}", "ERROR")
                    continue
                
                # Create group
                group_data = {
                    'name': source_group['name'],
                    'objectIds': new_object_ids
                }
                
                self.log(f"  Creating group: {source_group['name']} with {len(new_object_ids)} objects")
                result = self.create_policy_group(self.target_org_id, group_data)
                
                if result:
                    self.group_id_mapping[str(source_group['id'])] = str(result['id'])
                    self.log(f"    ✓ Created with ID: {result['id']}")
                else:
                    self.log(f"    ✗ Failed to create group", "ERROR")
    
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
        """Create group policies"""
        if not source_policies:
            self.log("No group policies to create")
            return
            
        self.log("\nStep 3: Creating group policies...")
        
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
                new_id = result.get('groupPolicyId')
                self.group_policy_mapping[old_id] = new_id
                self.log(f"    ✓ Created policy with new ID: {new_id}")
            else:
                self.log(f"    ✗ Failed to create policy", "ERROR")
                
            time.sleep(1)
    
    def migrate_vlans(self, source_vlans):
        """Migrate VLANs with complete logic"""
        self.log("\nStep 4: Cleaning up existing VLANs...")
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
        
        self.log("\nStep 5: Migrating VLANs...")
        
        # Process VLAN 1 -> 100 migration
        default_vlan = next((v for v in source_vlans if v['id'] == 1), None)
        
        if default_vlan:
            current_vlans = self.get_current_vlans()
            vlan_1_exists = any(v['id'] == 1 for v in current_vlans)
            vlan_100_exists = any(v['id'] == 100 for v in current_vlans)
            
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
            
            # Handle VLAN 100 - either create or update existing
            vlan_100_data = self.process_vlan_data(default_vlan, 100)
            vlan_100_data['name'] = 'Data'
            
            if vlan_100_exists:
                # Update existing VLAN 100
                self.log(f"  Updating existing VLAN 100 (Data) with subnet {vlan_100_data['subnet']}")
                result = self.update_vlan(100, vlan_100_data)
                if result:
                    self.log("    ✓ Updated VLAN 100")
            else:
                # Create new VLAN 100
                vlan_100_data['id'] = 100
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
        
        # Create other VLANs
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
                
            self.log(f"  Creating VLAN {new_vlan_id} (was {old_vlan_id})")
            
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
        
        # Clean up temporary VLANs
        if last_vlan_id and last_vlan_id not in [100, 200, 300, 301, 400, 410, 800, 803, 900]:
            self.log(f"  Cleaning up temporary VLAN {last_vlan_id}...")
            self.delete_vlan(last_vlan_id)
    
    def configure_syslog(self, syslog_config=None):
        """Configure syslog server"""
        self.log("\nStep 6: Configuring syslog server...")
        
        if not syslog_config:
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
    
    def apply_firewall_rules(self, firewall_rules):
        """Apply firewall rules with object/group references"""
        self.log("\nStep 7: Applying firewall rules...")
        
        if not firewall_rules:
            self.log("No firewall rules to apply")
            return
            
        self.log(f"Applying {len(firewall_rules)} firewall rules...")
        
        # Update rules with new object/group IDs
        updated_rules = []
        for rule in firewall_rules:
            updated_rule = rule.copy()
            updated_rule.pop('ruleNumber', None)  # Will be auto-assigned
            
            # Update source CIDR references
            src = rule.get('srcCidr', '')
            if 'OBJ(' in src:
                for old_id, new_id in self.object_id_mapping.items():
                    src = src.replace(f'OBJ({old_id})', f'OBJ({new_id})')
                updated_rule['srcCidr'] = src
            elif 'GRP(' in src:
                for old_id, new_id in self.group_id_mapping.items():
                    src = src.replace(f'GRP({old_id})', f'GRP({new_id})')
                updated_rule['srcCidr'] = src
            
            # Update destination CIDR references
            dst = rule.get('destCidr', '')
            if 'OBJ(' in dst:
                for old_id, new_id in self.object_id_mapping.items():
                    dst = dst.replace(f'OBJ({old_id})', f'OBJ({new_id})')
                updated_rule['destCidr'] = dst
            elif 'GRP(' in dst:
                for old_id, new_id in self.group_id_mapping.items():
                    dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
                updated_rule['destCidr'] = dst
            
            updated_rules.append(updated_rule)
        
        # Apply rules via API
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        data = {'rules': updated_rules}
        
        result = self.make_api_request(url, method='PUT', data=data)
        if result:
            actual_count = len(result.get('rules', []))
            self.log(f"  ✓ Successfully applied {actual_count} firewall rules")
            return True
        else:
            self.log(f"  ✗ Failed to apply firewall rules", "ERROR")
            return False
    
    def get_current_vlans(self):
        """Get current VLAN configuration"""
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
    
    def process_vlan_data(self, vlan, new_vlan_id):
        """Process VLAN data for migration"""
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
                self.log(f"    TEST MODE: Changing IP from {vlan.get('subnet')} to {ip_config['new_subnet']}")
            else:
                # Update subnet for test network (10.x.x.x -> 10.255.255.x)
                if vlan_data.get('subnet'):
                    old_subnet = vlan_data['subnet']
                    vlan_data['subnet'] = self.update_ip_for_test(old_subnet)
                    if old_subnet != vlan_data['subnet']:
                        self.log(f"    TEST MODE: Changing IP from {old_subnet} to {vlan_data['subnet']}")
                        
                if vlan_data.get('applianceIp'):
                    vlan_data['applianceIp'] = self.update_appliance_ip_for_test(vlan_data['applianceIp'])
        else:
            # PRODUCTION MODE: Keep original IPs
            self.log(f"    PRODUCTION MODE: Keeping original IP {vlan.get('subnet')}")
            
        # Update group policy ID if mapped
        if 'groupPolicyId' in vlan_data:
            old_policy_id = vlan_data['groupPolicyId']
            new_policy_id = self.group_policy_mapping.get(old_policy_id)
            if new_policy_id:
                vlan_data['groupPolicyId'] = new_policy_id
                self.log(f"    Updated group policy ID: {old_policy_id} → {new_policy_id}")
            else:
                vlan_data.pop('groupPolicyId', None)
                self.log(f"    Removed unmapped group policy ID: {old_policy_id}", "WARNING")
        
        # Process DHCP settings
        vlan_data = self.process_dhcp_settings(vlan_data)
        
        # Clean up data
        vlan_data = self.clean_vlan_data(vlan_data)
        
        return vlan_data
    
    def process_dhcp_settings(self, vlan_data):
        """Process and preserve DHCP settings"""
        vlan_id = vlan_data.get('id')
        old_vlan_id = None
        
        # Determine original VLAN ID for reverse mapping
        for orig_id, new_id in self.vlan_mapping.items():
            if new_id == vlan_id:
                old_vlan_id = orig_id
                break
        
        # Log DHCP configuration being applied
        dhcp_handling = vlan_data.get('dhcpHandling', 'Not specified')
        dns_servers = vlan_data.get('dnsNameservers', 'Not specified')
        self.log(f"      DHCP settings: handling={dhcp_handling}, DNS={dns_servers}")
        
        # Handle DHCP relay in test mode - relay servers not reachable from test IP ranges
        if vlan_data.get('dhcpRelayServerIps'):
            if self.mode == 'test':
                # In test mode, convert DHCP relay to DHCP server since relay servers aren't reachable
                self.log(f"      TEST MODE: Converting DHCP relay to DHCP server (relay servers not reachable from test range)")
                vlan_data['dhcpHandling'] = 'Run a DHCP server'
                vlan_data['dhcpLeaseTime'] = '12 hours'
                vlan_data.pop('dhcpRelayServerIps', None)  # Remove relay servers
                self.log(f"      TEST MODE: Updated to DHCP server with 12 hour lease")
            else:
                self.log(f"      PRODUCTION MODE: Preserving DHCP relay servers: {vlan_data['dhcpRelayServerIps']}")
            
        # Process DHCP options if present
        if vlan_data.get('dhcpOptions'):
            self.log(f"      Preserving {len(vlan_data['dhcpOptions'])} DHCP options")
            
        # Process reserved IP ranges
        if vlan_data.get('reservedIpRanges') and self.mode == 'test':
            updated_ranges = []
            for range_data in vlan_data['reservedIpRanges']:
                if 'start' in range_data and 'end' in range_data:
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
            self.log(f"      DHCP settings: {', '.join(dhcp_settings)}")
            
        return vlan_data
    
    def clean_vlan_data(self, vlan_data):
        """Remove fields that can't be set via API"""
        fields_to_remove = [
            'networkId', 'mask', 'id',  # id removed here, added when creating
            'templateVlanType', 'cidr'
        ]
        
        for field in fields_to_remove:
            vlan_data.pop(field, None)
            
        return vlan_data
    
    def update_ip_for_test(self, ip_str):
        """Update IP address for test mode"""
        if self.mode != 'test' or not ip_str or '/' not in ip_str:
            return ip_str
            
        try:
            ip_net = ipaddress.ip_network(ip_str, strict=False)
            if str(ip_net.network_address).startswith('10.'):
                parts = str(ip_net.network_address).split('.')
                new_ip = f"{TEST_NETWORK_PREFIX}.{parts[3]}/{ip_net.prefixlen}"
                return new_ip
            return ip_str
        except:
            return ip_str
            
    def update_appliance_ip_for_test(self, ip_str):
        """Update appliance IP for test mode"""
        if self.mode != 'test' or not ip_str:
            return ip_str
            
        try:
            if ip_str.startswith('10.'):
                parts = ip_str.split('.')
                return f"{TEST_NETWORK_PREFIX}.{parts[3]}"
            return ip_str
        except:
            return ip_str
    
    def validate_deployment(self):
        """Validate the complete deployment"""
        self.log("\nStep 8: Validating deployment...")
        
        validation_results = {
            'vlans': False,
            'group_policies': False,
            'firewall_rules': False,
            'syslog': False
        }
        
        # Check VLANs
        vlans = self.get_current_vlans()
        if len(vlans) >= 8:  # Expecting at least 8 VLANs
            validation_results['vlans'] = True
            self.log(f"  ✓ VLANs: {len(vlans)} configured")
        else:
            self.log(f"  ✗ VLANs: Only {len(vlans)} configured, expected at least 8", "WARNING")
        
        # Check group policies
        url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        policies = self.make_api_request(url) or []
        if len(policies) >= 3:  # Expecting at least 3 policies
            validation_results['group_policies'] = True
            self.log(f"  ✓ Group Policies: {len(policies)} configured")
        else:
            self.log(f"  ✗ Group Policies: Only {len(policies)} configured, expected at least 3", "WARNING")
        
        # Check firewall rules
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        fw_result = self.make_api_request(url)
        if fw_result and len(fw_result.get('rules', [])) >= 50:  # Expecting at least 50 rules
            validation_results['firewall_rules'] = True
            rule_count = len(fw_result['rules'])
            self.log(f"  ✓ Firewall Rules: {rule_count} configured")
        else:
            rule_count = len(fw_result.get('rules', [])) if fw_result else 0
            self.log(f"  ✗ Firewall Rules: Only {rule_count} configured, expected at least 50", "WARNING")
        
        # Check syslog
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        syslog_result = self.make_api_request(url)
        if syslog_result and len(syslog_result.get('servers', [])) >= 1:
            validation_results['syslog'] = True
            self.log(f"  ✓ Syslog: {len(syslog_result['servers'])} server(s) configured")
        else:
            self.log(f"  ✗ Syslog: No servers configured", "WARNING")
        
        # Check switch configurations
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        devices = self.make_api_request(url) or []
        switch_devices = [d for d in devices if d.get('model', '').startswith('MS')]
        if switch_devices:
            validation_results['switches'] = True
            self.log(f"  ✓ Switches: {len(switch_devices)} configured")
        else:
            self.log(f"  ✗ Switches: No switch devices found", "WARNING")
        
        # Overall validation
        all_valid = all(validation_results.values())
        if all_valid:
            self.log("  🎉 All validation checks passed!")
        else:
            failed_items = [k for k, v in validation_results.items() if not v]
            self.log(f"  ⚠️  Validation issues with: {', '.join(failed_items)}", "WARNING")
        
        return validation_results
    
    def get_switch_ports(self, device_serial):
        """Get switch port configuration for a device"""
        url = f"{BASE_URL}/devices/{device_serial}/switch/ports"
        return self.make_api_request(url) or []
    
    def update_switch_port(self, device_serial, port_id, port_config):
        """Update switch port configuration"""
        url = f"{BASE_URL}/devices/{device_serial}/switch/ports/{port_id}"
        return self.make_api_request(url, method='PUT', data=port_config)
    
    def migrate_switch_configurations(self, source_switches):
        """Migrate switch port configurations with VLAN remapping"""
        if not source_switches:
            self.log("No switch configurations to migrate")
            return
        
        self.log("\nStep 8: Migrating switch configurations...")
        
        # Get target devices
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        target_devices = self.make_api_request(url) or []
        target_switches = {d['serial']: d for d in target_devices if d.get('model', '').startswith('MS')}
        
        self.log(f"  Found {len(target_switches)} target switch devices")
        
        total_ports_updated = 0
        used_target_devices = set()  # Track which target devices we've used
        
        for source_serial, source_config in source_switches.items():
            source_name = source_config['device_info']['name']
            source_model = source_config['device_info']['model']
            
            # Find matching target device
            target_serial = None
            target_device = None
            
            # Try exact serial match first
            if source_serial in target_switches:
                target_serial = source_serial
                target_device = target_switches[source_serial]
                self.log(f"  Found exact serial match: {source_serial}")
            else:
                # Match by model for testing, but avoid already used devices
                matching_models = [d for d in target_switches.values() 
                                 if d.get('model') == source_model and d['serial'] not in used_target_devices]
                if matching_models:
                    target_device = matching_models[0]  # Take first available
                    target_serial = target_device['serial']
                    used_target_devices.add(target_serial)  # Mark as used
                    self.log(f"  Matched by model: {source_name} ({source_model}) → {target_device.get('name', target_serial)}")
                else:
                    self.log(f"  No available target device for {source_name} ({source_model})", "WARNING")
                    continue
            
            # Deploy port configurations
            ports_config = source_config['ports']
            self.log(f"  Deploying {len(ports_config)} ports to {target_device.get('name', target_serial)}")
            
            successful_ports = 0
            failed_ports = 0
            
            for port in ports_config:
                port_id = port['portId']
                
                # Apply VLAN remapping to port config
                updated_port = port.copy()
                
                # Update access VLAN
                if 'vlan' in port and port['vlan'] in self.vlan_mapping:
                    old_vlan = port['vlan']
                    new_vlan = self.vlan_mapping[old_vlan]
                    updated_port['vlan'] = new_vlan
                
                # Update voice VLAN
                if 'voiceVlan' in port and port['voiceVlan'] in self.vlan_mapping:
                    old_voice_vlan = port['voiceVlan']
                    new_voice_vlan = self.vlan_mapping[old_voice_vlan]
                    updated_port['voiceVlan'] = new_voice_vlan
                
                # Remove read-only fields
                port_config = {k: v for k, v in updated_port.items() if k not in ['portId', 'schedule']}
                
                result = self.update_switch_port(target_serial, port_id, port_config)
                if result:
                    successful_ports += 1
                else:
                    failed_ports += 1
                
                # Rate limiting
                time.sleep(0.1)
            
            self.log(f"    ✓ {successful_ports}/{len(ports_config)} ports deployed successfully")
            if failed_ports > 0:
                self.log(f"    ⚠️  {failed_ports} ports failed to deploy", "WARNING")
            
            total_ports_updated += successful_ports
        
        self.log(f"  Switch migration complete: {total_ports_updated} total ports configured")
    
    def generate_report(self):
        """Generate comprehensive migration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
Complete Network Migration Report
=================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Network ID: {self.network_id}
Organization: {self.target_org_id}
Mode: {self.mode.upper()}
Duration: {duration}

Policy Object Mappings:
"""
        for old_id, new_id in self.object_id_mapping.items():
            report += f"  Object {old_id} → {new_id}\n"
        
        report += "\nPolicy Group Mappings:\n"
        for old_id, new_id in self.group_id_mapping.items():
            report += f"  Group {old_id} → {new_id}\n"
            
        report += "\nGroup Policy Mappings:\n"
        for old_id, new_id in self.group_policy_mapping.items():
            report += f"  Policy {old_id} → {new_id}\n"
            
        report += "\nMigration Log:\n"
        for entry in self.log_entries:
            report += entry + "\n"
            
        return report

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Complete Network Migration Tool v1.0')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--source-config', required=True, help='Source configuration JSON file')
    parser.add_argument('--firewall-template', required=True, help='Firewall rules template JSON file')
    parser.add_argument('--syslog-server', help='Syslog server IP address')
    parser.add_argument('--syslog-port', type=int, default=514, help='Syslog server port (default: 514)')
    parser.add_argument('--mode', choices=['test', 'production'], default='production',
                       help='Migration mode: test (changes IPs) or production (keeps IPs)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🚀 Complete Network Migration Tool v1.0")
    print("=" * 60)
    
    # Load source configuration
    try:
        with open(args.source_config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading source configuration: {e}")
        sys.exit(1)
        
    # Load firewall template
    try:
        with open(args.firewall_template, 'r') as f:
            firewall_template = json.load(f)
    except Exception as e:
        print(f"❌ Error loading firewall template: {e}")
        sys.exit(1)
        
    # Extract configuration components
    source_vlans = []
    source_policies = []
    source_switches = {}
    
    if 'appliance' in config:
        if 'vlans' in config['appliance']:
            source_vlans = config['appliance']['vlans']
        if 'groupPolicies' in config['appliance']:
            source_policies = config['appliance']['groupPolicies']
    else:
        print("❌ No appliance configuration found in source file")
        sys.exit(1)
    
    # Extract switch configurations if available
    if 'ports' in config:
        # Convert ports data to switch format
        for device_serial, ports in config['ports'].items():
            # Find device info
            device_info = None
            for device in config.get('devices', []):
                if device['serial'] == device_serial:
                    device_info = {
                        'serial': device['serial'],
                        'name': device.get('name', device_serial),
                        'model': device.get('model', 'Unknown'),
                        'mac': device.get('mac'),
                        'lanIp': device.get('lanIp'),
                        'firmware': device.get('firmware')
                    }
                    break
            
            if device_info:
                source_switches[device_serial] = {
                    'device_info': device_info,
                    'ports': ports
                }
    
    firewall_rules = firewall_template.get('rules', [])
    
    print(f"📋 Configuration Summary:")
    print(f"  Source VLANs: {len(source_vlans)}")
    print(f"  Group Policies: {len(source_policies)}")
    print(f"  Switch Devices: {len(source_switches)}")
    print(f"  Switch Ports: {sum(len(s['ports']) for s in source_switches.values())}")
    print(f"  Firewall Rules: {len(firewall_rules)}")
    print(f"  Mode: {args.mode.upper()}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        print("\nVLANs that would be migrated:")
        for vlan in source_vlans:
            old_id = vlan['id']
            new_id = STANDARD_VLAN_MAPPING.get(old_id)
            if new_id:
                print(f"  VLAN {old_id} -> VLAN {new_id}")
        print("\nGroup policies that would be created:")
        for policy in source_policies:
            print(f"  {policy['name']} (ID: {policy['groupPolicyId']})")
        print(f"\nFirewall rules that would be applied: {len(firewall_rules)}")
        return
        
    # Confirm before proceeding
    if not args.auto_confirm:
        print(f"\n⚠️  WARNING: This will completely replace the configuration of network {args.network_id}")
        print(f"Mode: {args.mode.upper()}")
        if args.mode == 'test':
            print("TEST MODE: IP addresses WILL be changed for testing")
        else:
            print("PRODUCTION MODE: IP addresses will be preserved")
            
        # Add auto-confirm option
        if hasattr(args, 'auto_confirm') and args.auto_confirm:
            print("\n✅ Auto-confirming migration...")
        else:
            response = input("\n❓ Proceed with complete migration? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Migration cancelled")
                return
    
    # Create migrator and run complete migration
    try:
        migrator = CompleteNetworkMigrator(args.network_id, args.mode)
        
        # Step 1: Discover policy object references
        target_object_ids, target_group_ids = migrator.discover_policy_object_references(firewall_rules)
        
        # Step 2: Migrate policy objects
        if target_object_ids or target_group_ids:
            migrator.migrate_policy_objects(target_object_ids, target_group_ids)
        
        # Step 3: Create group policies
        migrator.create_group_policies(source_policies)
        
        # Step 4-5: Migrate VLANs
        migrator.migrate_vlans(source_vlans)
        
        # Step 6: Configure syslog
        syslog_config = None
        if args.syslog_server:
            syslog_config = {
                'host': args.syslog_server,
                'port': args.syslog_port,
                'roles': ['Flows', 'URLs', 'Security events', 'Appliance event log']
            }
        
        if migrator.configure_syslog(syslog_config):
            # Step 7: Apply firewall rules
            migrator.apply_firewall_rules(firewall_rules)
        else:
            print("\n⚠️  WARNING: Skipping firewall rules due to syslog configuration failure")
        
        # Step 8: Migrate switch configurations
        if source_switches:
            migrator.migrate_switch_configurations(source_switches)
        
        # Step 9: Validate deployment
        validation_results = migrator.validate_deployment()
        
        # Generate and save report
        report = migrator.generate_report()
        report_file = f"complete_migration_report_{args.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save ID mappings for reference
        mappings = {
            'object_mappings': migrator.object_id_mapping,
            'group_mappings': migrator.group_id_mapping,
            'policy_mappings': migrator.group_policy_mapping,
            'timestamp': datetime.now().isoformat()
        }
        
        mappings_file = f"migration_mappings_{args.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(mappings_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        print(f"📄 Mappings saved to: {mappings_file}")
        
        # Final status
        if all(validation_results.values()):
            print("\n🎉 ✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("All components validated and working correctly.")
        else:
            print("\n⚠️  🔶 MIGRATION COMPLETED WITH WARNINGS")
            print("Some validation checks failed. Please review the logs.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(__doc__)
        print("\nExample usage:")
        print("  python3 complete_network_migration.py --network-id L_3790904986339115852 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --mode test")
        print("  python3 complete_network_migration.py --network-id L_12345 --source-config azp_30_config.json --firewall-template firewall_rules_template.json --mode production --auto-confirm")
    else:
        main()