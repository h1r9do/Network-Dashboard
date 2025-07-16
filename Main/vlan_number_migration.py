#!/usr/bin/env python3
"""
VLAN Number Migration Script
============================

This script migrates VLANs to new numbering scheme while preserving
all settings including IP ranges, DHCP configuration, and reservations.

Migration Map:
- VLAN 1   → VLAN 100 (Data)
- VLAN 101 → VLAN 200 (Voice)
- VLAN 201 → VLAN 400 (Credit Card)
- VLAN 301 → VLAN 410 (Scanner)
- VLANs 300, 800-803 remain unchanged

Usage:
    python3 vlan_number_migration.py --network-id <network_id> [--dry-run]

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

# VLAN mapping
VLAN_MAPPING = {
    1: 100,    # Data
    101: 200,  # Voice
    201: 400,  # Credit Card
    301: 410,  # Scanner
    # These remain the same:
    300: 300,  # AP Mgmt
    800: 800,  # Guest
    801: 801,  # IOT
    802: 802,  # IoT Network
    803: 803,  # IoT Wireless
}

class VlanMigrator:
    def __init__(self, network_id, dry_run=False):
        """Initialize VLAN migrator"""
        self.network_id = network_id
        self.dry_run = dry_run
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        
        # Get network info
        self.network_info = self.get_network_info()
        self.org_id = self.network_info['organizationId']
        
        self.log(f"VLAN Migrator initialized for {self.network_info['name']}")
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
    
    def backup_configuration(self):
        """Backup all current configuration"""
        self.log("\nBacking up current configuration...")
        
        # Backup VLANs
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        self.backup_data['vlans'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['vlans'])} VLANs")
        
        # Backup firewall rules
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        self.backup_data['firewall_rules'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['firewall_rules']['rules'])} firewall rules")
        
        # Backup switch ports
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        devices = self.make_api_request(url)
        switches = [d for d in devices if d['model'].startswith('MS')]
        
        self.backup_data['switch_ports'] = {}
        for switch in switches:
            url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
            ports = self.make_api_request(url)
            self.backup_data['switch_ports'][switch['serial']] = ports
            self.log(f"  ✓ Backed up {len(ports)} ports for {switch['name']}")
        
        # Backup MX ports
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports"
        self.backup_data['mx_ports'] = self.make_api_request(url)
        self.log(f"  ✓ Backed up {len(self.backup_data['mx_ports'])} MX ports")
        
        # Save backup to file
        backup_filename = f"vlan_migration_backup_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2)
        self.log(f"\n✓ Backup saved to {backup_filename}")
    
    def migrate_single_vlan(self, old_vlan_data, new_vlan_id):
        """Migrate a single VLAN to new ID"""
        old_id = old_vlan_data['id']
        self.log(f"\nMigrating VLAN {old_id} → {new_vlan_id}")
        
        # Store VLAN configuration
        vlan_config = {
            'id': new_vlan_id,
            'name': old_vlan_data.get('name', f'VLAN {new_vlan_id}'),
            'subnet': old_vlan_data.get('subnet'),
            'applianceIp': old_vlan_data.get('applianceIp'),
            'groupPolicyId': old_vlan_data.get('groupPolicyId'),
            'dhcpHandling': old_vlan_data.get('dhcpHandling', 'Run a DHCP server'),
            'dhcpLeaseTime': old_vlan_data.get('dhcpLeaseTime', '1 day'),
            'dhcpBootOptionsEnabled': old_vlan_data.get('dhcpBootOptionsEnabled', False),
            'dnsNameservers': old_vlan_data.get('dnsNameservers', 'upstream_dns'),
            'dhcpOptions': old_vlan_data.get('dhcpOptions', []),
            'reservedIpRanges': old_vlan_data.get('reservedIpRanges', []),
            'fixedIpAssignments': old_vlan_data.get('fixedIpAssignments', {}),
            'vpnNatSubnet': old_vlan_data.get('vpnNatSubnet')
        }
        
        # Log what we're preserving
        self.log(f"  Preserving configuration:")
        self.log(f"    - Name: {vlan_config['name']}")
        self.log(f"    - Subnet: {vlan_config['subnet']}")
        self.log(f"    - DHCP Mode: {vlan_config['dhcpHandling']}")
        
        if vlan_config['dhcpOptions']:
            self.log(f"    - DHCP Options: {len(vlan_config['dhcpOptions'])} configured")
        
        if vlan_config['fixedIpAssignments']:
            self.log(f"    - Fixed IPs: {len(vlan_config['fixedIpAssignments'])} reservations")
        
        # Delete old VLAN
        self.log(f"  Deleting VLAN {old_id}...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{old_id}"
        result = self.make_api_request(url, method='DELETE')
        
        if result is None and not self.dry_run:
            self.log(f"  ✗ Failed to delete VLAN {old_id}", "ERROR")
            return False
        
        time.sleep(2)  # Wait for deletion to complete
        
        # Create new VLAN with same settings
        self.log(f"  Creating VLAN {new_vlan_id}...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        
        # Remove None values and clean up
        vlan_config = {k: v for k, v in vlan_config.items() if v is not None}
        
        result = self.make_api_request(url, method='POST', data=vlan_config)
        
        if result and not self.dry_run:
            self.log(f"  ✓ Created VLAN {new_vlan_id} with all settings preserved")
            return True
        elif self.dry_run:
            self.log(f"  ✓ Would create VLAN {new_vlan_id}", "DRY_RUN")
            return True
        else:
            self.log(f"  ✗ Failed to create VLAN {new_vlan_id}", "ERROR")
            return False
    
    def migrate_vlans(self):
        """Migrate all VLANs that need new IDs"""
        self.log("\n" + "="*60)
        self.log("Starting VLAN migration...")
        self.log("="*60)
        
        success_count = 0
        
        # Process VLANs that need migration
        for old_vlan in self.backup_data['vlans']:
            old_id = old_vlan['id']
            
            if old_id in VLAN_MAPPING:
                new_id = VLAN_MAPPING[old_id]
                
                if old_id != new_id:
                    # This VLAN needs migration
                    if self.migrate_single_vlan(old_vlan, new_id):
                        success_count += 1
                    else:
                        self.log(f"Failed to migrate VLAN {old_id}", "ERROR")
                        if not self.dry_run:
                            return False
                else:
                    # VLAN ID doesn't change
                    self.log(f"\nVLAN {old_id} - No change needed")
                    success_count += 1
        
        self.log(f"\n✓ Successfully migrated {success_count} VLANs")
        return True
    
    def update_firewall_rules(self):
        """Update firewall rules with new VLAN references"""
        self.log("\n" + "="*60)
        self.log("Updating firewall rules...")
        self.log("="*60)
        
        # Get NEO 07 firewall template (or use backed up rules)
        original_rules = self.backup_data['firewall_rules']['rules']
        
        # Update VLAN references in rules
        updated_rules = []
        for rule in original_rules:
            new_rule = copy.deepcopy(rule)
            
            # Update source VLAN references
            if 'srcCidr' in new_rule:
                src = new_rule['srcCidr']
                for old_id, new_id in VLAN_MAPPING.items():
                    if old_id != new_id:
                        src = src.replace(f'VLAN({old_id}).', f'VLAN({new_id}).')
                new_rule['srcCidr'] = src
            
            # Update destination VLAN references
            if 'destCidr' in new_rule:
                dst = new_rule['destCidr']
                for old_id, new_id in VLAN_MAPPING.items():
                    if old_id != new_id:
                        dst = dst.replace(f'VLAN({old_id}).', f'VLAN({new_id}).')
                new_rule['destCidr'] = dst
            
            updated_rules.append(new_rule)
        
        # Apply updated rules
        self.log(f"  Applying {len(updated_rules)} updated firewall rules...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        data = {'rules': updated_rules}
        
        result = self.make_api_request(url, method='PUT', data=data)
        
        if result:
            self.log(f"  ✓ Successfully updated firewall rules")
            return True
        else:
            self.log(f"  ✗ Failed to update firewall rules", "ERROR")
            return False
    
    def update_switch_ports(self):
        """Update switch port VLAN assignments"""
        self.log("\n" + "="*60)
        self.log("Updating switch port configurations...")
        self.log("="*60)
        
        for switch_serial, ports in self.backup_data['switch_ports'].items():
            self.log(f"\nUpdating switch {switch_serial}...")
            updated_count = 0
            
            for port in ports:
                port_id = port['portId']
                needs_update = False
                updates = {}
                
                # Check access VLAN
                if 'vlan' in port and port['vlan'] in VLAN_MAPPING:
                    old_vlan = port['vlan']
                    new_vlan = VLAN_MAPPING[old_vlan]
                    if old_vlan != new_vlan:
                        updates['vlan'] = new_vlan
                        needs_update = True
                
                # Check voice VLAN
                if 'voiceVlan' in port and port['voiceVlan'] in VLAN_MAPPING:
                    old_voice = port['voiceVlan']
                    new_voice = VLAN_MAPPING[old_voice]
                    if old_voice != new_voice:
                        updates['voiceVlan'] = new_voice
                        needs_update = True
                
                # Check allowed VLANs for trunk ports
                if port.get('type') == 'trunk' and 'allowedVlans' in port:
                    allowed = port['allowedVlans']
                    if allowed != 'all':
                        # Parse and update VLAN list
                        new_allowed = self.update_vlan_list(allowed)
                        if new_allowed != allowed:
                            updates['allowedVlans'] = new_allowed
                            needs_update = True
                
                # Apply updates if needed
                if needs_update:
                    self.log(f"  Updating port {port_id}: {updates}")
                    url = f"{BASE_URL}/devices/{switch_serial}/switch/ports/{port_id}"
                    result = self.make_api_request(url, method='PUT', data=updates)
                    if result:
                        updated_count += 1
            
            self.log(f"  ✓ Updated {updated_count} ports on this switch")
        
        return True
    
    def update_mx_ports(self):
        """Update MX port VLAN assignments"""
        self.log("\n" + "="*60)
        self.log("Updating MX port configurations...")
        self.log("="*60)
        
        updated_count = 0
        
        for port in self.backup_data['mx_ports']:
            port_num = port['number']
            needs_update = False
            updates = {}
            
            # Check VLAN (native for trunk, access for access)
            if 'vlan' in port and port['vlan'] in VLAN_MAPPING:
                old_vlan = port['vlan']
                new_vlan = VLAN_MAPPING[old_vlan]
                if old_vlan != new_vlan:
                    updates['vlan'] = new_vlan
                    needs_update = True
            
            # Check allowed VLANs for trunk ports
            if port.get('type') == 'trunk' and 'allowedVlans' in port:
                allowed = port['allowedVlans']
                if allowed != 'all':
                    new_allowed = self.update_vlan_list(allowed)
                    if new_allowed != allowed:
                        updates['allowedVlans'] = new_allowed
                        needs_update = True
            
            # Apply updates if needed
            if needs_update:
                self.log(f"  Updating port {port_num}: {updates}")
                url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports/{port_num}"
                
                # Include all required fields for update
                update_data = {
                    'enabled': port.get('enabled', True),
                    'type': port.get('type', 'access'),
                    'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False),
                    **updates
                }
                
                result = self.make_api_request(url, method='PUT', data=update_data)
                if result:
                    updated_count += 1
        
        self.log(f"  ✓ Updated {updated_count} MX ports")
        return True
    
    def update_vlan_list(self, vlan_list_str):
        """Update a comma-separated VLAN list with new IDs"""
        # Parse VLAN list (e.g., "1,101,201,300-301,800-803")
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
VLAN Migration Report
====================
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
        report_filename = f"vlan_migration_report_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Report saved to {report_filename}")
    
    def run_migration(self):
        """Run the complete migration process"""
        try:
            # Step 1: Backup configuration
            self.backup_configuration()
            
            # Step 2: Clear firewall rules (to allow VLAN deletion)
            self.log("\nClearing firewall rules to allow VLAN deletion...")
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
            clear_data = {'rules': []}
            result = self.make_api_request(url, method='PUT', data=clear_data)
            if result:
                self.log("  ✓ Firewall rules cleared")
            else:
                self.log("  ✗ Failed to clear firewall rules", "ERROR")
                return False
            
            # Step 3: Migrate VLANs
            if not self.migrate_vlans():
                self.log("VLAN migration failed!", "ERROR")
                return False
            
            # Step 4: Update and apply firewall rules
            if not self.update_firewall_rules():
                self.log("Firewall rule update failed!", "ERROR")
                return False
            
            # Step 4: Update switch ports
            if not self.update_switch_ports():
                self.log("Switch port update failed!", "ERROR")
                return False
            
            # Step 5: Update MX ports
            if not self.update_mx_ports():
                self.log("MX port update failed!", "ERROR")
                return False
            
            # Generate report
            self.generate_report()
            
            self.log("\n" + "="*60)
            self.log("✅ VLAN MIGRATION COMPLETED SUCCESSFULLY!")
            self.log("="*60)
            
            return True
            
        except Exception as e:
            self.log(f"Migration failed with error: {e}", "ERROR")
            self.generate_report()
            return False

def main():
    parser = argparse.ArgumentParser(description='VLAN Number Migration Tool')
    parser.add_argument('--network-id', required=True, help='Target network ID')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    print("🔧 VLAN Number Migration Tool")
    print("=" * 60)
    print("This tool will migrate VLANs to the new numbering scheme:")
    print("  VLAN 1   → VLAN 100 (Data)")
    print("  VLAN 101 → VLAN 200 (Voice)")
    print("  VLAN 201 → VLAN 400 (Credit Card)")
    print("  VLAN 301 → VLAN 410 (Scanner)")
    print("=" * 60)
    
    if not args.dry_run:
        print("\n⚠️  WARNING: This will make permanent changes to your network!")
        if not os.getenv('SKIP_CONFIRMATION'):
            confirm = input("Are you sure you want to proceed? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Migration cancelled.")
                sys.exit(0)
        else:
            print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    # Run migration
    migrator = VlanMigrator(args.network_id, args.dry_run)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()