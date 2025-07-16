#!/usr/bin/env python3
"""
Enhanced verification script for TST 01 migration.
This version handles partial migrations and provides detailed analysis.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

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

# Test network prefix for IP comparisons
TEST_NETWORK_PREFIX = '10.255.255'

# VLAN mapping from migration
VLAN_MAPPING = {
    1: 100,      # Data
    101: 200,    # Voice
    300: 300,    # AP Mgmt -> Net Mgmt
    301: 301,    # Scanner
    801: 400,    # IOT -> IoT
    201: 410,    # Ccard
    800: 800,    # Guest
    803: 803,    # IoT Wireless
    900: 900,    # Mgmt
    802: None    # IOT Network -> To be removed
}

# Expected VLANs after full migration
EXPECTED_VLANS = {
    100: "Data",
    200: "Voice", 
    300: "Net Mgmt",
    301: "Scanner",
    400: "IoT",
    410: "Ccard",
    800: "Guest",
    803: "IoT Wireless",
    900: "Mgmt"
}

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
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def analyze_vlan_migration_status(tst_vlans):
    """Analyze the current VLAN migration status"""
    print("\nVLAN MIGRATION STATUS ANALYSIS")
    print("=" * 80)
    
    # Categorize VLANs
    old_vlans = []
    new_vlans = []
    unchanged_vlans = []
    
    for vlan in tst_vlans:
        vlan_id = vlan['id']
        
        # Check if it's an old VLAN that should be migrated
        if vlan_id in VLAN_MAPPING and VLAN_MAPPING[vlan_id] != vlan_id:
            old_vlans.append(vlan)
        # Check if it's a new VLAN from the mapping
        elif vlan_id in EXPECTED_VLANS:
            new_vlans.append(vlan)
        # VLANs that stay the same
        elif vlan_id in [300, 301, 800, 803, 900]:
            unchanged_vlans.append(vlan)
        else:
            old_vlans.append(vlan)
    
    print(f"\nCurrent Status:")
    print(f"  Old VLANs still present: {len(old_vlans)}")
    print(f"  New VLANs created: {len(new_vlans)}")
    print(f"  Unchanged VLANs: {len(unchanged_vlans)}")
    
    if old_vlans:
        print(f"\n❌ Old VLANs that need to be removed:")
        for vlan in old_vlans:
            print(f"    VLAN {vlan['id']}: {vlan['name']} ({vlan.get('subnet', 'No subnet')})")
    
    print(f"\n✅ Successfully migrated VLANs:")
    for vlan in new_vlans:
        # Find original VLAN ID
        orig_id = None
        for old_id, new_id in VLAN_MAPPING.items():
            if new_id == vlan['id']:
                orig_id = old_id
                break
        
        if orig_id and orig_id != vlan['id']:
            print(f"    VLAN {orig_id} → {vlan['id']}: {vlan['name']} ({vlan.get('subnet', 'No subnet')})")
    
    for vlan in unchanged_vlans:
        print(f"    VLAN {vlan['id']}: {vlan['name']} (unchanged)")
    
    # Check for missing VLANs
    current_vlan_ids = {v['id'] for v in tst_vlans}
    missing_vlans = set(EXPECTED_VLANS.keys()) - current_vlan_ids
    
    if missing_vlans:
        print(f"\n❌ Missing VLANs that should be created:")
        for vlan_id in sorted(missing_vlans):
            print(f"    VLAN {vlan_id}: {EXPECTED_VLANS[vlan_id]}")
    
    # Migration completeness
    total_expected = len(EXPECTED_VLANS)
    total_migrated = len([v for v in tst_vlans if v['id'] in EXPECTED_VLANS])
    completeness = (total_migrated / total_expected) * 100
    
    print(f"\nMigration Completeness: {completeness:.1f}% ({total_migrated}/{total_expected} VLANs)")
    
    return completeness == 100

def compare_firewall_rules_detailed(tst_rules, azp_rules):
    """Detailed firewall rules comparison"""
    print("\nFIREWALL RULES DETAILED ANALYSIS")
    print("=" * 80)
    
    tst_rule_list = tst_rules.get('rules', [])
    azp_rule_list = azp_rules.get('rules', [])
    
    print(f"\nRule Count:")
    print(f"  TST 01: {len(tst_rule_list)} rules")
    print(f"  AZP 30: {len(azp_rule_list)} rules")
    print(f"  NEO 07 expected: ~95 rules")
    
    # Analyze rule sources
    tst_comments = defaultdict(int)
    for rule in tst_rule_list:
        comment = rule.get('comment', 'No comment')
        if 'NEO' in comment.upper():
            tst_comments['NEO 07'] += 1
        elif 'AZP' in comment.upper():
            tst_comments['AZP 30'] += 1
        else:
            tst_comments['Other'] += 1
    
    print(f"\nRule Sources (based on comments):")
    for source, count in tst_comments.items():
        print(f"  {source}: {count} rules")
    
    # Policy breakdown
    tst_policy_counts = defaultdict(int)
    azp_policy_counts = defaultdict(int)
    
    for rule in tst_rule_list:
        tst_policy_counts[rule.get('policy', 'unknown')] += 1
    
    for rule in azp_rule_list:
        azp_policy_counts[rule.get('policy', 'unknown')] += 1
    
    print(f"\nRules by Policy Type:")
    all_policies = set(tst_policy_counts.keys()) | set(azp_policy_counts.keys())
    for policy in sorted(all_policies):
        print(f"  {policy}: TST 01={tst_policy_counts[policy]}, AZP 30={azp_policy_counts[policy]}")
    
    # Check for proper VLAN references in rules
    vlan_refs = {'old': 0, 'new': 0, 'other': 0}
    for rule in tst_rule_list:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        
        for addr in [src, dst]:
            if 'VLAN' in addr:
                vlan_num = ''.join(filter(str.isdigit, addr.split('/')[-1]))
                if vlan_num:
                    vlan_id = int(vlan_num)
                    if vlan_id in VLAN_MAPPING and VLAN_MAPPING[vlan_id] != vlan_id:
                        vlan_refs['old'] += 1
                    elif vlan_id in EXPECTED_VLANS:
                        vlan_refs['new'] += 1
                    else:
                        vlan_refs['other'] += 1
    
    print(f"\nVLAN References in Rules:")
    print(f"  Old VLAN IDs: {vlan_refs['old']} references")
    print(f"  New VLAN IDs: {vlan_refs['new']} references")
    print(f"  Other: {vlan_refs['other']} references")
    
    return len(tst_rule_list) > 50  # Basic check for sufficient rules

def analyze_switch_port_configuration(network_id):
    """Analyze switch port VLAN assignments"""
    print("\nSWITCH PORT CONFIGURATION ANALYSIS")
    print("=" * 80)
    
    # Get switches
    switches_url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = make_api_request(switches_url)
    
    if not devices:
        print("  ⚠️  Unable to retrieve devices")
        return
    
    switches = [d for d in devices if d.get('model', '').startswith('MS')]
    
    if not switches:
        print("  No switches found in network")
        return
    
    print(f"\nSwitches found: {len(switches)}")
    
    total_ports = 0
    vlan_assignments = defaultdict(int)
    
    for switch in switches:
        print(f"\n  {switch.get('name', 'Unknown')} ({switch['serial']}):")
        
        # Get switch ports
        ports_url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
        ports = make_api_request(ports_url)
        
        if ports:
            total_ports += len(ports)
            
            for port in ports:
                vlan = port.get('vlan')
                if vlan:
                    vlan_assignments[vlan] += 1
    
    print(f"\nTotal ports analyzed: {total_ports}")
    print(f"\nVLAN Assignments:")
    
    # Categorize VLAN assignments
    old_vlan_ports = 0
    new_vlan_ports = 0
    
    for vlan_id, count in sorted(vlan_assignments.items()):
        status = ""
        if vlan_id in VLAN_MAPPING and VLAN_MAPPING[vlan_id] != vlan_id:
            status = " (OLD - needs update)"
            old_vlan_ports += count
        elif vlan_id in EXPECTED_VLANS:
            status = " (NEW - correct)"
            new_vlan_ports += count
        
        print(f"  VLAN {vlan_id}: {count} ports{status}")
    
    if old_vlan_ports > 0:
        print(f"\n❌ Ports still using old VLAN IDs: {old_vlan_ports}")
    if new_vlan_ports > 0:
        print(f"✅ Ports using new VLAN IDs: {new_vlan_ports}")

def generate_detailed_summary(results):
    """Generate detailed summary with actionable items"""
    print("\n" + "=" * 80)
    print("MIGRATION VERIFICATION DETAILED SUMMARY")
    print("=" * 80)
    print(f"\nVerification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source Configuration: AZP 30")
    print(f"Target Network: TST 01")
    
    # Overall migration status
    if results.get('vlan_migration_complete'):
        print("\n✅ VLAN MIGRATION: COMPLETE")
    else:
        print("\n⚠️  VLAN MIGRATION: PARTIAL")
        print("   Action Required: Remove old VLANs after confirming switch port updates")
    
    # Component checklist
    print("\nComponent Checklist:")
    components = [
        ("VLANs Created", results.get('vlans_created', False)),
        ("Old VLANs Removed", results.get('old_vlans_removed', False)),
        ("Group Policies", results.get('group_policies', False)),
        ("Firewall Rules", results.get('firewall_rules', False)),
        ("Syslog Configuration", results.get('syslog', False)),
        ("Switch Port Updates", results.get('switch_ports_updated', False))
    ]
    
    for component, status in components:
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}")
    
    # Next steps
    print("\nNext Steps:")
    if not results.get('old_vlans_removed'):
        print("  1. Update all switch ports to use new VLAN IDs")
        print("  2. Remove old VLANs (1, 101, 201, 801, 802)")
    if not results.get('switch_ports_updated'):
        print("  3. Run switch port migration script")
    if results.get('firewall_vlan_refs'):
        print("  4. Update firewall rules to reference new VLAN IDs")
    
    print("\nConfiguration Notes:")
    print("  - IP addresses use test prefix 10.255.255.x")
    print("  - Firewall rules based on NEO 07 configuration")
    print("  - DHCP relay converted to DHCP server for test network")
    print("  - Group policy IDs have been remapped")

def main():
    """Main verification function"""
    print("TST 01 Network Migration Verification - Enhanced")
    print("=" * 80)
    
    results = {}
    
    # 1. Get current TST 01 configuration
    print("\nFetching TST 01 configuration...")
    tst_vlans_url = f"{BASE_URL}/networks/{TST_01_NETWORK_ID}/appliance/vlans"
    tst_vlans = make_api_request(tst_vlans_url) or []
    
    if tst_vlans:
        # Analyze VLAN migration status
        results['vlan_migration_complete'] = analyze_vlan_migration_status(tst_vlans)
        results['vlans_created'] = any(v['id'] in EXPECTED_VLANS for v in tst_vlans)
        results['old_vlans_removed'] = not any(v['id'] in [1, 101, 201, 801, 802] for v in tst_vlans)
    
    # 2. Check Group Policies
    print("\nChecking group policies...")
    tst_policies_url = f"{BASE_URL}/networks/{TST_01_NETWORK_ID}/groupPolicies"
    tst_policies = make_api_request(tst_policies_url) or []
    
    if tst_policies:
        print(f"  Found {len(tst_policies)} group policies")
        for policy in tst_policies:
            print(f"    ID {policy['groupPolicyId']}: {policy['name']}")
        results['group_policies'] = len(tst_policies) >= 3
    
    # 3. Analyze Firewall Rules
    print("\nAnalyzing firewall rules...")
    tst_fw_url = f"{BASE_URL}/networks/{TST_01_NETWORK_ID}/appliance/firewall/l3FirewallRules"
    azp_fw_url = f"{BASE_URL}/networks/{AZP_30_NETWORK_ID}/appliance/firewall/l3FirewallRules"
    
    tst_fw = make_api_request(tst_fw_url) or {}
    azp_fw = make_api_request(azp_fw_url) or {}
    
    if tst_fw:
        results['firewall_rules'] = compare_firewall_rules_detailed(tst_fw, azp_fw)
        
        # Check for old VLAN references
        old_refs = 0
        for rule in tst_fw.get('rules', []):
            for field in ['srcCidr', 'destCidr']:
                value = str(rule.get(field, ''))
                if any(f"VLAN{vid}" in value for vid in [1, 101, 201, 801, 802]):
                    old_refs += 1
        
        results['firewall_vlan_refs'] = old_refs > 0
        if old_refs > 0:
            print(f"\n⚠️  Found {old_refs} firewall rules referencing old VLAN IDs")
    
    # 4. Check Syslog
    print("\nChecking syslog configuration...")
    tst_syslog_url = f"{BASE_URL}/networks/{TST_01_NETWORK_ID}/syslogServers"
    tst_syslog = make_api_request(tst_syslog_url) or {}
    
    if tst_syslog and tst_syslog.get('servers'):
        servers = tst_syslog['servers']
        print(f"  Found {len(servers)} syslog server(s)")
        for server in servers:
            print(f"    {server['host']}:{server['port']}")
        results['syslog'] = len(servers) > 0
    
    # 5. Analyze Switch Ports
    analyze_switch_port_configuration(TST_01_NETWORK_ID)
    
    # Check if switch ports are updated
    # This is a simplified check - in reality would need to verify each port
    results['switch_ports_updated'] = False  # Requires manual verification
    
    # Generate summary
    generate_detailed_summary(results)
    
    # Save detailed report
    report_file = f"tst_01_enhanced_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'network_id': TST_01_NETWORK_ID,
        'results': results,
        'vlan_analysis': {
            'current_vlans': [{'id': v['id'], 'name': v['name']} for v in tst_vlans],
            'expected_vlans': EXPECTED_VLANS,
            'migration_complete': results.get('vlan_migration_complete', False)
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()