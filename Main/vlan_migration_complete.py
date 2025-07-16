#!/usr/bin/env python3
"""
Complete VLAN Number Migration Script
=====================================

This script performs a complete VLAN migration by:
1. Taking full backup of all configurations
2. Removing all VLAN references (firewall, switches, MX ports)
3. Deleting old VLANs
4. Creating new VLANs with same settings
5. Restoring all references with new VLAN IDs

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
import copy

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
        """Initialize complete VLAN migrator"""
        self.network_id = network_id
        self.dry_run = dry_run
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        
        # Get network info
        self.network_info = self.get_network_info()
        self.org_id = self.network_info['organizationId']
        
        self.log(f"Complete VLAN Migrator initialized for {self.network_info['name']}")
        self.log(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)
    
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with error handling"""
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
            
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            self.log(f"API Error: {e}", "ERROR")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}", "ERROR")
            return None
    
    def get_network_info(self):
        """Get network information"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        return self.make_api_request(url)
    
    def take_complete_backup(self):
        """Take complete backup of all configurations"""
        self.log("\n" + "="*60)
        self.log("Taking complete configuration backup...")
        self.log("="*60)
        
        # Backup VLANs
        self.log("Backing up VLANs...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        self.backup_data['vlans'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['vlans'])} VLANs")
        
        # Backup firewall rules
        self.log("Backing up firewall rules...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        self.backup_data['firewall_rules'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['firewall_rules']['rules'])} firewall rules")
        
        # Backup group policies
        self.log("Backing up group policies...")
        url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        self.backup_data['group_policies'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['group_policies'])} group policies")
        
        # Backup switch ports
        self.log("Backing up switch configurations...")
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        devices = self.make_api_request(url)
        switches = [d for d in devices if d['model'].startswith('MS')]
        
        self.backup_data['switch_ports'] = {}
        for switch in switches:
            url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
            ports = self.make_api_request(url)
            self.backup_data['switch_ports'][switch['serial']] = {
                'device': switch,
                'ports': ports
            }
            self.log(f"  ✓ Backed up {len(ports)} ports for {switch['name']}")
        
        # Backup MX ports
        self.log("Backing up MX ports...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports"
        self.backup_data['mx_ports'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['mx_ports'])} MX ports")
        
        # Backup syslog
        self.log("Backing up syslog configuration...")
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        self.backup_data['syslog'] = self.make_api_request(url)
        
        # Save backup to file
        backup_filename = f"complete_vlan_backup_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2)
        self.log(f"\n✓ Complete backup saved to {backup_filename}")
    
    def clear_vlan_references(self):
        """Clear all VLAN references before deletion"""
        self.log("\n" + "="*60)
        self.log("Clearing VLAN references...")
        self.log("="*60)
        
        # Step 1: Clear firewall rules
        self.log("\nStep 1: Clearing firewall rules...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': []})
        if result:
            self.log("  ✓ Firewall rules cleared")
        
        # Step 2: Update switch ports to temporary VLAN
        self.log("\nStep 2: Moving switch ports to temporary VLANs...")
        temp_vlan_mapping = {
            1: 999,     # Data ports to temp VLAN
            101: 998,   # Voice to temp VLAN
            801: 997,   # IoT to temp VLAN
            201: 996    # Credit card to temp VLAN
        }
        
        # First create temporary VLANs
        for old_id, temp_id in temp_vlan_mapping.items():
            # Check if VLAN exists in backup
            if any(v['id'] == old_id for v in self.backup_data['vlans']):
                self.log(f"  Creating temporary VLAN {temp_id}...")
                vlan_data = {
                    'id': temp_id,
                    'name': f'TEMP_{old_id}',
                    'subnet': f'192.168.{temp_id-900}.0/24',
                    'applianceIp': f'192.168.{temp_id-900}.1'
                }
                url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
                self.make_api_request(url, method='POST', data=vlan_data)
        
        # Update switch ports
        for switch_serial, switch_data in self.backup_data['switch_ports'].items():
            switch_name = switch_data['device']['name']
            update_count = 0
            
            for port in switch_data['ports']:
                port_id = port['portId']
                updates = {}
                
                # Check access VLAN
                if port.get('vlan') in temp_vlan_mapping:
                    updates['vlan'] = temp_vlan_mapping[port['vlan']]
                
                # Check voice VLAN
                if port.get('voiceVlan') in temp_vlan_mapping:
                    updates['voiceVlan'] = temp_vlan_mapping[port['voiceVlan']]
                
                # Update allowed VLANs for trunk ports
                if port.get('type') == 'trunk' and port.get('allowedVlans'):
                    allowed = port['allowedVlans']
                    if allowed != 'all':
                        # Parse and update VLAN list properly
                        vlan_parts = []
                        for part in allowed.split(','):
                            part = part.strip()
                            if part in ['1', '101', '801', '201']:
                                # Replace with temp VLAN
                                vlan_parts.append(str(temp_vlan_mapping[int(part)]))
                            else:
                                # Keep other VLANs as-is
                                vlan_parts.append(part)
                        updates['allowedVlans'] = ','.join(vlan_parts)
                
                if updates:
                    url = f"{BASE_URL}/devices/{switch_serial}/switch/ports/{port_id}"
                    result = self.make_api_request(url, method='PUT', data=updates)
                    if result:
                        update_count += 1
            
            if update_count > 0:
                self.log(f"  ✓ Updated {update_count} ports on {switch_name}")
        
        # Step 3: Update MX ports
        self.log("\nStep 3: Updating MX ports to temporary VLANs...")
        mx_update_count = 0
        
        for port in self.backup_data['mx_ports']:
            port_num = port['number']
            updates = {}
            
            # Check native VLAN
            if port.get('vlan') in temp_vlan_mapping:
                updates['vlan'] = temp_vlan_mapping[port['vlan']]
            
            # Update allowed VLANs for trunk ports
            if port.get('type') == 'trunk' and port.get('allowedVlans'):
                allowed = port['allowedVlans']
                if allowed != 'all':
                    # Parse and update VLAN list properly
                    vlan_parts = []
                    for part in allowed.split(','):
                        part = part.strip()
                        if part in ['1', '101', '801', '201']:
                            # Replace with temp VLAN
                            vlan_parts.append(str(temp_vlan_mapping[int(part)]))
                        else:
                            # Keep other VLANs as-is
                            vlan_parts.append(part)
                    updates['allowedVlans'] = ','.join(vlan_parts)
            
            if updates:
                # Include all required fields
                update_data = {
                    'enabled': port.get('enabled', True),
                    'type': port.get('type', 'access'),
                    'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False),
                    **updates
                }
                
                url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                result = self.make_api_request(url, method='PUT', data=update_data)
                if result:
                    mx_update_count += 1
        
        if mx_update_count > 0:
            self.log(f"  ✓ Updated {mx_update_count} MX ports")
        
        return temp_vlan_mapping
    
    def migrate_vlans(self):
        """Migrate VLANs with new IDs"""
        self.log("\n" + "="*60)
        self.log("Migrating VLANs to new IDs...")
        self.log("="*60)
        
        migrated_vlans = {}
        
        for old_vlan in self.backup_data['vlans']:
            old_id = old_vlan['id']
            
            if old_id in VLAN_MAPPING:
                new_id = VLAN_MAPPING[old_id]
                
                if old_id != new_id:
                    self.log(f"\nMigrating VLAN {old_id} → {new_id}")
                    
                    # Delete old VLAN
                    self.log(f"  Deleting VLAN {old_id}...")
                    url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{old_id}"
                    result = self.make_api_request(url, method='DELETE')
                    
                    # Check if deletion was successful (DELETE returns empty response on success)
                    if not self.dry_run:
                        # Verify VLAN was deleted
                        time.sleep(1)
                        check_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
                        vlans = self.make_api_request(check_url)
                        if vlans and any(v['id'] == old_id for v in vlans):
                            self.log(f"  ✗ Failed to delete VLAN {old_id}", "ERROR")
                            continue
                    
                    time.sleep(2)
                    
                    # Create new VLAN with all settings
                    self.log(f"  Creating VLAN {new_id}...")
                    
                    # Check if IP changes are required for this VLAN
                    if new_id in IP_CHANGES:
                        self.log(f"    Applying IP changes for VLAN {new_id}")
                        ip_config = IP_CHANGES[new_id]
                        subnet = ip_config['new_subnet']
                        appliance_ip = ip_config['new_ip']
                    else:
                        # Keep original IP configuration
                        subnet = old_vlan.get('subnet')
                        appliance_ip = old_vlan.get('applianceIp')
                    
                    vlan_data = {
                        'id': new_id,
                        'name': old_vlan.get('name', f'VLAN {new_id}'),
                        'subnet': subnet,
                        'applianceIp': appliance_ip,
                        'groupPolicyId': old_vlan.get('groupPolicyId'),
                        'dhcpHandling': old_vlan.get('dhcpHandling', 'Run a DHCP server'),
                        'dhcpLeaseTime': old_vlan.get('dhcpLeaseTime', '1 day'),
                        'dhcpBootOptionsEnabled': old_vlan.get('dhcpBootOptionsEnabled', False),
                        'dnsNameservers': old_vlan.get('dnsNameservers', 'upstream_dns'),
                        'dhcpOptions': old_vlan.get('dhcpOptions', []),
                        'reservedIpRanges': old_vlan.get('reservedIpRanges', []),
                        'fixedIpAssignments': old_vlan.get('fixedIpAssignments', {}),
                        'vpnNatSubnet': old_vlan.get('vpnNatSubnet')
                    }
                    
                    # Remove None values
                    vlan_data = {k: v for k, v in vlan_data.items() if v is not None}
                    
                    url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
                    result = self.make_api_request(url, method='POST', data=vlan_data)
                    
                    if result:
                        self.log(f"  ✓ Created VLAN {new_id}")
                        migrated_vlans[old_id] = new_id
                    
                    time.sleep(1)
                else:
                    # VLAN ID doesn't change, but check for IP changes
                    if old_id == 800 and old_id in IP_CHANGES:
                        self.log(f"\nVLAN {old_id} - Updating IP configuration...")
                        
                        # Update VLAN 800 with new IP configuration
                        ip_config = IP_CHANGES[old_id]
                        vlan_data = {
                            'name': old_vlan.get('name', f'VLAN {old_id}'),
                            'subnet': ip_config['new_subnet'],
                            'applianceIp': ip_config['new_ip'],
                            'groupPolicyId': old_vlan.get('groupPolicyId'),
                            'dhcpHandling': old_vlan.get('dhcpHandling', 'Run a DHCP server'),
                            'dhcpLeaseTime': old_vlan.get('dhcpLeaseTime', '1 day'),
                            'dhcpBootOptionsEnabled': old_vlan.get('dhcpBootOptionsEnabled', False),
                            'dnsNameservers': old_vlan.get('dnsNameservers', 'upstream_dns'),
                            'dhcpOptions': old_vlan.get('dhcpOptions', []),
                            'reservedIpRanges': old_vlan.get('reservedIpRanges', []),
                            'fixedIpAssignments': old_vlan.get('fixedIpAssignments', {}),
                            'vpnNatSubnet': old_vlan.get('vpnNatSubnet')
                        }
                        
                        # Remove None values
                        vlan_data = {k: v for k, v in vlan_data.items() if v is not None}
                        
                        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{old_id}"
                        result = self.make_api_request(url, method='PUT', data=vlan_data)
                        
                        if result:
                            self.log(f"  ✓ Updated VLAN {old_id} IP configuration")
                        
                        time.sleep(1)
                    else:
                        # VLAN ID doesn't change and no IP changes needed
                        self.log(f"\nVLAN {old_id} - No change needed")
                    
                    migrated_vlans[old_id] = new_id
        
        return migrated_vlans
    
    def restore_configurations(self, temp_vlan_mapping):
        """Restore all configurations with new VLAN IDs"""
        self.log("\n" + "="*60)
        self.log("Restoring configurations with new VLAN IDs...")
        self.log("="*60)
        
        # Step 1: Update switch ports to new VLANs
        self.log("\nStep 1: Updating switch ports to new VLAN IDs...")
        
        for switch_serial, switch_data in self.backup_data['switch_ports'].items():
            switch_name = switch_data['device']['name']
            update_count = 0
            
            for port in switch_data['ports']:
                port_id = port['portId']
                updates = {}
                
                # Update access VLAN
                if port.get('vlan') in VLAN_MAPPING:
                    updates['vlan'] = VLAN_MAPPING[port['vlan']]
                
                # Update voice VLAN
                if port.get('voiceVlan') in VLAN_MAPPING:
                    updates['voiceVlan'] = VLAN_MAPPING[port['voiceVlan']]
                
                # Update allowed VLANs for trunk ports
                if port.get('type') == 'trunk' and port.get('allowedVlans'):
                    allowed = port['allowedVlans']
                    if allowed != 'all':
                        # Update VLAN IDs in allowed list
                        new_allowed = self.update_vlan_list(allowed)
                        if new_allowed != allowed:
                            updates['allowedVlans'] = new_allowed
                
                if updates:
                    url = f"{BASE_URL}/devices/{switch_serial}/switch/ports/{port_id}"
                    result = self.make_api_request(url, method='PUT', data=updates)
                    if result:
                        update_count += 1
            
            if update_count > 0:
                self.log(f"  ✓ Updated {update_count} ports on {switch_name}")
        
        # Step 2: Update MX ports
        self.log("\nStep 2: Updating MX ports to new VLAN IDs...")
        mx_update_count = 0
        
        for port in self.backup_data['mx_ports']:
            port_num = port['number']
            updates = {}
            
            # Update native VLAN
            if port.get('vlan') in VLAN_MAPPING:
                updates['vlan'] = VLAN_MAPPING[port['vlan']]
            
            # Update allowed VLANs for trunk ports
            if port.get('type') == 'trunk' and port.get('allowedVlans'):
                allowed = port['allowedVlans']
                if allowed != 'all':
                    new_allowed = self.update_vlan_list(allowed)
                    if new_allowed != allowed:
                        updates['allowedVlans'] = new_allowed
            
            if updates:
                # Include all required fields
                update_data = {
                    'enabled': port.get('enabled', True),
                    'type': port.get('type', 'access'),
                    'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False),
                    **updates
                }
                
                url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                result = self.make_api_request(url, method='PUT', data=update_data)
                if result:
                    mx_update_count += 1
        
        if mx_update_count > 0:
            self.log(f"  ✓ Updated {mx_update_count} MX ports")
        
        # Step 3: Apply firewall rules with new VLAN IDs
        self.log("\nStep 3: Applying NEO 07 firewall template...")
        
        # Load 54-rule NEO 07 firewall template (no default rule - Meraki will auto-add)
        neo07_template_file = 'neo07_54_rule_template_20250710_105817.json'
        try:
            with open(neo07_template_file, 'r') as f:
                neo07_template = json.load(f)
            template_rules = neo07_template['rules']
            self.log(f"  Loaded 54-rule NEO 07 firewall template: {len(template_rules)} rules (Meraki will auto-add default)")
        except FileNotFoundError:
            self.log(f"  Clean template file not found, falling back to original", "WARNING")
            # Fallback to original template file
            old_template_file = 'neo07_firewall_template_20250710.json'
            try:
                with open(old_template_file, 'r') as f:
                    neo07_template = json.load(f)
                template_rules = neo07_template['rules']
                self.log(f"  Loaded original NEO 07 firewall template: {len(template_rules)} rules")
            except FileNotFoundError:
                self.log(f"  No template files found, downloading current NEO 07 rules", "ERROR")
                neo07_id = 'L_3790904986339115847'
                url = f"{BASE_URL}/networks/{neo07_id}/appliance/firewall/l3FirewallRules"
                neo07_current = self.make_api_request(url)
                if neo07_current:
                    template_rules = neo07_current['rules']
                    self.log(f"  Downloaded current NEO 07 rules: {len(template_rules)} rules")
                else:
                    self.log("  Could not get NEO 07 rules, using original rules", "ERROR")
                    template_rules = self.backup_data['firewall_rules']['rules']
        
        # Convert clean NEO 07 rules for this store
        updated_rules = []
        
        for rule in template_rules:
            new_rule = copy.deepcopy(rule)
            
            # Convert NEO 07 IP ranges to this store's IP ranges
            if 'srcCidr' in new_rule and new_rule['srcCidr']:
                src = new_rule['srcCidr']
                # Convert NEO 07 IPs (10.24.38.x) to this store's test IPs (10.1.32.x)
                src = src.replace('10.24.38.', '10.1.32.')
                new_rule['srcCidr'] = src
            
            # Convert destination CIDR
            if 'destCidr' in new_rule and new_rule['destCidr']:
                dst = new_rule['destCidr']
                # Convert NEO 07 IPs (10.24.38.x) to this store's test IPs (10.1.32.x)
                dst = dst.replace('10.24.38.', '10.1.32.')
                new_rule['destCidr'] = dst
            
            updated_rules.append(new_rule)
        
        self.log(f"  Processed {len(updated_rules)} template rules (no policy object issues, Meraki will auto-add default)")
        
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': updated_rules})
        
        if result:
            self.log(f"  ✓ Applied {len(updated_rules)} NEO 07 firewall template rules")
        
        # Step 4: Delete temporary VLANs
        self.log("\nStep 4: Cleaning up temporary VLANs...")
        for old_id, temp_id in temp_vlan_mapping.items():
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{temp_id}"
            result = self.make_api_request(url, method='DELETE')
            if result:
                self.log(f"  ✓ Deleted temporary VLAN {temp_id}")
            time.sleep(1)
    
    def update_vlan_list(self, vlan_list_str):
        """Update a comma-separated VLAN list with new IDs"""
        parts = vlan_list_str.split(',')
        new_parts = []
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range
                start, end = part.split('-')
                start_id = int(start)
                end_id = int(end)
                
                # Update start and end if needed
                if start_id in VLAN_MAPPING:
                    start_id = VLAN_MAPPING[start_id]
                if end_id in VLAN_MAPPING:
                    end_id = VLAN_MAPPING[end_id]
                
                new_parts.append(f"{start_id}-{end_id}")
            else:
                # Single VLAN
                vlan_id = int(part)
                if vlan_id in VLAN_MAPPING:
                    vlan_id = VLAN_MAPPING[vlan_id]
                new_parts.append(str(vlan_id))
        
        return ','.join(new_parts)
    
    def generate_report(self):
        """Generate migration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
Complete VLAN Migration Report
==============================
Network: {self.network_info['name']} ({self.network_id})
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}
Mode: {'DRY RUN' if self.dry_run else 'LIVE'}

VLAN Mapping Applied:
"""
        for old_id, new_id in VLAN_MAPPING.items():
            if old_id != new_id:
                report += f"  VLAN {old_id} → VLAN {new_id}\n"
        
        report += "\nLog Entries:\n"
        report += "\n".join(self.log_entries)
        
        # Save report
        report_filename = f"complete_vlan_migration_report_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Report saved to {report_filename}")
    
    def run_migration(self):
        """Run the complete migration process"""
        try:
            # Step 1: Take complete backup
            self.take_complete_backup()
            
            # Step 2: Clear all VLAN references
            temp_vlan_mapping = self.clear_vlan_references()
            
            # Step 3: Migrate VLANs
            migrated_vlans = self.migrate_vlans()
            
            # Step 4: Restore configurations with new VLAN IDs
            self.restore_configurations(temp_vlan_mapping)
            
            # Generate report
            self.generate_report()
            
            self.log("\n" + "="*60)
            self.log("✅ COMPLETE VLAN MIGRATION FINISHED SUCCESSFULLY!")
            self.log("="*60)
            
            return True
            
        except Exception as e:
            self.log(f"Migration failed with error: {e}", "ERROR")
            self.generate_report()
            return False

def main():
    parser = argparse.ArgumentParser(description='Complete VLAN Number Migration Tool')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    print("🔧 Complete VLAN Number Migration Tool")
    print("=" * 60)
    print("This tool will migrate VLANs to the new numbering scheme:")
    print("  VLAN 1   → VLAN 100 (Data)")
    print("  VLAN 101 → VLAN 200 (Voice)")
    print("  VLAN 801 → VLAN 400 (IoT) + IP change")
    print("  VLAN 201 → VLAN 410 (Credit Card)")
    print("  VLAN 800 → VLAN 800 (Guest) + IP change only")
    print("=" * 60)
    
    if not args.dry_run:
        print("\n⚠️  WARNING: This will make permanent changes to your network!")
        print("The process will:")
        print("1. Take complete backup of all configurations")
        print("2. Move all ports to temporary VLANs")
        print("3. Delete and recreate VLANs with new IDs")
        print("4. Restore all configurations with new VLAN references")
        print("")
        
        if not os.getenv('SKIP_CONFIRMATION'):
            confirm = input("Are you sure you want to proceed? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Migration cancelled.")
                sys.exit(0)
        else:
            print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    # Run migration
    migrator = CompleteVlanMigrator(args.network_id, args.dry_run)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()