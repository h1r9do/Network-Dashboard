#!/usr/bin/env python3
"""
Verify VLAN Migration
====================

This script verifies that VLAN migration was completed successfully.

Usage:
    python3 verify_vlan_migration.py --network-id <network_id>

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

# Expected new VLAN IDs after migration
EXPECTED_VLANS = {
    100: 'Data',
    200: 'Voice',
    400: 'Credit Card',
    410: 'Scanner',
    300: 'AP Mgmt',
    800: 'Guest',
    801: 'IOT',
    802: 'IoT Network',
    803: 'IoT Wireless'
}

# Old VLAN IDs that should NOT exist
OLD_VLANS = [1, 101, 201, 301]

def check_vlans(network_id):
    """Check VLAN configuration"""
    print("\n" + "="*60)
    print("Checking VLANs...")
    print("="*60)
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("❌ Failed to get VLANs")
        return False
    
    vlans = response.json()
    current_vlan_ids = [v['id'] for v in vlans]
    
    # Check for old VLANs that should not exist
    old_found = []
    for old_id in OLD_VLANS:
        if old_id in current_vlan_ids:
            old_found.append(old_id)
    
    if old_found:
        print(f"❌ Old VLANs still exist: {old_found}")
        print("   These should have been migrated to new IDs")
        all_good = False
    else:
        print("✅ No old VLANs found")
        all_good = True
    
    # Check for expected new VLANs
    print("\nChecking expected VLANs:")
    for vlan_id, purpose in EXPECTED_VLANS.items():
        if vlan_id in current_vlan_ids:
            vlan = next(v for v in vlans if v['id'] == vlan_id)
            print(f"✅ VLAN {vlan_id} ({purpose}): {vlan.get('subnet', 'No subnet')}")
        else:
            print(f"❌ VLAN {vlan_id} ({purpose}): NOT FOUND")
            all_good = False
    
    # Check DHCP settings preserved
    print("\nChecking DHCP settings:")
    for vlan in vlans:
        if vlan['id'] in EXPECTED_VLANS:
            dhcp_mode = vlan.get('dhcpHandling', 'Unknown')
            
            # Check for DHCP options (VoIP)
            if vlan['id'] == 200 and vlan.get('dhcpOptions'):
                print(f"✅ VLAN 200 (Voice): DHCP options preserved")
            
            # Check for fixed IPs
            if vlan.get('fixedIpAssignments'):
                count = len(vlan['fixedIpAssignments'])
                print(f"✅ VLAN {vlan['id']}: {count} DHCP reservations preserved")
    
    return all_good

def check_firewall_rules(network_id):
    """Check firewall rules for old VLAN references"""
    print("\n" + "="*60)
    print("Checking Firewall Rules...")
    print("="*60)
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("❌ Failed to get firewall rules")
        return False
    
    rules = response.json().get('rules', [])
    print(f"Total rules: {len(rules)}")
    
    # Check for old VLAN references
    old_refs_found = False
    for i, rule in enumerate(rules):
        src = rule.get('srcCidr', '')
        dst = rule.get('destCidr', '')
        
        for old_id in OLD_VLANS:
            if f'VLAN({old_id}).' in src or f'VLAN({old_id}).' in dst:
                print(f"❌ Rule {i+1}: Contains old VLAN {old_id} reference")
                print(f"   Comment: {rule.get('comment', 'No comment')}")
                old_refs_found = True
    
    if not old_refs_found:
        print("✅ No old VLAN references found in firewall rules")
    
    # Check for new VLAN references
    new_refs = {}
    for rule in rules:
        src = rule.get('srcCidr', '')
        dst = rule.get('destCidr', '')
        
        for new_id in [100, 200, 400, 410]:
            if f'VLAN({new_id}).' in src or f'VLAN({new_id}).' in dst:
                new_refs[new_id] = new_refs.get(new_id, 0) + 1
    
    if new_refs:
        print("\nNew VLAN references found:")
        for vlan_id, count in sorted(new_refs.items()):
            print(f"  VLAN {vlan_id}: {count} references")
    
    return not old_refs_found

def check_switch_ports(network_id):
    """Check switch port VLAN assignments"""
    print("\n" + "="*60)
    print("Checking Switch Ports...")
    print("="*60)
    
    url = f"{BASE_URL}/networks/{network_id}/devices"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("❌ Failed to get devices")
        return False
    
    devices = response.json()
    switches = [d for d in devices if d['model'].startswith('MS')]
    
    if not switches:
        print("No switches found in network")
        return True
    
    all_good = True
    
    for switch in switches:
        print(f"\nSwitch: {switch['name']}")
        
        url = f"{BASE_URL}/devices/{switch['serial']}/switch/ports"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ Failed to get ports for {switch['name']}")
            continue
        
        ports = response.json()
        
        # Check for old VLAN assignments
        old_vlan_ports = []
        for port in ports:
            # Check access VLAN
            if port.get('vlan') in OLD_VLANS:
                old_vlan_ports.append(f"Port {port['portId']}: VLAN {port['vlan']}")
            
            # Check voice VLAN
            if port.get('voiceVlan') in OLD_VLANS:
                old_vlan_ports.append(f"Port {port['portId']}: Voice VLAN {port['voiceVlan']}")
        
        if old_vlan_ports:
            print(f"❌ Ports with old VLAN assignments:")
            for p in old_vlan_ports[:5]:  # Show first 5
                print(f"   {p}")
            if len(old_vlan_ports) > 5:
                print(f"   ... and {len(old_vlan_ports)-5} more")
            all_good = False
        else:
            print("✅ No ports with old VLAN assignments")
        
        # Count new VLAN usage
        new_vlan_count = {}
        for port in ports:
            vlan = port.get('vlan')
            if vlan in [100, 200, 400, 410]:
                new_vlan_count[vlan] = new_vlan_count.get(vlan, 0) + 1
            
            voice_vlan = port.get('voiceVlan')
            if voice_vlan == 200:
                new_vlan_count['200_voice'] = new_vlan_count.get('200_voice', 0) + 1
        
        if new_vlan_count:
            print("  New VLAN usage:")
            for vlan, count in sorted(new_vlan_count.items()):
                if isinstance(vlan, str) and vlan.endswith('_voice'):
                    print(f"    Voice VLAN 200: {count} ports")
                else:
                    print(f"    VLAN {vlan}: {count} ports")
    
    return all_good

def check_mx_ports(network_id):
    """Check MX port VLAN assignments"""
    print("\n" + "="*60)
    print("Checking MX Ports...")
    print("="*60)
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/ports"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("❌ Failed to get MX ports")
        return False
    
    ports = response.json()
    
    # Check for old VLAN assignments
    old_vlan_ports = []
    for port in ports:
        if port.get('vlan') in OLD_VLANS:
            old_vlan_ports.append(f"Port {port['number']}: VLAN {port['vlan']}")
        
        # Check allowed VLANs on trunk ports
        if port.get('type') == 'trunk' and port.get('allowedVlans'):
            allowed = port['allowedVlans']
            if allowed != 'all':
                for old_id in OLD_VLANS:
                    if str(old_id) in allowed:
                        old_vlan_ports.append(f"Port {port['number']}: Allows old VLAN {old_id}")
    
    if old_vlan_ports:
        print("❌ MX ports with old VLAN references:")
        for p in old_vlan_ports:
            print(f"   {p}")
        return False
    else:
        print("✅ No MX ports with old VLAN assignments")
        return True

def generate_summary(network_id, results):
    """Generate verification summary"""
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nThe VLAN migration appears to be complete:")
        print("- Old VLANs (1, 101, 201, 301) have been removed")
        print("- New VLANs (100, 200, 400, 410) are configured")
        print("- Firewall rules updated with new VLAN references")
        print("- Switch ports migrated to new VLANs")
        print("- MX ports updated")
    else:
        print("\n❌ SOME CHECKS FAILED!")
        print("\nIssues found:")
        for check, passed in results.items():
            if not passed:
                print(f"- {check}: FAILED")
        
        print("\nRecommended actions:")
        print("1. Review the specific failures above")
        print("2. Run migration script again if needed")
        print("3. Check for any manual configurations that need updating")
    
    # Save report
    report_file = f"vlan_verification_report_{network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(f"VLAN Migration Verification Report\n")
        f.write(f"Network ID: {network_id}\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Overall Status: {'PASSED' if all_passed else 'FAILED'}\n\n")
        
        for check, passed in results.items():
            f.write(f"{check}: {'PASSED' if passed else 'FAILED'}\n")
    
    print(f"\nReport saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Verify VLAN migration completion')
    parser.add_argument('--network-id', required=True, help='Network ID to verify')
    
    args = parser.parse_args()
    
    print("🔍 VLAN Migration Verification Tool")
    print("=" * 60)
    print(f"Verifying network: {args.network_id}")
    
    # Run checks
    results = {
        'VLANs': check_vlans(args.network_id),
        'Firewall Rules': check_firewall_rules(args.network_id),
        'Switch Ports': check_switch_ports(args.network_id),
        'MX Ports': check_mx_ports(args.network_id)
    }
    
    # Generate summary
    generate_summary(args.network_id, results)

if __name__ == "__main__":
    main()