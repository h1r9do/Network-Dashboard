#!/usr/bin/env python3
"""
Complete VLAN Number Migration Script - DEBUG VERSION
=====================================================

Enhanced with comprehensive debugging output for troubleshooting
"""

import os
import sys
import json
import requests
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
import copy
import traceback

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# VLAN mapping - CORRECTED per user requirements
VLAN_MAPPING = {
    1: 100,    # Data
    101: 200,  # Voice
    801: 400,  # IoT (IP change required)
    201: 410,  # Credit Card
    # These remain the same:
    300: 300,  # AP Mgmt → Net Mgmt (name change)
    301: 301,  # Scanner (no change)
    800: 800,  # Guest (IP change required)
    803: 803,  # IoT Wireless (no change)
    900: 900,  # Mgmt (no change)
}

# IP changes required for specific VLANs
IP_CHANGES = {
    800: {
        'old_subnet': '172.13.0.1/30',
        'new_subnet': '172.16.80.1/24',
        'old_ip': '172.13.0.1',
        'new_ip': '172.16.80.1'
    },
    400: {  # This will be the new VLAN ID for 801
        'old_subnet': '172.13.0.1/30', 
        'new_subnet': '172.16.40.1/24',
        'old_ip': '172.13.0.1',
        'new_ip': '172.16.40.1'
    }
}

class CompleteVlanMigrator:
    def __init__(self, network_id, dry_run=False):
        """Initialize complete VLAN migrator with debug mode"""
        self.network_id = network_id
        self.dry_run = dry_run
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        
        # Debug flags
        self.debug = True
        self.verbose = True
        
        # Get network info
        self.network_info = self.get_network_info()
        self.org_id = self.network_info['organizationId']
        
        self.log(f"Complete VLAN Migrator initialized for {self.network_info['name']}")
        self.log(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self.log(f"DEBUG: Enabled - Verbose logging active")
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)
    
    def debug_log(self, message, data=None):
        """Debug logging with optional data dump"""
        if self.debug:
            self.log(f"DEBUG: {message}", "DEBUG")
            if data and self.verbose:
                if isinstance(data, (dict, list)):
                    self.log(f"DEBUG DATA: {json.dumps(data, indent=2)}", "DEBUG")
                else:
                    self.log(f"DEBUG DATA: {data}", "DEBUG")
    
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with error handling and debug output"""
        self.debug_log(f"API Request: {method} {url}")
        
        if self.dry_run and method in ['POST', 'PUT', 'DELETE']:
            self.log(f"DRY RUN: Would {method} to {url}", "DRY_RUN")
            if data:
                self.log(f"DRY RUN: With data: {json.dumps(data, indent=2)}", "DRY_RUN")
            return {'dry_run': True}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS, timeout=30)
            
            self.debug_log(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json() if response.text else {}
                self.debug_log(f"Response received ({len(str(result))} chars)")
                return result
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 204:
                return {}
            else:
                self.log(f"API Error: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except requests.exceptions.Timeout:
            self.log(f"API Timeout: {url}", "ERROR")
            return None
        except Exception as e:
            self.log(f"API Exception: {str(e)}", "ERROR")
            self.debug_log(f"Exception traceback: {traceback.format_exc()}")
            return None
    
    def get_network_info(self):
        """Get network information"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        info = self.make_api_request(url)
        if info:
            self.debug_log(f"Network info retrieved: {info['name']} (ID: {info['id']})")
        return info
    
    def take_complete_backup(self):
        """Take complete backup of all configurations"""
        self.log("\n" + "="*60)
        self.log("Taking complete configuration backup...")
        self.log("="*60)
        
        # Backup VLANs
        self.log("Backing up VLANs...")
        vlans_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        vlans = self.make_api_request(vlans_url)
        if vlans:
            self.backup_data['vlans'] = vlans
            self.log(f"  ✓ Backed up {len(vlans)} VLANs")
            self.debug_log("VLAN IDs backed up", [v['id'] for v in vlans])
        
        # Backup firewall rules
        self.log("Backing up firewall rules...")
        fw_url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        fw_rules = self.make_api_request(fw_url)
        if fw_rules:
            self.backup_data['firewall_rules'] = fw_rules
            rule_count = len(fw_rules.get('rules', []))
            self.log(f"  ✓ Backed up {rule_count} firewall rules")
            self.debug_log(f"First 3 rules", fw_rules.get('rules', [])[:3])
        
        # Backup group policies
        self.log("Backing up group policies...")
        gp_url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        group_policies = self.make_api_request(gp_url)
        if group_policies:
            self.backup_data['group_policies'] = group_policies
            self.log(f"  ✓ Backed up {len(group_policies)} group policies")
        
        # Get devices
        devices_url = f"{BASE_URL}/networks/{self.network_id}/devices"
        devices = self.make_api_request(devices_url)
        self.backup_data['devices'] = devices or []
        
        # Backup switch configurations
        self.log("Backing up switch configurations...")
        self.backup_data['switch_ports'] = {}
        for device in devices:
            if device['model'].startswith('MS'):
                self.debug_log(f"Backing up ports for switch {device['name']} ({device['serial']})")
                ports_url = f"{BASE_URL}/devices/{device['serial']}/switch/ports"
                ports = self.make_api_request(ports_url)
                if ports:
                    self.backup_data['switch_ports'][device['serial']] = ports
                    self.log(f"  ✓ Backed up {len(ports)} ports for {device['name']}")
                time.sleep(0.5)
        
        # Backup MX ports
        self.log("Backing up MX ports...")
        self.backup_data['mx_ports'] = {}
        for device in devices:
            if device['model'].startswith('MX'):
                self.debug_log(f"Checking MX ports for {device['name']}")
                for port_num in range(2, 12):
                    port_url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                    port_config = self.make_api_request(port_url)
                    if port_config:
                        self.backup_data['mx_ports'][port_num] = port_config
                        self.debug_log(f"Port {port_num} config", port_config)
                self.log(f"  ✓ Backed up {len(self.backup_data['mx_ports'])} MX ports")
                time.sleep(0.5)
        
        # Backup syslog configuration
        self.log("Backing up syslog configuration...")
        syslog_url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        syslog = self.make_api_request(syslog_url)
        if syslog:
            self.backup_data['syslog'] = syslog
        
        # Save backup to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"complete_vlan_backup_{self.network_id}_{timestamp}.json"
        
        if not self.dry_run:
            with open(backup_filename, 'w') as f:
                json.dump(self.backup_data, f, indent=2)
            self.log(f"\n✓ Complete backup saved to {backup_filename}")
        else:
            self.log(f"\nDRY RUN: Would save backup to {backup_filename}")
            
        return backup_filename
    
    def clear_vlan_references(self):
        """Clear all VLAN references before deletion"""
        self.log("\n" + "="*60)
        self.log("Clearing VLAN references...")
        self.log("="*60)
        
        # Create temporary VLANs
        temp_vlan_mapping = {
            1: 999,     # Data ports temporary
            101: 998,   # Voice temporary  
            801: 997,   # IoT temporary
            201: 996    # Credit card temporary
        }
        
        # Step 1: Clear firewall rules
        self.log("\nStep 1: Clearing firewall rules...")
        self.debug_log("Current firewall rule count", len(self.backup_data.get('firewall_rules', {}).get('rules', [])))
        
        if not self.dry_run:
            fw_url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
            clear_rules = {'rules': []}
            result = self.make_api_request(fw_url, 'PUT', clear_rules)
            if result:
                self.log("  ✓ Firewall rules cleared")
        else:
            self.log("  DRY RUN: Would clear firewall rules")
        
        # Step 2: Create temporary VLANs first
        self.log("\nStep 2: Creating temporary VLANs...")
        
        # Create all temporary VLANs before moving any ports
        for old_vlan, temp_vlan in temp_vlan_mapping.items():
            # Check if old VLAN exists (handle both string and int IDs)
            existing_vlan = next((v for v in self.backup_data['vlans'] if str(v['id']) == str(old_vlan)), None)
            if not existing_vlan:
                self.debug_log(f"VLAN {old_vlan} not found in backup data")
                self.debug_log(f"Available VLAN IDs: {[v['id'] for v in self.backup_data['vlans']]}")
                continue
                
            self.log(f"  Creating temporary VLAN {temp_vlan}...")
            
            if not self.dry_run:
                # Create temporary VLAN
                temp_vlan_data = {
                    'id': str(temp_vlan),
                    'name': f"TEMP_{temp_vlan}",
                    'subnet': f"10.255.{temp_vlan % 255}.0/24",
                    'applianceIp': f"10.255.{temp_vlan % 255}.1"
                }
                create_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
                result = self.make_api_request(create_url, 'POST', temp_vlan_data)
                if result:
                    self.debug_log(f"Created temp VLAN {temp_vlan}", result)
                    self.log(f"  ✓ Created temporary VLAN {temp_vlan}")
                else:
                    self.log(f"  ✗ Failed to create temporary VLAN {temp_vlan}", "ERROR")
                time.sleep(1)
        
        # Step 3: Now move switch ports to temporary VLANs
        self.log("\nStep 3: Moving switch ports to temporary VLANs...")
        
        # Move switch ports to temporary VLANs
        for serial, ports in self.backup_data.get('switch_ports', {}).items():
            device_name = next((d['name'] for d in self.backup_data['devices'] if d['serial'] == serial), serial)
            ports_to_update = []
            
            for port in ports:
                if port.get('vlan') and int(port['vlan']) in temp_vlan_mapping:
                    old_vlan = int(port['vlan'])
                    new_temp_vlan = temp_vlan_mapping[old_vlan]
                    ports_to_update.append({
                        'portId': port['portId'],
                        'old_vlan': old_vlan,
                        'new_vlan': new_temp_vlan
                    })
            
            if ports_to_update:
                self.debug_log(f"Updating {len(ports_to_update)} ports on {device_name}")
                
                for port_update in ports_to_update:
                    if not self.dry_run:
                        port_url = f"{BASE_URL}/devices/{serial}/switch/ports/{port_update['portId']}"
                        update_data = {'vlan': port_update['new_vlan']}
                        result = self.make_api_request(port_url, 'PUT', update_data)
                        if result:
                            self.debug_log(f"Port {port_update['portId']}: VLAN {port_update['old_vlan']} → {port_update['new_vlan']}")
                        time.sleep(0.2)
                
                self.log(f"  ✓ Updated {len(ports_to_update)} ports on {device_name}")
        
        # Step 4: Update MX ports to temporary VLANs
        self.log("\nStep 4: Updating MX ports to temporary VLANs...")
        mx_updates = 0
        
        for port_num, port_config in self.backup_data.get('mx_ports', {}).items():
            if port_config.get('vlan') and int(port_config['vlan']) in temp_vlan_mapping:
                old_vlan = int(port_config['vlan'])
                new_temp_vlan = temp_vlan_mapping[old_vlan]
                
                if not self.dry_run:
                    port_url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                    # Only update if port is enabled
                    if port_config.get('enabled'):
                        update_data = {'vlan': new_temp_vlan}
                        result = self.make_api_request(port_url, 'PUT', update_data)
                        if result:
                            self.debug_log(f"MX Port {port_num}: VLAN {old_vlan} → {new_temp_vlan}")
                            mx_updates += 1
                        else:
                            self.log(f"  WARNING: Failed to update MX port {port_num} to VLAN {new_temp_vlan}", "WARNING")
                    time.sleep(0.5)
        
        self.log(f"  ✓ Updated {mx_updates} MX ports")
        
        return temp_vlan_mapping
    
    def migrate_vlans(self):
        """Delete old VLANs and create new ones"""
        self.log("\n" + "="*60)
        self.log("Migrating VLANs to new IDs...")
        self.log("="*60)
        
        # Process VLANs that need migration
        for old_id, new_id in VLAN_MAPPING.items():
            existing_vlan = next((v for v in self.backup_data['vlans'] if str(v['id']) == str(old_id)), None)
            
            if not existing_vlan:
                self.debug_log(f"VLAN {old_id} not found, skipping")
                continue
            
            # Skip if no change needed
            if old_id == new_id and old_id not in [800, 400]:
                self.log(f"\nVLAN {old_id} - No change needed")
                
                # Check for IP changes
                if new_id == 800:
                    self.log(f"VLAN 800 - Updating IP configuration...")
                    if not self.dry_run:
                        update_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{new_id}"
                        update_data = {
                            'subnet': IP_CHANGES[800]['new_subnet'],
                            'applianceIp': IP_CHANGES[800]['new_ip']
                        }
                        result = self.make_api_request(update_url, 'PUT', update_data)
                        if result:
                            self.log(f"  ✓ Updated VLAN 800 IP configuration")
                            self.debug_log("New IP config", update_data)
                        time.sleep(1)
                continue
            
            self.log(f"\nMigrating VLAN {old_id} → {new_id}")
            
            # Delete old VLAN
            self.log(f"  Deleting VLAN {old_id}...")
            if not self.dry_run:
                delete_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{old_id}"
                result = self.make_api_request(delete_url, 'DELETE')
                if result is not None:
                    self.debug_log(f"Deleted VLAN {old_id}")
                time.sleep(3)
            
            # Create new VLAN
            self.log(f"  Creating VLAN {new_id}...")
            new_vlan_data = {
                'id': str(new_id),
                'name': existing_vlan['name'],
                'subnet': existing_vlan['subnet'],
                'applianceIp': existing_vlan['applianceIp']
            }
            
            # Apply IP changes if needed
            if new_id in IP_CHANGES:
                self.log(f"    Applying IP changes for VLAN {new_id}")
                new_vlan_data['subnet'] = IP_CHANGES[new_id]['new_subnet']
                new_vlan_data['applianceIp'] = IP_CHANGES[new_id]['new_ip']
                self.debug_log("IP change applied", {
                    'old': f"{existing_vlan['applianceIp']}/{existing_vlan['subnet']}",
                    'new': f"{new_vlan_data['applianceIp']}/{new_vlan_data['subnet']}"
                })
            
            # Copy other VLAN settings
            for key in ['fixedIpAssignments', 'reservedIpRanges', 'dnsNameservers', 'dhcpHandling', 
                       'dhcpRelayServerIps', 'dhcpLeaseTime', 'dhcpBootOptionsEnabled', 'dhcpOptions']:
                if key in existing_vlan:
                    new_vlan_data[key] = existing_vlan[key]
            
            if not self.dry_run:
                create_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
                result = self.make_api_request(create_url, 'POST', new_vlan_data)
                if result:
                    self.log(f"  ✓ Created VLAN {new_id}")
                    self.debug_log("New VLAN created", result)
                time.sleep(1)
    
    def restore_configurations(self, temp_vlan_mapping):
        """Restore all configurations with new VLAN IDs"""
        self.log("\n" + "="*60)
        self.log("Restoring configurations with new VLAN IDs...")
        self.log("="*60)
        
        # Reverse mapping for restoration
        temp_to_new = {}
        for old_vlan, temp_vlan in temp_vlan_mapping.items():
            new_vlan = VLAN_MAPPING.get(old_vlan, old_vlan)
            temp_to_new[temp_vlan] = new_vlan
        
        self.debug_log("Temp to new VLAN mapping", temp_to_new)
        
        # Step 1: Update switch ports to new VLAN IDs
        self.log("\nStep 1: Updating switch ports to new VLAN IDs...")
        
        for serial, ports in self.backup_data.get('switch_ports', {}).items():
            device_name = next((d['name'] for d in self.backup_data['devices'] if d['serial'] == serial), serial)
            ports_updated = 0
            
            for port in ports:
                if port.get('vlan'):
                    original_vlan = int(port['vlan'])
                    new_vlan = VLAN_MAPPING.get(original_vlan, original_vlan)
                    
                    if original_vlan != new_vlan:
                        self.debug_log(f"Port {port['portId']} needs update: {original_vlan} → {new_vlan}")
                        
                        if not self.dry_run:
                            port_url = f"{BASE_URL}/devices/{serial}/switch/ports/{port['portId']}"
                            update_data = {'vlan': new_vlan}
                            result = self.make_api_request(port_url, 'PUT', update_data)
                            if result:
                                ports_updated += 1
                            time.sleep(0.2)
            
            if ports_updated > 0:
                self.log(f"  ✓ Updated {ports_updated} ports on {device_name}")
        
        # Step 2: Update MX ports to new VLAN IDs
        self.log("\nStep 2: Updating MX ports to new VLAN IDs...")
        mx_updated = 0
        
        for port_num, port_config in self.backup_data.get('mx_ports', {}).items():
            if port_config.get('vlan'):
                original_vlan = int(port_config['vlan'])
                new_vlan = VLAN_MAPPING.get(original_vlan, original_vlan)
                
                if original_vlan != new_vlan and port_config.get('enabled'):
                    self.debug_log(f"MX Port {port_num} needs update: {original_vlan} → {new_vlan}")
                    
                    if not self.dry_run:
                        port_url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                        update_data = {'vlan': new_vlan}
                        result = self.make_api_request(port_url, 'PUT', update_data)
                        if result:
                            mx_updated += 1
                        time.sleep(0.5)
        
        self.log(f"  ✓ Updated {mx_updated} MX ports")
        
        # Step 3: Apply new firewall template
        self.log("\nStep 3: Applying new firewall template...")
        
        # Load 54-rule firewall template (no default rule - Meraki will auto-add)
        neo07_template_file = 'neo07_54_rule_template_20250710_105817.json'
        
        if os.path.exists(neo07_template_file):
            try:
                with open(neo07_template_file, 'r') as f:
                    template_data = json.load(f)
                
                # Check if template is wrapped in a rules object
                if isinstance(template_data, dict) and 'rules' in template_data:
                    neo07_template = template_data['rules']
                    self.log(f"  Loaded template with 'rules' wrapper: {len(neo07_template)} rules")
                elif isinstance(template_data, list):
                    neo07_template = template_data
                    self.log(f"  Loaded template as list: {len(neo07_template)} rules")
                else:
                    self.log(f"  ERROR: Unexpected template format: {type(template_data)}", "ERROR")
                    neo07_template = []
            except json.JSONDecodeError as e:
                self.log(f"  ERROR: Failed to parse firewall template JSON: {e}", "ERROR")
                neo07_template = []
            except Exception as e:
                self.log(f"  ERROR: Failed to load firewall template: {e}", "ERROR")
                neo07_template = []
            
            if neo07_template:
                self.log(f"  Processing {len(neo07_template)} firewall rules...")
                
                # Update VLAN references in template
                processed_rules = []
                for idx, rule in enumerate(neo07_template):
                    # Handle both dict and string rule formats
                    if not isinstance(rule, dict):
                        self.log(f"  WARNING: Rule {idx} is not a dict ({type(rule)}), skipping", "WARNING")
                        continue
                    new_rule = copy.deepcopy(rule)
                    
                    # Update srcCidr VLAN references
                    if 'VLAN(' in str(new_rule.get('srcCidr', '')):
                        for old_vlan, new_vlan in VLAN_MAPPING.items():
                            old_ref = f"VLAN({old_vlan})"
                            new_ref = f"VLAN({new_vlan})"
                            if old_ref in new_rule['srcCidr']:
                                new_rule['srcCidr'] = new_rule['srcCidr'].replace(old_ref, new_ref)
                                self.debug_log(f"Updated srcCidr: {old_ref} → {new_ref}")
                    
                    # Update destCidr VLAN references
                    if 'VLAN(' in str(new_rule.get('destCidr', '')):
                        for old_vlan, new_vlan in VLAN_MAPPING.items():
                            old_ref = f"VLAN({old_vlan})"
                            new_ref = f"VLAN({new_vlan})"
                            if old_ref in new_rule['destCidr']:
                                new_rule['destCidr'] = new_rule['destCidr'].replace(old_ref, new_ref)
                                self.debug_log(f"Updated destCidr: {old_ref} → {new_ref}")
                    
                    processed_rules.append(new_rule)
            
            self.log(f"  Processed {len(processed_rules)} template rules (no policy object issues, Meraki will auto-add default)")
            
            if not self.dry_run:
                fw_url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
                fw_data = {'rules': processed_rules}
                result = self.make_api_request(fw_url, 'PUT', fw_data)
                if result:
                    self.log(f"  ✓ Applied {len(processed_rules)} firewall template rules")
                    self.debug_log("First 3 rules applied", processed_rules[:3])
        else:
            self.log(f"  WARNING: Firewall template file not found: {neo07_template_file}")
            self.log("  Using backup firewall rules instead...")
            
            # Fallback to updating existing rules
            if 'firewall_rules' in self.backup_data:
                processed_rules = []
                for rule in self.backup_data['firewall_rules'].get('rules', []):
                    new_rule = copy.deepcopy(rule)
                    
                    # Update VLAN references
                    for field in ['srcCidr', 'destCidr']:
                        if 'VLAN(' in str(new_rule.get(field, '')):
                            for old_vlan, new_vlan in VLAN_MAPPING.items():
                                old_ref = f"VLAN({old_vlan})"
                                new_ref = f"VLAN({new_vlan})"
                                if old_ref in new_rule[field]:
                                    new_rule[field] = new_rule[field].replace(old_ref, new_ref)
                    
                    processed_rules.append(new_rule)
                
                if not self.dry_run:
                    fw_url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
                    fw_data = {'rules': processed_rules}
                    result = self.make_api_request(fw_url, 'PUT', fw_data)
                    if result:
                        self.log(f"  ✓ Restored {len(processed_rules)} firewall rules with updated VLAN references")
        
        # Step 4: Clean up temporary VLANs
        self.log("\nStep 4: Cleaning up temporary VLANs...")
        
        for temp_vlan in temp_vlan_mapping.values():
            if not self.dry_run:
                delete_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{temp_vlan}"
                result = self.make_api_request(delete_url, 'DELETE')
                if result is not None:
                    self.log(f"  ✓ Deleted temporary VLAN {temp_vlan}")
                time.sleep(1)
    
    def generate_report(self):
        """Generate migration report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"complete_vlan_migration_report_{self.network_id}_{timestamp}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("\nComplete VLAN Migration Report\n")
            f.write("==============================\n")
            f.write(f"Network: {self.network_info['name']} ({self.network_id})\n")
            f.write(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
            f.write("\nVLAN Mapping Applied:\n")
            for old, new in VLAN_MAPPING.items():
                if old != new:
                    f.write(f"  VLAN {old} → VLAN {new}\n")
            f.write("\nLog Entries:\n")
            for entry in self.log_entries:
                f.write(entry + "\n")
        
        self.log(f"\n✓ Migration report saved to {report_filename}")
        
        # Final summary
        self.log("\n" + "="*60)
        if self.dry_run:
            self.log("DRY RUN COMPLETE - No changes were made")
        else:
            self.log("✅ COMPLETE VLAN MIGRATION FINISHED SUCCESSFULLY!")
            self.log(f"Total time: {duration}")
        self.log("="*60)
    
    def run_migration(self):
        """Run the complete migration process"""
        try:
            # 1. Take complete backup
            backup_file = self.take_complete_backup()
            
            # 2. Clear VLAN references
            temp_mapping = self.clear_vlan_references()
            
            # 3. Migrate VLANs
            self.migrate_vlans()
            
            # 4. Restore configurations
            self.restore_configurations(temp_mapping)
            
            # 5. Generate report
            self.generate_report()
            
            return True
            
        except Exception as e:
            self.log(f"\n❌ MIGRATION FAILED: {str(e)}", "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False

def main():
    parser = argparse.ArgumentParser(description='Complete VLAN Migration Script - DEBUG VERSION')
    parser.add_argument('--network-id', required=True, help='Network ID to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("COMPLETE VLAN MIGRATION SCRIPT - DEBUG VERSION")
    print("="*80)
    print(f"Network ID: {args.network_id}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print("="*80)
    
    if not args.dry_run and not os.getenv('SKIP_CONFIRMATION'):
        print("\n⚠️  WARNING: This will completely migrate VLANs on the target network!")
        print("The following changes will be made:")
        print("  - VLAN 1 → 100")
        print("  - VLAN 101 → 200") 
        print("  - VLAN 801 → 400 (with IP change)")
        print("  - VLAN 201 → 410")
        print("  - New firewall template will be applied")
        print("\nPress CTRL+C to cancel or wait 10 seconds to continue...")
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nMigration cancelled.")
            sys.exit(0)
    
    # Run migration
    migrator = CompleteVlanMigrator(args.network_id, args.dry_run)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()