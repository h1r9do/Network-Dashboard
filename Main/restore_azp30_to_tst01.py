#!/usr/bin/env python3
"""
Comprehensive AZP 30 to TST 01 Restore Script
Restores complete AZP 30 configuration to TST 01 with test IP ranges
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

class ComprehensiveRestore:
    def __init__(self, source_config_file, target_network_id, target_name):
        self.source_config_file = source_config_file
        self.target_network_id = target_network_id
        self.target_name = target_name
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        self.source_data = {}
        
        self.log(f"Comprehensive Restore initialized")
        self.log(f"Source: {source_config_file}")
        self.log(f"Target: {target_name} ({target_network_id})")
    
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
    
    def load_source_configuration(self):
        """Load AZP 30 configuration from file"""
        self.log("Loading AZP 30 source configuration...")
        
        try:
            with open(self.source_config_file, 'r') as f:
                self.source_data = json.load(f)
            
            # Log what we found
            if 'vlans' in self.source_data:
                self.log(f"  Found {len(self.source_data['vlans'])} VLANs")
            if 'firewall_rules' in self.source_data:
                self.log(f"  Found {len(self.source_data['firewall_rules']['rules'])} firewall rules")
            if 'mx_ports' in self.source_data:
                self.log(f"  Found {len(self.source_data['mx_ports'])} MX ports")
            if 'switch_ports' in self.source_data:
                self.log(f"  Found switch configurations for {len(self.source_data['switch_ports'])} switches")
            if 'group_policies' in self.source_data:
                self.log(f"  Found {len(self.source_data['group_policies'])} group policies")
            
            return True
            
        except FileNotFoundError:
            self.log(f"Source configuration file not found: {self.source_config_file}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error loading source configuration: {e}", "ERROR")
            return False
    
    def backup_target_configuration(self):
        """Backup current TST 01 configuration"""
        self.log("\nBacking up current TST 01 configuration...")
        
        # Backup VLANs
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
        self.backup_data['vlans'] = self.make_api_request(url)
        if self.backup_data['vlans']:
            self.log(f"  ✓ Backed up {len(self.backup_data['vlans'])} VLANs")
        
        # Backup firewall rules
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        self.backup_data['firewall_rules'] = self.make_api_request(url)
        if self.backup_data['firewall_rules']:
            self.log(f"  ✓ Backed up {len(self.backup_data['firewall_rules']['rules'])} firewall rules")
        
        # Backup MX ports
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/ports"
        self.backup_data['mx_ports'] = self.make_api_request(url)
        if self.backup_data['mx_ports']:
            self.log(f"  ✓ Backed up {len(self.backup_data['mx_ports'])} MX ports")
        
        # Backup switch configurations
        url = f"{BASE_URL}/networks/{self.target_network_id}/devices"
        devices = self.make_api_request(url)
        if devices:
            switches = [d for d in devices if d['model'].startswith('MS')]
            self.backup_data['switch_ports'] = {}
            
            for switch in switches:
                url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
                ports = self.make_api_request(url)
                if ports:
                    self.backup_data['switch_ports'][switch['serial']] = {
                        'device': switch,
                        'ports': ports
                    }
                    self.log(f"  ✓ Backed up {len(ports)} ports for {switch['name']}")
        
        # Backup group policies
        url = f"{BASE_URL}/networks/{self.target_network_id}/groupPolicies"
        self.backup_data['group_policies'] = self.make_api_request(url)
        if self.backup_data['group_policies']:
            self.log(f"  ✓ Backed up {len(self.backup_data['group_policies'])} group policies")
        
        # Save backup
        backup_filename = f"tst01_backup_before_azp30_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2)
        self.log(f"  ✓ Complete backup saved to {backup_filename}")
        return backup_filename
    
    def convert_ip_ranges(self, ip_string, is_subnet=False):
        """Convert AZP 30 IP ranges to TST 01 test ranges"""
        if not ip_string:
            return ip_string
        
        # Convert AZP 30 production IPs to TST 01 test IPs
        converted = ip_string
        
        # Convert 10.24.x.x to 10.255.255.x (AZP 30 base)
        converted = converted.replace('10.24.38.', '10.255.255.')
        converted = converted.replace('10.24.39.', '10.255.255.')
        
        # Handle other potential store IP ranges
        converted = converted.replace('10.25.', '10.255.255.')
        converted = converted.replace('10.26.', '10.255.255.')
        
        return converted
    
    def clear_target_configuration(self):
        """Clear existing TST 01 configuration"""
        self.log("\nClearing existing TST 01 configuration...")
        
        # Clear firewall rules first
        self.log("  Clearing firewall rules...")
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': []})
        if result:
            self.log("    ✓ Firewall rules cleared")
        
        # Delete VLANs (except management)
        self.log("  Clearing VLANs...")
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
        current_vlans = self.make_api_request(url)
        
        if current_vlans:
            for vlan in current_vlans:
                if vlan['id'] != 900:  # Keep management VLAN
                    self.log(f"    Deleting VLAN {vlan['id']}...")
                    delete_url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans/{vlan['id']}"
                    self.make_api_request(delete_url, method='DELETE')
                    time.sleep(1)
    
    def restore_vlans(self):
        """Restore VLANs from AZP 30 with test IP ranges"""
        self.log("\nRestoring VLANs from AZP 30...")
        
        if 'vlans' not in self.source_data:
            self.log("  No VLAN data found in source configuration", "WARNING")
            return False
        
        created_count = 0
        for vlan in self.source_data['vlans']:
            if vlan['id'] == 900:  # Skip management VLAN
                continue
            
            vlan_data = copy.deepcopy(vlan)
            
            # Convert IP ranges to test ranges
            if vlan_data.get('subnet'):
                vlan_data['subnet'] = self.convert_ip_ranges(vlan_data['subnet'])
            
            if vlan_data.get('applianceIp'):
                vlan_data['applianceIp'] = self.convert_ip_ranges(vlan_data['applianceIp'])
            
            # Remove fields that shouldn't be copied
            fields_to_remove = ['interfaceId', 'networkId']
            for field in fields_to_remove:
                if field in vlan_data:
                    del vlan_data[field]
            
            self.log(f"  Creating VLAN {vlan_data['id']}: {vlan_data['name']}")
            url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/vlans"
            result = self.make_api_request(url, method='POST', data=vlan_data)
            
            if result:
                created_count += 1
                self.log(f"    ✓ Created VLAN {vlan_data['id']}")
            else:
                self.log(f"    ✗ Failed to create VLAN {vlan_data['id']}", "ERROR")
            
            time.sleep(1)
        
        self.log(f"  ✓ Created {created_count} VLANs")
        return True
    
    def restore_firewall_rules(self):
        """Restore firewall rules from AZP 30 with converted IPs and filtered VLANs"""
        self.log("\nRestoring firewall rules from AZP 30...")
        
        if 'firewall_rules' not in self.source_data:
            self.log("  No firewall rules found in source configuration", "WARNING")
            return False
        
        # Load the filtered firewall rules from the separate file
        try:
            with open('azp_30_original_firewall_rules.json', 'r') as f:
                fw_data = json.load(f)
            firewall_rules = fw_data['rules']
            self.log(f"  Loaded {len(firewall_rules)} firewall rules from AZP 30")
        except FileNotFoundError:
            # Fall back to source data if separate file not found
            firewall_rules = self.source_data['firewall_rules']['rules']
            self.log(f"  Using {len(firewall_rules)} firewall rules from source data")
        
        # TST 01 VLANs that exist
        tst01_vlans = [1, 101, 201, 300, 301, 800, 801, 803, 900]
        
        # Process rules
        filtered_rules = []
        skipped_count = 0
        
        for rule in firewall_rules:
            new_rule = copy.deepcopy(rule)
            
            # Convert IP ranges for source CIDR
            if 'srcCidr' in new_rule and new_rule['srcCidr']:
                src = new_rule['srcCidr']
                src = self.convert_ip_ranges(src)
                src = self.filter_vlan_references(src, tst01_vlans)
                src = self.simplify_policy_references(src)
                new_rule['srcCidr'] = src
            
            # Convert IP ranges for destination CIDR
            if 'destCidr' in new_rule and new_rule['destCidr']:
                dst = new_rule['destCidr']
                dst = self.convert_ip_ranges(dst)
                dst = self.filter_vlan_references(dst, tst01_vlans)
                dst = self.simplify_policy_references(dst)
                new_rule['destCidr'] = dst
            
            # Skip rules with unresolved policy references
            src_check = str(new_rule.get('srcCidr', ''))
            dst_check = str(new_rule.get('destCidr', ''))
            if 'GRP(' in src_check + dst_check or 'OBJ(' in src_check + dst_check:
                self.log(f"    Skipping rule with policy objects: {rule.get('comment', 'No comment')}")
                skipped_count += 1
                continue
            
            filtered_rules.append(new_rule)
        
        self.log(f"  Processed {len(filtered_rules)} rules ({skipped_count} skipped)")
        
        # Apply firewall rules
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': filtered_rules})
        
        if result:
            self.log(f"  ✓ Applied {len(filtered_rules)} firewall rules")
            return True
        else:
            self.log("  ✗ Failed to apply firewall rules", "ERROR")
            return False
    
    def filter_vlan_references(self, cidr_string, valid_vlans):
        """Filter out VLAN references that don't exist in TST 01"""
        if not cidr_string or cidr_string == "Any":
            return cidr_string
        
        import re
        parts = cidr_string.split(',')
        valid_parts = []
        
        for part in parts:
            part = part.strip()
            vlan_match = re.search(r'VLAN\((\d+)\)', part)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
                if vlan_id in valid_vlans:
                    valid_parts.append(part)
            else:
                valid_parts.append(part)
        
        return ','.join(valid_parts) if valid_parts else "Any"
    
    def simplify_policy_references(self, cidr_string):
        """Replace policy object references with simplified equivalents"""
        if not cidr_string or cidr_string == "Any":
            return cidr_string
        
        replacements = {
            'GRP(3790904986339115076)': '13.107.64.0/18,52.112.0.0/14',
            'GRP(3790904986339115077)': '10.0.0.0/8',
            'GRP(3790904986339115118)': '199.71.106.0/20',
            'OBJ(3790904986339115064)': '74.125.224.0/19',
            'OBJ(3790904986339115065)': '173.194.0.0/16',
            'OBJ(3790904986339115066)': '108.177.8.0/21',
            'OBJ(3790904986339115067)': '142.250.0.0/15',
            'OBJ(3790904986339115074)': 'time.windows.com',
        }
        
        result = cidr_string
        for obj_ref, replacement in replacements.items():
            result = result.replace(obj_ref, replacement)
        
        return result
    
    def restore_mx_ports(self):
        """Restore MX port configurations from AZP 30"""
        self.log("\nRestoring MX port configurations from AZP 30...")
        
        if 'mx_ports' not in self.source_data:
            self.log("  No MX port data found in source configuration", "WARNING")
            return False
        
        updated_count = 0
        for port in self.source_data['mx_ports']:
            port_num = port['number']
            
            # Check if port is disabled and skip VLAN configuration
            port_enabled = port.get('enabled', True)
            
            # Prepare port configuration
            port_config = {
                'enabled': port_enabled,
                'type': port.get('type', 'access'),
                'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False)
            }
            
            # Only add VLAN configuration if port is enabled
            if port_enabled:
                if port.get('vlan'):
                    port_config['vlan'] = port['vlan']
                
                # Add allowed VLANs for trunk ports if present
                if port.get('allowedVlans'):
                    port_config['allowedVlans'] = port['allowedVlans']
            
            self.log(f"  Configuring MX port {port_num} (enabled: {port_enabled})")
            url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/ports/{port_num}"
            result = self.make_api_request(url, method='PUT', data=port_config)
            
            if result:
                updated_count += 1
                self.log(f"    ✓ Configured MX port {port_num}")
            else:
                self.log(f"    ✗ Failed to configure MX port {port_num}", "ERROR")
            
            time.sleep(1)
        
        self.log(f"  ✓ Configured {updated_count} MX ports")
        return True
    
    def restore_switch_ports(self):
        """Restore switch port configurations from AZP 30"""
        self.log("\nRestoring switch port configurations from AZP 30...")
        
        if 'switch_ports' not in self.source_data:
            self.log("  No switch port data found in source configuration", "WARNING")
            return False
        
        # Get current TST 01 switches
        url = f"{BASE_URL}/networks/{self.target_network_id}/devices"
        devices = self.make_api_request(url)
        if not devices:
            self.log("  Could not get TST 01 devices", "ERROR")
            return False
        
        tst01_switches = [d for d in devices if d['model'].startswith('MS')]
        self.log(f"  Found {len(tst01_switches)} switches in TST 01")
        
        # Map TST 01 switches to AZP 30 switch configs (by position/index)
        azp30_switch_serials = list(self.source_data['switch_ports'].keys())
        
        for i, tst01_switch in enumerate(tst01_switches):
            if i < len(azp30_switch_serials):
                azp30_serial = azp30_switch_serials[i]
                azp30_ports = self.source_data['switch_ports'][azp30_serial]
                
                self.log(f"  Applying AZP 30 switch config to {tst01_switch['name']}")
                
                updated_count = 0
                for port_config in azp30_ports:
                    port_id = port_config['portId']
                    
                    # Prepare port configuration (exclude read-only fields)
                    port_data = {}
                    updatable_fields = [
                        'name', 'enabled', 'type', 'vlan', 'voiceVlan', 'allowedVlans',
                        'poeEnabled', 'isolationEnabled', 'rstpEnabled', 'stpGuard',
                        'linkNegotiation', 'portScheduleId', 'udld', 'accessPolicyType',
                        'accessPolicyNumber', 'macAllowList', 'stickyMacAllowList',
                        'stickyMacAllowListLimit', 'stormControlEnabled'
                    ]
                    
                    for field in updatable_fields:
                        if field in port_config:
                            port_data[field] = port_config[field]
                    
                    # Apply port configuration
                    url = f"{BASE_URL}/devices/{tst01_switch['serial']}/switch/ports/{port_id}"
                    result = self.make_api_request(url, method='PUT', data=port_data)
                    
                    if result:
                        updated_count += 1
                    
                    time.sleep(0.5)  # Rate limit
                
                self.log(f"    ✓ Updated {updated_count} ports on {tst01_switch['name']}")
            else:
                self.log(f"  No AZP 30 config available for switch {tst01_switch['name']}")
        
        return True
    
    def run_comprehensive_restore(self):
        """Run complete restoration process"""
        self.log("="*80)
        self.log("COMPREHENSIVE AZP 30 TO TST 01 RESTORE")
        self.log("="*80)
        
        try:
            # Step 1: Load source configuration
            if not self.load_source_configuration():
                return False
            
            # Step 2: Backup current TST 01 configuration
            backup_file = self.backup_target_configuration()
            
            # Step 3: Clear existing configuration
            self.clear_target_configuration()
            
            # Step 4: Restore VLANs
            if not self.restore_vlans():
                self.log("VLAN restoration failed", "ERROR")
                return False
            
            # Step 5: Restore firewall rules
            if not self.restore_firewall_rules():
                self.log("Firewall rules restoration failed", "ERROR")
                return False
            
            # Step 6: Restore MX ports
            if not self.restore_mx_ports():
                self.log("MX ports restoration failed", "ERROR")
                return False
            
            # Step 7: Restore switch ports
            if not self.restore_switch_ports():
                self.log("Switch ports restoration failed", "ERROR")
                return False
            
            # Generate report
            self.generate_report(backup_file)
            
            self.log("\n" + "="*80)
            self.log("✅ COMPREHENSIVE AZP 30 TO TST 01 RESTORE COMPLETED!")
            self.log("="*80)
            self.log("TST 01 now has complete AZP 30 configuration with test IP ranges")
            self.log(f"Original TST 01 backup: {backup_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Restoration failed: {e}", "ERROR")
            return False
    
    def generate_report(self, backup_file):
        """Generate restoration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
Comprehensive AZP 30 to TST 01 Restore Report
=============================================
Target: {self.target_name} ({self.target_network_id})
Source: {self.source_config_file}
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}
Backup File: {backup_file}

Components Restored:
"""
        
        if 'vlans' in self.source_data:
            report += f"- VLANs: {len(self.source_data['vlans'])} restored with test IP ranges\n"
        if 'firewall_rules' in self.source_data:
            report += f"- Firewall Rules: {len(self.source_data['firewall_rules']['rules'])} processed and filtered\n"
        if 'mx_ports' in self.source_data:
            report += f"- MX Ports: {len(self.source_data['mx_ports'])} configured\n"
        if 'switch_ports' in self.source_data:
            report += f"- Switch Configs: {len(self.source_data['switch_ports'])} switches processed\n"
        
        report += "\nLog Entries:\n"
        report += "\n".join(self.log_entries)
        
        # Save report
        report_filename = f"azp30_to_tst01_restore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        self.log(f"✓ Report saved to {report_filename}")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive AZP 30 to TST 01 Restore Tool')
    parser.add_argument('--source-config', default='azp_30_full_config_20250709_170149.json',
                        help='AZP 30 configuration file')
    parser.add_argument('--target-network-id', default='L_3790904986339115852',
                        help='TST 01 network ID')
    parser.add_argument('--target-name', default='TST 01',
                        help='Target network name')
    
    args = parser.parse_args()
    
    print("🔄 Comprehensive AZP 30 to TST 01 Restore Tool")
    print("=" * 80)
    print("This tool will completely restore AZP 30 configuration to TST 01:")
    print("- VLANs with test IP ranges (10.255.255.x)")
    print("- Complete firewall rules (filtered and simplified)")
    print("- MX port configurations")
    print("- Switch port configurations")
    print("- All other network settings")
    print("=" * 80)
    
    print(f"\nSource: {args.source_config}")
    print(f"Target: {args.target_name} ({args.target_network_id})")
    
    if not os.getenv('SKIP_CONFIRMATION'):
        print("\n⚠️  WARNING: This will completely replace TST 01 configuration!")
        confirm = input("Proceed with comprehensive restore? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Restore cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    # Run restore
    restorer = ComprehensiveRestore(args.source_config, args.target_network_id, args.target_name)
    success = restorer.run_comprehensive_restore()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()