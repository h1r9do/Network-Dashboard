#!/usr/bin/env python3
"""
Network Configuration Comparison Tool
Compares all aspects of two networks including VLANs, firewall rules, ports, etc.
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import difflib

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

class NetworkComparator:
    def __init__(self, network1_id, network1_name, network2_id, network2_name):
        self.network1_id = network1_id
        self.network1_name = network1_name
        self.network2_id = network2_id
        self.network2_name = network2_name
        self.comparison_results = {}
        
    def make_api_request(self, url):
        """Make API request with error handling"""
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    def compare_vlans(self):
        """Compare VLANs between networks"""
        print(f"\n{'='*80}")
        print(f"VLAN COMPARISON: {self.network1_name} vs {self.network2_name}")
        print(f"{'='*80}")
        
        # Get VLANs from both networks
        url1 = f"{BASE_URL}/networks/{self.network1_id}/appliance/vlans"
        url2 = f"{BASE_URL}/networks/{self.network2_id}/appliance/vlans"
        
        vlans1 = self.make_api_request(url1)
        vlans2 = self.make_api_request(url2)
        
        if not vlans1 or not vlans2:
            print("Failed to retrieve VLAN data")
            return
        
        # Create VLAN dictionaries by ID
        vlans1_dict = {v['id']: v for v in vlans1}
        vlans2_dict = {v['id']: v for v in vlans2}
        
        # Compare VLANs
        all_vlan_ids = set(vlans1_dict.keys()) | set(vlans2_dict.keys())
        
        print(f"\n{self.network1_name} VLANs: {sorted(vlans1_dict.keys())}")
        print(f"{self.network2_name} VLANs: {sorted(vlans2_dict.keys())}")
        
        print(f"\nDetailed VLAN Comparison:")
        print(f"{'VLAN ID':<10} {'Status':<20} {'Name':<20} {'Subnet':<20}")
        print("-" * 70)
        
        for vlan_id in sorted(all_vlan_ids):
            if vlan_id in vlans1_dict and vlan_id in vlans2_dict:
                v1 = vlans1_dict[vlan_id]
                v2 = vlans2_dict[vlan_id]
                status = "Both networks"
                name = f"{v1['name']} | {v2['name']}" if v1['name'] != v2['name'] else v1['name']
                subnet = f"{v1.get('subnet', 'N/A')} | {v2.get('subnet', 'N/A')}" if v1.get('subnet') != v2.get('subnet') else v1.get('subnet', 'N/A')
            elif vlan_id in vlans1_dict:
                v1 = vlans1_dict[vlan_id]
                status = f"{self.network1_name} only"
                name = v1['name']
                subnet = v1.get('subnet', 'N/A')
            else:
                v2 = vlans2_dict[vlan_id]
                status = f"{self.network2_name} only"
                name = v2['name']
                subnet = v2.get('subnet', 'N/A')
            
            print(f"{vlan_id:<10} {status:<20} {name:<20} {subnet:<20}")
        
        self.comparison_results['vlans'] = {
            'network1_count': len(vlans1),
            'network2_count': len(vlans2),
            'common_vlans': len(set(vlans1_dict.keys()) & set(vlans2_dict.keys()))
        }
    
    def compare_firewall_rules(self):
        """Compare firewall rules between networks"""
        print(f"\n{'='*80}")
        print(f"FIREWALL RULES COMPARISON: {self.network1_name} vs {self.network2_name}")
        print(f"{'='*80}")
        
        # Get firewall rules from both networks
        url1 = f"{BASE_URL}/networks/{self.network1_id}/appliance/firewall/l3FirewallRules"
        url2 = f"{BASE_URL}/networks/{self.network2_id}/appliance/firewall/l3FirewallRules"
        
        fw1 = self.make_api_request(url1)
        fw2 = self.make_api_request(url2)
        
        if not fw1 or not fw2:
            print("Failed to retrieve firewall data")
            return
        
        rules1 = fw1.get('rules', [])
        rules2 = fw2.get('rules', [])
        
        print(f"\n{self.network1_name}: {len(rules1)} rules")
        print(f"{self.network2_name}: {len(rules2)} rules")
        
        # Show first few rules from each
        print(f"\n{self.network1_name} - First 5 rules:")
        for i, rule in enumerate(rules1[:5]):
            print(f"  {i+1}. {rule.get('comment', 'No comment')} - {rule.get('policy', 'N/A')}")
            print(f"     Src: {rule.get('srcCidr', 'Any')} → Dst: {rule.get('destCidr', 'Any')}")
        
        print(f"\n{self.network2_name} - First 5 rules:")
        for i, rule in enumerate(rules2[:5]):
            print(f"  {i+1}. {rule.get('comment', 'No comment')} - {rule.get('policy', 'N/A')}")
            print(f"     Src: {rule.get('srcCidr', 'Any')} → Dst: {rule.get('destCidr', 'Any')}")
        
        # Check for VLAN references
        print(f"\nVLAN References in Firewall Rules:")
        vlan_refs1 = self.count_vlan_references(rules1)
        vlan_refs2 = self.count_vlan_references(rules2)
        
        print(f"\n{self.network1_name} VLAN references: {vlan_refs1}")
        print(f"{self.network2_name} VLAN references: {vlan_refs2}")
        
        self.comparison_results['firewall'] = {
            'network1_rules': len(rules1),
            'network2_rules': len(rules2)
        }
    
    def count_vlan_references(self, rules):
        """Count VLAN references in firewall rules"""
        vlan_counts = {}
        for rule in rules:
            src = str(rule.get('srcCidr', ''))
            dst = str(rule.get('destCidr', ''))
            combined = src + ' ' + dst
            
            # Find all VLAN references
            import re
            vlan_matches = re.findall(r'VLAN\((\d+)\)', combined)
            for vlan_id in vlan_matches:
                vlan_counts[int(vlan_id)] = vlan_counts.get(int(vlan_id), 0) + 1
        
        return dict(sorted(vlan_counts.items()))
    
    def compare_mx_ports(self):
        """Compare MX port configurations"""
        print(f"\n{'='*80}")
        print(f"MX PORT COMPARISON: {self.network1_name} vs {self.network2_name}")
        print(f"{'='*80}")
        
        # Get MX ports from both networks
        url1 = f"{BASE_URL}/networks/{self.network1_id}/appliance/ports"
        url2 = f"{BASE_URL}/networks/{self.network2_id}/appliance/ports"
        
        ports1 = self.make_api_request(url1)
        ports2 = self.make_api_request(url2)
        
        if not ports1 or not ports2:
            print("Failed to retrieve MX port data")
            return
        
        print(f"\n{self.network1_name}: {len(ports1)} MX ports")
        print(f"{self.network2_name}: {len(ports2)} MX ports")
        
        # Compare each port
        print(f"\nPort Configuration Comparison:")
        print(f"{'Port':<6} {'Type':<10} {'Enabled':<10} {'VLAN/Native':<15} {'Allowed VLANs':<30}")
        print("-" * 80)
        
        max_ports = max(len(ports1), len(ports2))
        for i in range(max_ports):
            if i < len(ports1):
                p1 = ports1[i]
                port_num = p1['number']
                
                # Find matching port in network2
                p2 = next((p for p in ports2 if p['number'] == port_num), None)
                
                if p2:
                    # Compare configurations
                    type_match = p1.get('type') == p2.get('type')
                    enabled_match = p1.get('enabled') == p2.get('enabled')
                    vlan_match = p1.get('vlan') == p2.get('vlan')
                    allowed_match = p1.get('allowedVlans') == p2.get('allowedVlans')
                    
                    if type_match and enabled_match and vlan_match and allowed_match:
                        status = "✓ Match"
                    else:
                        status = "✗ Differ"
                    
                    print(f"{port_num:<6} {status:<10} {self.network1_name}: {p1.get('type', 'N/A'):<8} {str(p1.get('enabled', 'N/A')):<8} VLAN {str(p1.get('vlan', 'N/A')):<10} {str(p1.get('allowedVlans', 'N/A'))[:25]:<25}")
                    print(f"{'':6} {'':10} {self.network2_name}: {p2.get('type', 'N/A'):<8} {str(p2.get('enabled', 'N/A')):<8} VLAN {str(p2.get('vlan', 'N/A')):<10} {str(p2.get('allowedVlans', 'N/A'))[:25]:<25}")
                    print()
    
    def compare_switch_ports(self):
        """Compare switch port configurations"""
        print(f"\n{'='*80}")
        print(f"SWITCH PORT COMPARISON: {self.network1_name} vs {self.network2_name}")
        print(f"{'='*80}")
        
        # Get devices from both networks
        url1 = f"{BASE_URL}/networks/{self.network1_id}/devices"
        url2 = f"{BASE_URL}/networks/{self.network2_id}/devices"
        
        devices1 = self.make_api_request(url1)
        devices2 = self.make_api_request(url2)
        
        if not devices1 or not devices2:
            print("Failed to retrieve device data")
            return
        
        # Filter for switches
        switches1 = [d for d in devices1 if d['model'].startswith('MS')]
        switches2 = [d for d in devices2 if d['model'].startswith('MS')]
        
        print(f"\n{self.network1_name}: {len(switches1)} switches")
        print(f"{self.network2_name}: {len(switches2)} switches")
        
        # Get port counts and VLAN usage
        for sw in switches1[:1]:  # Just show first switch
            url = f"{BASE_URL}/devices/{sw['serial']}/switch/ports"
            ports = self.make_api_request(url)
            
            if ports:
                print(f"\n{self.network1_name} - {sw['name']} Port Summary:")
                self.summarize_switch_ports(ports)
        
        for sw in switches2[:1]:  # Just show first switch
            url = f"{BASE_URL}/devices/{sw['serial']}/switch/ports"
            ports = self.make_api_request(url)
            
            if ports:
                print(f"\n{self.network2_name} - {sw['name']} Port Summary:")
                self.summarize_switch_ports(ports)
    
    def summarize_switch_ports(self, ports):
        """Summarize switch port configurations"""
        vlan_usage = {}
        port_types = {'access': 0, 'trunk': 0}
        enabled_count = 0
        
        for port in ports:
            # Count port types
            port_types[port.get('type', 'access')] += 1
            
            # Count enabled ports
            if port.get('enabled', False):
                enabled_count += 1
            
            # Count VLAN usage
            vlan = port.get('vlan')
            if vlan:
                vlan_usage[vlan] = vlan_usage.get(vlan, 0) + 1
        
        print(f"  Total ports: {len(ports)}")
        print(f"  Enabled: {enabled_count}")
        print(f"  Access ports: {port_types['access']}")
        print(f"  Trunk ports: {port_types['trunk']}")
        print(f"  VLAN usage: {dict(sorted(vlan_usage.items()))}")
    
    def compare_group_policies(self):
        """Compare group policies"""
        print(f"\n{'='*80}")
        print(f"GROUP POLICY COMPARISON: {self.network1_name} vs {self.network2_name}")
        print(f"{'='*80}")
        
        # Get group policies from both networks
        url1 = f"{BASE_URL}/networks/{self.network1_id}/groupPolicies"
        url2 = f"{BASE_URL}/networks/{self.network2_id}/groupPolicies"
        
        policies1 = self.make_api_request(url1)
        policies2 = self.make_api_request(url2)
        
        if policies1 is None or policies2 is None:
            print("Failed to retrieve group policy data")
            return
        
        print(f"\n{self.network1_name}: {len(policies1)} policies")
        print(f"{self.network2_name}: {len(policies2)} policies")
        
        # Show policy names
        if policies1:
            print(f"\n{self.network1_name} policies:")
            for p in policies1:
                print(f"  - {p['name']} (ID: {p['groupPolicyId']})")
        
        if policies2:
            print(f"\n{self.network2_name} policies:")
            for p in policies2:
                print(f"  - {p['name']} (ID: {p['groupPolicyId']})")
    
    def run_comparison(self):
        """Run all comparisons"""
        print(f"\n{'='*80}")
        print(f"NETWORK CONFIGURATION COMPARISON")
        print(f"Network 1: {self.network1_name} ({self.network1_id})")
        print(f"Network 2: {self.network2_name} ({self.network2_id})")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        self.compare_vlans()
        self.compare_firewall_rules()
        self.compare_mx_ports()
        self.compare_switch_ports()
        self.compare_group_policies()
        
        # Summary
        print(f"\n{'='*80}")
        print("COMPARISON SUMMARY")
        print(f"{'='*80}")
        print(f"VLANs: {self.comparison_results.get('vlans', {}).get('network1_count', 0)} vs {self.comparison_results.get('vlans', {}).get('network2_count', 0)}")
        print(f"Firewall Rules: {self.comparison_results.get('firewall', {}).get('network1_rules', 0)} vs {self.comparison_results.get('firewall', {}).get('network2_rules', 0)}")

def main():
    # TST 01 vs NEO 07
    tst01_id = "L_3790904986339115852"
    neo07_id = "L_3790904986339115847"
    
    comparator = NetworkComparator(tst01_id, "TST 01", neo07_id, "NEO 07")
    comparator.run_comparison()

if __name__ == "__main__":
    main()