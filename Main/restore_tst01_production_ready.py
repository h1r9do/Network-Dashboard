#!/usr/bin/env python3
"""
Quick Restore TST 01 to Production-Ready State
Restores TST 01 using the production-ready backup (faster than comprehensive restore)
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

class QuickRestore:
    def __init__(self, backup_file, target_network_id):
        self.backup_file = backup_file
        self.target_network_id = target_network_id
        self.log_entries = []
        self.start_time = datetime.now()
        self.backup_data = {}
        
        self.log(f"Quick Restore initialized")
        self.log(f"Backup: {backup_file}")
        self.log(f"Target: TST 01 ({target_network_id})")
    
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
    
    def load_backup(self):
        """Load production-ready backup"""
        self.log("Loading production-ready backup...")
        
        try:
            with open(self.backup_file, 'r') as f:
                self.backup_data = json.load(f)
            
            # Log what we found
            if 'vlans' in self.backup_data:
                self.log(f"  Found {len(self.backup_data['vlans'])} VLANs")
            if 'firewall_rules' in self.backup_data:
                self.log(f"  Found {len(self.backup_data['firewall_rules']['rules'])} firewall rules")
            if 'mx_ports' in self.backup_data:
                self.log(f"  Found {len(self.backup_data['mx_ports'])} MX ports")
            if 'switch_ports' in self.backup_data:
                self.log(f"  Found switch configurations for {len(self.backup_data['switch_ports'])} switches")
            if 'group_policies' in self.backup_data:
                self.log(f"  Found {len(self.backup_data['group_policies'])} group policies")
            
            return True
            
        except FileNotFoundError:
            self.log(f"Backup file not found: {self.backup_file}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error loading backup: {e}", "ERROR")
            return False
    
    def clear_current_configuration(self):
        """Clear existing TST 01 configuration"""
        self.log("\\nClearing existing TST 01 configuration...")
        
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
        """Restore VLANs from backup"""
        self.log("\\nRestoring VLANs from backup...")
        
        if 'vlans' not in self.backup_data:
            self.log("  No VLAN data found in backup", "WARNING")
            return False
        
        created_count = 0
        for vlan in self.backup_data['vlans']:
            if vlan['id'] == 900:  # Skip management VLAN
                continue
            
            vlan_data = copy.deepcopy(vlan)
            
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
        """Restore firewall rules from backup"""
        self.log("\\nRestoring firewall rules from backup...")
        
        if 'firewall_rules' not in self.backup_data:
            self.log("  No firewall rules found in backup", "WARNING")
            return False
        
        firewall_rules = self.backup_data['firewall_rules']['rules']
        self.log(f"  Restoring {len(firewall_rules)} firewall rules")
        
        # Apply firewall rules
        url = f"{BASE_URL}/networks/{self.target_network_id}/appliance/firewall/l3FirewallRules"
        result = self.make_api_request(url, method='PUT', data={'rules': firewall_rules})
        
        if result:
            self.log(f"  ✓ Applied {len(firewall_rules)} firewall rules")
            return True
        else:
            self.log("  ✗ Failed to apply firewall rules", "ERROR")
            return False
    
    def restore_mx_ports(self):
        """Restore MX port configurations from backup"""
        self.log("\\nRestoring MX port configurations from backup...")
        
        if 'mx_ports' not in self.backup_data:
            self.log("  No MX port data found in backup", "WARNING")
            return False
        
        updated_count = 0
        for port in self.backup_data['mx_ports']:
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
        """Restore switch port configurations from backup"""
        self.log("\\nRestoring switch port configurations from backup...")
        
        if 'switch_ports' not in self.backup_data:
            self.log("  No switch port data found in backup", "WARNING")
            return False
        
        # Get current TST 01 switches
        url = f"{BASE_URL}/networks/{self.target_network_id}/devices"
        devices = self.make_api_request(url)
        if not devices:
            self.log("  Could not get TST 01 devices", "ERROR")
            return False
        
        tst01_switches = [d for d in devices if d['model'].startswith('MS')]
        self.log(f"  Found {len(tst01_switches)} switches in TST 01")
        
        # Map TST 01 switches to backup switch configs (by position/index)
        backup_switch_serials = list(self.backup_data['switch_ports'].keys())
        
        for i, tst01_switch in enumerate(tst01_switches):
            if i < len(backup_switch_serials):
                backup_serial = backup_switch_serials[i]
                backup_config = self.backup_data['switch_ports'][backup_serial]
                
                self.log(f"  Applying backup switch config to {tst01_switch['name']}")
                
                updated_count = 0
                for port_config in backup_config['ports']:
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
                self.log(f"  No backup config available for switch {tst01_switch['name']}")
        
        return True
    
    def run_quick_restore(self):
        """Run quick restoration process"""
        self.log("="*60)
        self.log("QUICK TST 01 PRODUCTION-READY RESTORE")
        self.log("="*60)
        
        try:
            # Step 1: Load backup
            if not self.load_backup():
                return False
            
            # Step 2: Clear existing configuration
            self.clear_current_configuration()
            
            # Step 3: Restore VLANs
            if not self.restore_vlans():
                self.log("VLAN restoration failed", "ERROR")
                return False
            
            # Step 4: Restore firewall rules
            if not self.restore_firewall_rules():
                self.log("Firewall rules restoration failed", "ERROR")
                return False
            
            # Step 5: Restore MX ports
            if not self.restore_mx_ports():
                self.log("MX ports restoration failed", "ERROR")
                return False
            
            # Step 6: Restore switch ports
            if not self.restore_switch_ports():
                self.log("Switch ports restoration failed", "ERROR")
                return False
            
            # Generate report
            self.generate_report()
            
            self.log("\\n" + "="*60)
            self.log("✅ QUICK TST 01 PRODUCTION-READY RESTORE COMPLETED!")
            self.log("="*60)
            self.log("TST 01 restored to production-ready state for VLAN migration testing")
            
            return True
            
        except Exception as e:
            self.log(f"Restoration failed: {e}", "ERROR")
            return False
    
    def generate_report(self):
        """Generate restoration report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
Quick TST 01 Production-Ready Restore Report
============================================
Target: TST 01 ({self.target_network_id})
Backup: {self.backup_file}
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

Components Restored:
"""
        
        if 'vlans' in self.backup_data:
            report += f"- VLANs: {len(self.backup_data['vlans'])} restored\\n"
        if 'firewall_rules' in self.backup_data:
            report += f"- Firewall Rules: {len(self.backup_data['firewall_rules']['rules'])} restored\\n"
        if 'mx_ports' in self.backup_data:
            report += f"- MX Ports: {len(self.backup_data['mx_ports'])} configured\\n"
        if 'switch_ports' in self.backup_data:
            report += f"- Switch Configs: {len(self.backup_data['switch_ports'])} switches processed\\n"
        
        report += "\\nLog Entries:\\n"
        report += "\\n".join(self.log_entries)
        
        # Save report
        report_filename = f"tst01_quick_restore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        self.log(f"✓ Report saved to {report_filename}")

def main():
    parser = argparse.ArgumentParser(description='Quick TST 01 Production-Ready Restore Tool')
    parser.add_argument('--backup-file', default='tst01_production_ready_backup_20250710_091816.json',
                        help='Production-ready backup file')
    parser.add_argument('--target-network-id', default='L_3790904986339115852',
                        help='TST 01 network ID')
    
    args = parser.parse_args()
    
    print("🚀 Quick TST 01 Production-Ready Restore Tool")
    print("=" * 60)
    print("This tool will quickly restore TST 01 to production-ready state using backup:")
    print("- Complete VLAN configuration (legacy numbering)")
    print("- Production-complexity firewall rules (59 rules with VLAN references)")
    print("- MX and switch port configurations")
    print("- Ready for immediate VLAN migration testing")
    print("=" * 60)
    
    print(f"\\nBackup: {args.backup_file}")
    print(f"Target: TST 01 ({args.target_network_id})")
    
    if not os.getenv('SKIP_CONFIRMATION'):
        print("\\n⚠️  WARNING: This will completely replace TST 01 configuration!")
        confirm = input("Proceed with quick restore? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Restore cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    # Run restore
    restorer = QuickRestore(args.backup_file, args.target_network_id)
    success = restorer.run_quick_restore()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()