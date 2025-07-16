#!/usr/bin/env python3
"""
Export TST 01 configuration to JSON and compare with AZP 30
This script extracts complete network configurations and performs detailed comparison
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
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

# Network IDs
TST_01_NETWORK_ID = "L_3790904986339115852"
AZP_30_NETWORK_ID = "L_650207196201635912"

def make_api_request(url, method='GET', data=None):
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
            print("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return make_api_request(url, method, data)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        return None

def export_network_config(network_id, network_name):
    """Export complete network configuration"""
    print(f"\nExporting {network_name} configuration...")
    
    config = {
        'extraction_date': datetime.now().isoformat(),
        'network_id': network_id,
        'network_name': network_name
    }
    
    # 1. Network info
    print("  Fetching network info...")
    network_url = f"{BASE_URL}/networks/{network_id}"
    network_info = make_api_request(network_url)
    if network_info:
        config['network'] = network_info
    
    # 2. Devices
    print("  Fetching devices...")
    devices_url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = make_api_request(devices_url)
    if devices:
        config['devices'] = devices
        
        # Separate by type
        config['devices_by_type'] = {
            'mx': [d for d in devices if d.get('model', '').startswith('MX')],
            'ms': [d for d in devices if d.get('model', '').startswith('MS')],
            'mr': [d for d in devices if d.get('model', '').startswith('MR')]
        }
    
    # 3. VLANs
    print("  Fetching VLANs...")
    vlans_url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(vlans_url)
    if vlans:
        config['vlans'] = sorted(vlans, key=lambda x: x['id'])
    
    # 4. Static Routes
    print("  Fetching static routes...")
    routes_url = f"{BASE_URL}/networks/{network_id}/appliance/staticRoutes"
    routes = make_api_request(routes_url)
    if routes:
        config['static_routes'] = routes
    
    # 5. Firewall Rules
    print("  Fetching firewall rules...")
    fw_url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    fw_rules = make_api_request(fw_url)
    if fw_rules:
        config['firewall_rules'] = fw_rules
    
    # 6. Group Policies
    print("  Fetching group policies...")
    policies_url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
    policies = make_api_request(policies_url)
    if policies:
        config['group_policies'] = policies
    
    # 7. Syslog
    print("  Fetching syslog configuration...")
    syslog_url = f"{BASE_URL}/networks/{network_id}/syslogServers"
    syslog = make_api_request(syslog_url)
    if syslog:
        config['syslog'] = syslog
    
    # 8. SNMP
    print("  Fetching SNMP configuration...")
    snmp_url = f"{BASE_URL}/networks/{network_id}/snmp"
    snmp = make_api_request(snmp_url)
    if snmp:
        config['snmp'] = snmp
    
    # 9. MX Ports
    print("  Fetching MX port configuration...")
    mx_ports_url = f"{BASE_URL}/networks/{network_id}/appliance/ports"
    mx_ports = make_api_request(mx_ports_url)
    if mx_ports:
        config['mx_ports'] = mx_ports
    
    # 10. DHCP Settings (per VLAN)
    if vlans:
        print("  Fetching DHCP settings...")
        config['dhcp_settings'] = {}
        for vlan in vlans:
            dhcp_url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan['id']}/dhcp"
            dhcp = make_api_request(dhcp_url)
            if dhcp:
                config['dhcp_settings'][vlan['id']] = dhcp
    
    # 11. Switch Settings
    print("  Fetching switch settings...")
    switch_settings_url = f"{BASE_URL}/networks/{network_id}/switch/settings"
    switch_settings = make_api_request(switch_settings_url)
    if switch_settings:
        config['switch_settings'] = switch_settings
    
    # 12. Switch Ports (for each switch)
    if config.get('devices_by_type', {}).get('ms'):
        print("  Fetching switch port configurations...")
        config['switch_ports'] = {}
        for switch in config['devices_by_type']['ms']:
            ports_url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
            ports = make_api_request(ports_url)
            if ports:
                config['switch_ports'][switch['serial']] = ports
    
    # 13. Network Services
    print("  Fetching network services...")
    services_url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/services"
    services = make_api_request(services_url)
    if services:
        config['network_services'] = services
    
    # 14. Content Filtering
    print("  Fetching content filtering...")
    content_url = f"{BASE_URL}/networks/{network_id}/appliance/contentFiltering"
    content = make_api_request(content_url)
    if content:
        config['content_filtering'] = content
    
    # 15. VPN Settings
    print("  Fetching VPN settings...")
    vpn_url = f"{BASE_URL}/networks/{network_id}/appliance/vpn/siteToSiteVpn"
    vpn = make_api_request(vpn_url)
    if vpn:
        config['vpn_settings'] = vpn
    
    return config

def normalize_config_for_comparison(config, is_test_network=False):
    """Normalize configuration for comparison, removing network-specific items"""
    normalized = json.loads(json.dumps(config))  # Deep copy
    
    # Remove extraction date
    normalized.pop('extraction_date', None)
    
    # Normalize IPs in VLANs
    if 'vlans' in normalized:
        for vlan in normalized['vlans']:
            if is_test_network and vlan.get('subnet', '').startswith('10.255.255'):
                # For test network, normalize the subnet
                parts = vlan['subnet'].split('.')
                if len(parts) >= 4:
                    # Keep only the last octet and subnet mask
                    vlan['subnet_normalized'] = f"X.X.X.{parts[3]}"
            elif vlan.get('subnet', '').startswith('10.'):
                parts = vlan['subnet'].split('.')
                if len(parts) >= 4:
                    vlan['subnet_normalized'] = f"X.X.X.{parts[3]}"
    
    # Remove device-specific info
    if 'devices' in normalized:
        for device in normalized['devices']:
            device.pop('serial', None)
            device.pop('mac', None)
            device.pop('lanIp', None)
            device.pop('url', None)
    
    # Normalize firewall rules
    if 'firewall_rules' in normalized and 'rules' in normalized['firewall_rules']:
        for rule in normalized['firewall_rules']['rules']:
            # Normalize IP addresses in rules
            for field in ['srcCidr', 'destCidr']:
                if field in rule and isinstance(rule[field], str):
                    if is_test_network and rule[field].startswith('10.255.255'):
                        parts = rule[field].split('.')
                        if len(parts) >= 4:
                            rule[f'{field}_normalized'] = f"X.X.X.{parts[3]}"
                    elif rule[field].startswith('10.'):
                        parts = rule[field].split('.')
                        if len(parts) >= 4:
                            rule[f'{field}_normalized'] = f"X.X.X.{parts[3]}"
    
    return normalized

def compare_configurations(tst_config, azp_config):
    """Compare two network configurations and generate detailed report"""
    print("\n" + "=" * 80)
    print("CONFIGURATION COMPARISON REPORT")
    print("=" * 80)
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'source': 'AZP 30',
        'target': 'TST 01',
        'differences': {}
    }
    
    # 1. VLAN Comparison
    print("\n1. VLAN COMPARISON")
    print("-" * 40)
    
    tst_vlans = {v['id']: v for v in tst_config.get('vlans', [])}
    azp_vlans = {v['id']: v for v in azp_config.get('vlans', [])}
    
    print(f"TST 01 VLANs: {sorted(tst_vlans.keys())}")
    print(f"AZP 30 VLANs: {sorted(azp_vlans.keys())}")
    
    # Expected mapping
    vlan_mapping = {
        1: 100, 101: 200, 300: 300, 301: 301,
        801: 400, 201: 410, 800: 800, 803: 803, 900: 900
    }
    
    vlan_issues = []
    for azp_id, expected_tst_id in vlan_mapping.items():
        if azp_id in azp_vlans:
            if expected_tst_id in tst_vlans:
                print(f"\n  ✅ VLAN {azp_id} → {expected_tst_id} migrated")
            else:
                print(f"\n  ❌ VLAN {azp_id} → {expected_tst_id} NOT found in TST 01")
                vlan_issues.append(f"Missing VLAN {expected_tst_id}")
        
        # Check if old VLAN still exists
        if azp_id != expected_tst_id and azp_id in tst_vlans:
            print(f"     ⚠️  Old VLAN {azp_id} still exists in TST 01")
            vlan_issues.append(f"Old VLAN {azp_id} not removed")
    
    comparison['differences']['vlans'] = vlan_issues
    
    # 2. Firewall Rules Comparison
    print("\n\n2. FIREWALL RULES COMPARISON")
    print("-" * 40)
    
    tst_rules = tst_config.get('firewall_rules', {}).get('rules', [])
    azp_rules = azp_config.get('firewall_rules', {}).get('rules', [])
    
    print(f"TST 01: {len(tst_rules)} rules")
    print(f"AZP 30: {len(azp_rules)} rules")
    
    # Note: TST 01 uses NEO 07 rules, not AZP 30
    print("Note: TST 01 configured with NEO 07 firewall rules (not AZP 30)")
    
    # 3. Group Policies Comparison
    print("\n\n3. GROUP POLICIES COMPARISON")
    print("-" * 40)
    
    tst_policies = tst_config.get('group_policies', [])
    azp_policies = azp_config.get('group_policies', [])
    
    print(f"TST 01: {len(tst_policies)} policies")
    print(f"AZP 30: {len(azp_policies)} policies")
    
    tst_policy_names = {p['name'] for p in tst_policies}
    azp_policy_names = {p['name'] for p in azp_policies}
    
    common = tst_policy_names & azp_policy_names
    print(f"Common policies: {common}")
    
    # 4. Switch Port Analysis
    print("\n\n4. SWITCH PORT VLAN ASSIGNMENTS")
    print("-" * 40)
    
    if 'switch_ports' in tst_config:
        vlan_counts = defaultdict(int)
        total_ports = 0
        
        for serial, ports in tst_config['switch_ports'].items():
            for port in ports:
                if 'vlan' in port:
                    vlan_counts[port['vlan']] += 1
                    total_ports += 1
        
        print(f"Total ports analyzed: {total_ports}")
        print("\nVLAN assignments:")
        
        old_vlan_ports = 0
        new_vlan_ports = 0
        
        for vlan_id in sorted(vlan_counts.keys()):
            count = vlan_counts[vlan_id]
            if vlan_id in [1, 101, 201, 801, 802]:
                print(f"  VLAN {vlan_id}: {count} ports (OLD - needs update)")
                old_vlan_ports += count
            elif vlan_id in [100, 200, 300, 301, 400, 410, 800, 803, 900]:
                print(f"  VLAN {vlan_id}: {count} ports (NEW - correct)")
                new_vlan_ports += count
            else:
                print(f"  VLAN {vlan_id}: {count} ports")
        
        print(f"\nSwitch port migration status:")
        print(f"  Ports with old VLANs: {old_vlan_ports}")
        print(f"  Ports with new VLANs: {new_vlan_ports}")
        
        if old_vlan_ports > 0:
            migration_percent = (new_vlan_ports / (old_vlan_ports + new_vlan_ports)) * 100
            print(f"  Migration progress: {migration_percent:.1f}%")
    
    # 5. MX Port Comparison
    print("\n\n5. MX PORT CONFIGURATION")
    print("-" * 40)
    
    tst_mx_ports = tst_config.get('mx_ports', [])
    azp_mx_ports = azp_config.get('mx_ports', [])
    
    print(f"TST 01: {len(tst_mx_ports)} ports")
    print(f"AZP 30: {len(azp_mx_ports)} ports")
    
    # 6. Network Services
    print("\n\n6. NETWORK SERVICES")
    print("-" * 40)
    
    tst_services = tst_config.get('network_services', {})
    azp_services = azp_config.get('network_services', {})
    
    service_names = set()
    if 'access' in tst_services:
        service_names.update(s['service'] for s in tst_services['access'])
    if 'access' in azp_services:
        service_names.update(s['service'] for s in azp_services['access'])
    
    print(f"Services configured: {len(service_names)}")
    
    return comparison

def main():
    """Main function"""
    print("Network Configuration Export and Comparison Tool")
    print("=" * 80)
    
    # Export TST 01 configuration
    tst_config = export_network_config(TST_01_NETWORK_ID, "TST 01")
    
    # Save TST 01 configuration
    tst_filename = f"tst_01_full_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(tst_filename, 'w') as f:
        json.dump(tst_config, f, indent=2)
    print(f"\n✅ TST 01 configuration exported to: {tst_filename}")
    
    # Export AZP 30 configuration
    azp_config = export_network_config(AZP_30_NETWORK_ID, "AZP 30")
    
    # Save AZP 30 configuration
    azp_filename = f"azp_30_full_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(azp_filename, 'w') as f:
        json.dump(azp_config, f, indent=2)
    print(f"✅ AZP 30 configuration exported to: {azp_filename}")
    
    # Compare configurations
    comparison = compare_configurations(tst_config, azp_config)
    
    # Save comparison report
    comparison_filename = f"config_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(comparison_filename, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Summary
    print("\n" + "=" * 80)
    print("EXPORT AND COMPARISON COMPLETE")
    print("=" * 80)
    print(f"\nFiles created:")
    print(f"  1. TST 01 Config: {tst_filename}")
    print(f"  2. AZP 30 Config: {azp_filename}")
    print(f"  3. Comparison Report: {comparison_filename}")
    
    # Migration Status Summary
    print("\n" + "=" * 80)
    print("MIGRATION STATUS SUMMARY")
    print("=" * 80)
    
    # Check key migration indicators
    vlans_migrated = len([v for v in tst_config.get('vlans', []) if v['id'] in [100, 200, 300, 301, 400, 410, 800, 803, 900]])
    old_vlans_present = len([v for v in tst_config.get('vlans', []) if v['id'] in [1, 101, 201, 801, 802]])
    
    print(f"\n✅ New VLANs created: {vlans_migrated}/9")
    print(f"❌ Old VLANs to remove: {old_vlans_present}")
    print(f"✅ Group policies: {len(tst_config.get('group_policies', []))}")
    print(f"✅ Firewall rules: {len(tst_config.get('firewall_rules', {}).get('rules', []))}")
    
    if 'switch_ports' in tst_config:
        total_ports = sum(len(ports) for ports in tst_config['switch_ports'].values())
        print(f"⚠️  Switch ports to update: Check {total_ports} ports")
    
    print("\n📝 Next Steps:")
    print("   1. Review the exported configurations")
    print("   2. Update remaining switch ports to new VLAN IDs")
    print("   3. Remove old VLANs after switch port migration")
    print("   4. Verify firewall rules reference correct VLAN IDs")

if __name__ == "__main__":
    main()