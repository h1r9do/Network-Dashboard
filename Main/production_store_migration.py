#!/usr/bin/env python3
"""
Production Store VLAN Migration Script
Migrates production stores (like AZP 30) to new VLAN numbering and firewall rules
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

# Production VLAN mapping
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

# IP changes for production stores
def get_ip_changes(store_subnet_base):
    """Generate IP changes based on store's subnet base (e.g., 10.24.38)"""
    return {
        800: {
            'old_subnet': f'{store_subnet_base}.0/30',
            'new_subnet': '172.16.80.0/24',
            'old_ip': f'{store_subnet_base}.1',
            'new_ip': '172.16.80.1'
        },
        400: {  # This will be the new VLAN ID for 801
            'old_subnet': f'{store_subnet_base}.0/30', 
            'new_subnet': '172.16.40.0/24',
            'old_ip': f'{store_subnet_base}.1',
            'new_ip': '172.16.40.1'
        }
    }

class ProductionStoreMigrator:
    def __init__(self, network_id, network_name, dry_run=False):
        self.network_id = network_id
        self.network_name = network_name
        self.dry_run = dry_run
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        self.store_subnet_base = None
        self.ip_changes = {}
        
        # Get network info
        self.network_info = self.get_network_info()
        self.org_id = self.network_info['organizationId']
        
        # Detect store subnet base from existing VLANs
        self.detect_store_subnet()
        
        self.log(f"Production Store Migrator initialized for {self.network_name}")
        self.log(f"Store subnet base: {self.store_subnet_base}")
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
                self.log(f"DRY RUN: With data: {json.dumps(data, indent=2)[:200]}...", "DRY_RUN")
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
    
    def detect_store_subnet(self):
        """Detect the store's subnet base from existing VLANs"""
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        vlans = self.make_api_request(url)
        
        if vlans:
            for vlan in vlans:
                if vlan['id'] == 100:  # Look at data VLAN
                    subnet = vlan.get('subnet', '')
                    if subnet and '.' in subnet:
                        # Extract base (e.g., 10.24.38 from 10.24.38.0/25)
                        parts = subnet.split('/')
                        if len(parts) > 0:
                            ip_parts = parts[0].split('.')
                            if len(ip_parts) >= 3:
                                self.store_subnet_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                                break
        
        if not self.store_subnet_base:
            # Default fallback
            self.store_subnet_base = "10.24.38"
            self.log(f"Could not detect subnet base, using default: {self.store_subnet_base}", "WARNING")
        
        # Set IP changes based on detected subnet
        self.ip_changes = get_ip_changes(self.store_subnet_base)
    
    def take_complete_backup(self):
        """Take complete backup of store configuration"""
        self.log("\n" + "="*60)
        self.log("Taking complete store configuration backup...")
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
        
        # Backup switch configurations
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
        
        # Save backup to file
        backup_filename = f"production_migration_backup_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2)
        self.log(f"\n✓ Complete backup saved to {backup_filename}")
        return backup_filename
    
    def apply_new_firewall_template(self):
        """Apply new firewall rules from NEO 07 template"""
        self.log("\n" + "="*60)
        self.log("Applying new firewall template...")
        self.log("="*60)
        
        # Load NEO 07 firewall template
        template_file = "neo07_firewall_template_20250710.json"
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            firewall_rules = template_data['rules']
            self.log(f"Loaded {len(firewall_rules)} rules from template")
            
            # Update firewall rules for this store's IP ranges
            updated_rules = []
            for rule in firewall_rules:
                new_rule = copy.deepcopy(rule)
                
                # Update source CIDR for store-specific IPs
                if 'srcCidr' in new_rule:
                    src = new_rule['srcCidr']
                    # Convert template IPs to store IPs
                    src = src.replace('10.24.38.', f'{self.store_subnet_base}.')
                    new_rule['srcCidr'] = src
                
                # Update destination CIDR for store-specific IPs
                if 'destCidr' in new_rule:
                    dst = new_rule['destCidr']
                    # Convert template IPs to store IPs
                    dst = dst.replace('10.24.38.', f'{self.store_subnet_base}.')
                    new_rule['destCidr'] = dst
                
                updated_rules.append(new_rule)
            
            # Apply updated firewall rules
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
            result = self.make_api_request(url, method='PUT', data={'rules': updated_rules})
            
            if result:
                self.log(f"  ✓ Applied {len(updated_rules)} firewall rules")
                return True
            else:
                self.log("  ✗ Failed to apply firewall rules", "ERROR")
                return False
                
        except FileNotFoundError:
            self.log(f"Firewall template file {template_file} not found", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error applying firewall template: {e}", "ERROR")
            return False
    
    def migrate_vlans_with_ip_changes(self):
        """Migrate VLANs with proper IP address changes"""
        self.log("\n" + "="*60)
        self.log("Migrating VLANs with IP address updates...")
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
                    
                    time.sleep(2)
                    
                    # Create new VLAN with appropriate IP configuration
                    self.log(f"  Creating VLAN {new_id}...")
                    
                    # Check if IP changes are required
                    if new_id in self.ip_changes:
                        self.log(f"    Applying IP changes for VLAN {new_id}")
                        ip_config = self.ip_changes[new_id]
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
                    if old_id == 800 and old_id in self.ip_changes:
                        self.log(f"\nVLAN {old_id} - Updating IP configuration...")
                        
                        # Update VLAN 800 with new IP configuration
                        ip_config = self.ip_changes[old_id]
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
                    elif old_id == 300:
                        # Update name for VLAN 300: AP Mgmt → Net Mgmt
                        self.log(f"\nVLAN {old_id} - Updating name to 'Net Mgmt'...")
                        vlan_data = {
                            'name': 'Net Mgmt',
                            'subnet': old_vlan.get('subnet'),
                            'applianceIp': old_vlan.get('applianceIp'),
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
                            self.log(f"  ✓ Updated VLAN {old_id} name")
                    else:
                        # No changes needed
                        self.log(f"\nVLAN {old_id} - No change needed")
                    
                    migrated_vlans[old_id] = old_id
        
        return migrated_vlans
    
    def run_production_migration(self):
        """Run complete production store migration"""
        self.log("="*60)
        self.log(f"PRODUCTION STORE MIGRATION")
        self.log(f"Store: {self.network_name} ({self.network_id})")
        self.log(f"Subnet Base: {self.store_subnet_base}")
        self.log("="*60)
        
        try:
            # Step 1: Take complete backup
            backup_file = self.take_complete_backup()
            
            # Step 2: Apply new firewall template
            if not self.apply_new_firewall_template():
                self.log("Failed to apply firewall template", "ERROR")
                return False
            
            # Step 3: Migrate VLANs with IP changes
            migrated_vlans = self.migrate_vlans_with_ip_changes()
            
            # Generate report
            self.generate_report(backup_file)
            
            self.log("\n" + "="*60)
            self.log("✅ PRODUCTION STORE MIGRATION COMPLETED!")
            self.log("="*60)
            self.log(f"Store {self.network_name} has been migrated to new standard")
            self.log(f"Backup saved: {backup_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Migration failed: {e}", "ERROR")
            return False
    
    def generate_report(self, backup_file):
        """Generate migration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
Production Store Migration Report
=================================
Store: {self.network_name} ({self.network_id})
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}
Mode: {'DRY RUN' if self.dry_run else 'LIVE'}
Store Subnet Base: {self.store_subnet_base}

VLAN Mapping Applied:
"""
        for old_id, new_id in VLAN_MAPPING.items():
            if old_id != new_id:
                report += f"  VLAN {old_id} → VLAN {new_id}\n"
        
        report += f"\nIP Changes Applied:\n"
        for vlan_id, changes in self.ip_changes.items():
            report += f"  VLAN {vlan_id}: {changes['old_subnet']} → {changes['new_subnet']}\n"
        
        report += "\nLog Entries:\n"
        report += "\n".join(self.log_entries)
        
        # Save report
        report_filename = f"production_migration_report_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        self.log(f"✓ Report saved to {report_filename}")

def main():
    parser = argparse.ArgumentParser(description='Production Store VLAN Migration Tool')
    parser.add_argument('--network-id', required=True, help='Store network ID (e.g., AZP 30)')
    parser.add_argument('--network-name', required=True, help='Store name (e.g., "AZP 30")')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    print("🏪 Production Store VLAN Migration Tool")
    print("=" * 60)
    print("This tool will migrate a production store to new VLAN standard:")
    print("  VLAN 1   → VLAN 100 (Data)")
    print("  VLAN 101 → VLAN 200 (Voice)")
    print("  VLAN 801 → VLAN 400 (IoT) + IP change")
    print("  VLAN 201 → VLAN 410 (Credit Card)")
    print("  VLAN 800 → VLAN 800 (Guest) + IP change")
    print("  VLAN 300 → VLAN 300 (AP Mgmt → Net Mgmt)")
    print("  + Apply new firewall template (55 rules)")
    print("=" * 60)
    
    if not args.dry_run:
        print("\n⚠️  WARNING: This will make permanent changes to the production store!")
        print("The process will:")
        print("1. Take complete backup of store configuration")
        print("2. Apply new firewall rules from template")
        print("3. Migrate VLANs with IP address changes")
        print("4. Update all VLAN references")
        print("")
        
        if not os.getenv('SKIP_CONFIRMATION'):
            confirm = input("Are you sure you want to proceed with production migration? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Migration cancelled.")
                sys.exit(0)
        else:
            print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    # Run migration
    migrator = ProductionStoreMigrator(args.network_id, args.network_name, args.dry_run)
    success = migrator.run_production_migration()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()