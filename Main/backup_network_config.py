#!/usr/bin/env python3
"""
Backup Network Configuration
============================

This script creates a complete backup of a Meraki network configuration
that can be used for restoration.

Usage:
    python3 backup_network_config.py --network-id <network_id>

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

class NetworkBackup:
    def __init__(self, network_id):
        self.network_id = network_id
        self.backup_data = {}
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def make_api_request(self, url, method='GET'):
        try:
            response = requests.request(method, url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json() if response.text else None
        except Exception as e:
            self.log(f"API Error: {e}")
            return None
    
    def backup_network_info(self):
        """Backup basic network information"""
        self.log("Backing up network information...")
        url = f"{BASE_URL}/networks/{self.network_id}"
        self.backup_data['network'] = self.make_api_request(url)
        
    def backup_vlans(self):
        """Backup VLAN configuration"""
        self.log("Backing up VLANs...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        vlans = self.make_api_request(url)
        if vlans:
            self.backup_data['vlans'] = vlans
            self.log(f"  ✓ Backed up {len(vlans)} VLANs")
            
    def backup_firewall_rules(self):
        """Backup firewall rules"""
        self.log("Backing up firewall rules...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        rules = self.make_api_request(url)
        if rules:
            self.backup_data['firewall_rules'] = rules
            self.log(f"  ✓ Backed up {len(rules.get('rules', []))} firewall rules")
            
    def backup_group_policies(self):
        """Backup group policies"""
        self.log("Backing up group policies...")
        url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        policies = self.make_api_request(url)
        if policies:
            self.backup_data['group_policies'] = policies
            self.log(f"  ✓ Backed up {len(policies)} group policies")
            
    def backup_syslog(self):
        """Backup syslog configuration"""
        self.log("Backing up syslog configuration...")
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        syslog = self.make_api_request(url)
        if syslog:
            self.backup_data['syslog'] = syslog
            
    def backup_mx_ports(self):
        """Backup MX port configuration"""
        self.log("Backing up MX ports...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/ports"
        ports = self.make_api_request(url)
        if ports:
            self.backup_data['mx_ports'] = ports
            self.log(f"  ✓ Backed up {len(ports)} MX ports")
            
    def backup_switch_ports(self):
        """Backup switch port configuration"""
        self.log("Backing up switch ports...")
        
        # Get all switches
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        devices = self.make_api_request(url)
        
        if devices:
            switches = [d for d in devices if d.get('model', '').startswith('MS')]
            self.backup_data['switches'] = {}
            
            for switch in switches:
                self.log(f"  Backing up {switch['name']}...")
                url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
                ports = self.make_api_request(url)
                if ports:
                    self.backup_data['switches'][switch['serial']] = {
                        'device': switch,
                        'ports': ports
                    }
                    self.log(f"    ✓ Backed up {len(ports)} ports")
                    
    def backup_static_routes(self):
        """Backup static routes"""
        self.log("Backing up static routes...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/staticRoutes"
        routes = self.make_api_request(url)
        if routes:
            self.backup_data['static_routes'] = routes
            
    def backup_vpn(self):
        """Backup VPN configuration"""
        self.log("Backing up VPN configuration...")
        
        # Site-to-site VPN
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vpn/siteToSiteVpn"
        s2s_vpn = self.make_api_request(url)
        if s2s_vpn:
            self.backup_data['site_to_site_vpn'] = s2s_vpn
            
    def backup_content_filtering(self):
        """Backup content filtering settings"""
        self.log("Backing up content filtering...")
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/contentFiltering"
        filtering = self.make_api_request(url)
        if filtering:
            self.backup_data['content_filtering'] = filtering
            
    def save_backup(self):
        """Save backup to file"""
        network_name = self.backup_data['network']['name'].replace(' ', '_').lower()
        filename = f"backup_{network_name}_{self.network_id}_{self.timestamp}.json"
        
        self.backup_data['backup_info'] = {
            'timestamp': datetime.now().isoformat(),
            'network_id': self.network_id,
            'network_name': self.backup_data['network']['name'],
            'version': '1.0'
        }
        
        with open(filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2)
            
        self.log(f"\n✅ Backup completed successfully!")
        self.log(f"📁 Saved to: {filename}")
        self.log(f"📊 Size: {os.path.getsize(filename) / 1024:.1f} KB")
        
        return filename
    
    def run_backup(self):
        """Run complete backup process"""
        self.log(f"🔧 Starting backup for network {self.network_id}")
        self.log("="*60)
        
        # Backup all components
        self.backup_network_info()
        self.backup_vlans()
        self.backup_firewall_rules()
        self.backup_group_policies()
        self.backup_syslog()
        self.backup_mx_ports()
        self.backup_switch_ports()
        self.backup_static_routes()
        self.backup_vpn()
        self.backup_content_filtering()
        
        # Save to file
        return self.save_backup()

def main():
    parser = argparse.ArgumentParser(description='Backup Meraki network configuration')
    parser.add_argument('--network-id', required=True, help='Network ID to backup')
    
    args = parser.parse_args()
    
    backup = NetworkBackup(args.network_id)
    backup_file = backup.run_backup()
    
    print(f"\n💡 To restore this backup later, use:")
    print(f"   python3 restore_network_config.py --backup-file {backup_file}")

if __name__ == "__main__":
    main()