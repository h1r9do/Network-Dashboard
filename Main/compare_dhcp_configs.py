#!/usr/bin/env python3
"""
Compare DHCP configurations between AZP 30 and TST 01 networks
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def extract_dhcp_info(vlan: Dict[str, Any]) -> Dict[str, Any]:
    """Extract DHCP-related information from a VLAN configuration"""
    return {
        'id': vlan.get('id'),
        'name': vlan.get('name'),
        'subnet': vlan.get('subnet'),
        'applianceIp': vlan.get('applianceIp'),
        'dhcpHandling': vlan.get('dhcpHandling', 'Not specified'),
        'dhcpLeaseTime': vlan.get('dhcpLeaseTime', 'Not specified'),
        'dhcpOptions': vlan.get('dhcpOptions', []),
        'dhcpRelayServerIps': vlan.get('dhcpRelayServerIps', []),
        'dnsNameservers': vlan.get('dnsNameservers', 'Not specified'),
        'fixedIpAssignments': vlan.get('fixedIpAssignments', {}),
        'reservedIpRanges': vlan.get('reservedIpRanges', []),
        'groupPolicyId': vlan.get('groupPolicyId', 'Not specified')
    }

def format_dhcp_options(options: List[Dict[str, Any]]) -> str:
    """Format DHCP options for display"""
    if not options:
        return "None"
    
    formatted = []
    for opt in options:
        code = opt.get('code', 'Unknown')
        opt_type = opt.get('type', 'Unknown')
        value = opt.get('value', 'Unknown')
        
        # Add descriptions for common DHCP option codes
        descriptions = {
            '42': 'NTP Servers',
            '66': 'TFTP Server Name',
            '150': 'TFTP Server IP',
            '3': 'Default Gateway',
            '6': 'DNS Servers',
            '15': 'Domain Name',
            '119': 'Domain Search',
            '252': 'WPAD'
        }
        
        desc = descriptions.get(code, f'Option {code}')
        formatted.append(f"    - {desc} (Code {code}, Type: {opt_type}): {value}")
    
    return '\n'.join(formatted)

def compare_vlans(azp_vlans: List[Dict], tst_vlans: List[Dict]) -> None:
    """Compare VLAN configurations between AZP 30 and TST 01"""
    
    # Create lookup dictionaries by VLAN ID
    azp_dict = {v['id']: v for v in azp_vlans}
    tst_dict = {v['id']: v for v in tst_vlans}
    
    # Find common VLANs
    common_vlan_ids = set(azp_dict.keys()) & set(tst_dict.keys())
    azp_only_ids = set(azp_dict.keys()) - set(tst_dict.keys())
    tst_only_ids = set(tst_dict.keys()) - set(azp_dict.keys())
    
    print("=" * 80)
    print("DHCP CONFIGURATION COMPARISON: AZP 30 vs TST 01")
    print("=" * 80)
    print(f"Comparison Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Summary
    print("SUMMARY:")
    print(f"- Common VLANs: {len(common_vlan_ids)}")
    print(f"- VLANs only in AZP 30: {len(azp_only_ids)}")
    print(f"- VLANs only in TST 01: {len(tst_only_ids)}")
    print()
    
    # Detailed comparison for common VLANs
    print("=" * 80)
    print("DETAILED VLAN COMPARISON:")
    print("=" * 80)
    
    for vlan_id in sorted(common_vlan_ids):
        azp_vlan = extract_dhcp_info(azp_dict[vlan_id])
        tst_vlan = extract_dhcp_info(tst_dict[vlan_id])
        
        print(f"\nVLAN {vlan_id} - {azp_vlan['name']}:")
        print("-" * 60)
        
        # Compare DHCP handling mode
        if azp_vlan['dhcpHandling'] != tst_vlan['dhcpHandling']:
            print(f"  ❌ DHCP Handling Mode:")
            print(f"     AZP 30: {azp_vlan['dhcpHandling']}")
            print(f"     TST 01: {tst_vlan['dhcpHandling']}")
            print(f"     ACTION: Update TST 01 to use '{azp_vlan['dhcpHandling']}'")
        else:
            print(f"  ✓ DHCP Handling Mode: {azp_vlan['dhcpHandling']}")
        
        # For DHCP relay mode, compare relay servers
        if azp_vlan['dhcpHandling'] == 'Relay DHCP to another server':
            if azp_vlan['dhcpRelayServerIps'] != tst_vlan['dhcpRelayServerIps']:
                print(f"  ❌ DHCP Relay Servers:")
                print(f"     AZP 30: {', '.join(azp_vlan['dhcpRelayServerIps'])}")
                print(f"     TST 01: {', '.join(tst_vlan['dhcpRelayServerIps']) if tst_vlan['dhcpRelayServerIps'] else 'None'}")
                print(f"     ACTION: Update TST 01 relay servers to: {', '.join(azp_vlan['dhcpRelayServerIps'])}")
        
        # For DHCP server mode, compare additional settings
        if azp_vlan['dhcpHandling'] == 'Run a DHCP server':
            # Compare lease time
            if azp_vlan['dhcpLeaseTime'] != tst_vlan['dhcpLeaseTime']:
                print(f"  ❌ DHCP Lease Time:")
                print(f"     AZP 30: {azp_vlan['dhcpLeaseTime']}")
                print(f"     TST 01: {tst_vlan['dhcpLeaseTime']}")
                print(f"     ACTION: Update TST 01 lease time to '{azp_vlan['dhcpLeaseTime']}'")
            else:
                print(f"  ✓ DHCP Lease Time: {azp_vlan['dhcpLeaseTime']}")
            
            # Compare DHCP options
            azp_options = sorted(azp_vlan['dhcpOptions'], key=lambda x: x.get('code', ''))
            tst_options = sorted(tst_vlan['dhcpOptions'], key=lambda x: x.get('code', ''))
            
            if azp_options != tst_options:
                print(f"  ❌ DHCP Options:")
                print(f"     AZP 30:")
                print(format_dhcp_options(azp_options) if azp_options else "       None")
                print(f"     TST 01:")
                print(format_dhcp_options(tst_options) if tst_options else "       None")
                if azp_options:
                    print(f"     ACTION: Configure TST 01 with AZP 30's DHCP options")
            elif azp_options:
                print(f"  ✓ DHCP Options configured:")
                print(format_dhcp_options(azp_options))
        
        # Compare DNS servers
        if azp_vlan['dnsNameservers'] != tst_vlan['dnsNameservers']:
            print(f"  ❌ DNS Servers:")
            print(f"     AZP 30: {azp_vlan['dnsNameservers']}")
            print(f"     TST 01: {tst_vlan['dnsNameservers']}")
            print(f"     ACTION: Update TST 01 DNS servers to '{azp_vlan['dnsNameservers']}'")
        else:
            print(f"  ✓ DNS Servers: {azp_vlan['dnsNameservers']}")
        
        # Compare fixed IP assignments
        if azp_vlan['fixedIpAssignments'] != tst_vlan['fixedIpAssignments']:
            print(f"  ❌ Fixed IP Assignments:")
            azp_count = len(azp_vlan['fixedIpAssignments'])
            tst_count = len(tst_vlan['fixedIpAssignments'])
            print(f"     AZP 30: {azp_count} assignments")
            print(f"     TST 01: {tst_count} assignments")
            if azp_count > 0:
                print(f"     ACTION: Configure TST 01 with AZP 30's fixed IP assignments")
                for mac, info in azp_vlan['fixedIpAssignments'].items():
                    print(f"       - {mac}: {info['ip']} ({info['name']})")
        elif azp_vlan['fixedIpAssignments']:
            print(f"  ✓ Fixed IP Assignments: {len(azp_vlan['fixedIpAssignments'])} configured")
        
        # Compare reserved IP ranges
        if azp_vlan['reservedIpRanges'] != tst_vlan['reservedIpRanges']:
            print(f"  ❌ Reserved IP Ranges:")
            print(f"     AZP 30: {azp_vlan['reservedIpRanges']}")
            print(f"     TST 01: {tst_vlan['reservedIpRanges']}")
            if azp_vlan['reservedIpRanges']:
                print(f"     ACTION: Configure TST 01 with AZP 30's reserved IP ranges")
        elif azp_vlan['reservedIpRanges']:
            print(f"  ✓ Reserved IP Ranges: {azp_vlan['reservedIpRanges']}")
    
    # VLANs only in AZP 30
    if azp_only_ids:
        print("\n" + "=" * 80)
        print("VLANs ONLY IN AZP 30 (Not in TST 01):")
        print("=" * 80)
        for vlan_id in sorted(azp_only_ids):
            vlan = azp_dict[vlan_id]
            print(f"\nVLAN {vlan_id} - {vlan['name']}:")
            print(f"  Subnet: {vlan['subnet']}")
            print(f"  DHCP Handling: {vlan.get('dhcpHandling', 'Not specified')}")
    
    # VLANs only in TST 01
    if tst_only_ids:
        print("\n" + "=" * 80)
        print("VLANs ONLY IN TST 01 (Not in AZP 30):")
        print("=" * 80)
        for vlan_id in sorted(tst_only_ids):
            vlan = tst_dict[vlan_id]
            print(f"\nVLAN {vlan_id} - {vlan['name']}:")
            print(f"  Subnet: {vlan['subnet']}")
            print(f"  DHCP Handling: {vlan.get('dhcpHandling', 'Not specified')}")
    
    # Summary of required changes
    print("\n" + "=" * 80)
    print("SUMMARY OF REQUIRED CHANGES FOR TST 01:")
    print("=" * 80)
    
    changes_needed = False
    
    for vlan_id in sorted(common_vlan_ids):
        azp_vlan = extract_dhcp_info(azp_dict[vlan_id])
        tst_vlan = extract_dhcp_info(tst_dict[vlan_id])
        
        vlan_changes = []
        
        if azp_vlan['dhcpHandling'] != tst_vlan['dhcpHandling']:
            vlan_changes.append(f"Change DHCP handling to '{azp_vlan['dhcpHandling']}'")
            if azp_vlan['dhcpHandling'] == 'Relay DHCP to another server' and azp_vlan['dhcpRelayServerIps']:
                vlan_changes.append(f"Set relay servers to: {', '.join(azp_vlan['dhcpRelayServerIps'])}")
        
        if azp_vlan['dhcpHandling'] == 'Run a DHCP server':
            if azp_vlan['dhcpLeaseTime'] != tst_vlan['dhcpLeaseTime']:
                vlan_changes.append(f"Change lease time to '{azp_vlan['dhcpLeaseTime']}'")
            
            if azp_vlan['dhcpOptions'] != tst_vlan['dhcpOptions'] and azp_vlan['dhcpOptions']:
                vlan_changes.append("Configure DHCP options")
        
        if azp_vlan['dnsNameservers'] != tst_vlan['dnsNameservers']:
            vlan_changes.append(f"Update DNS servers to '{azp_vlan['dnsNameservers']}'")
        
        if azp_vlan['fixedIpAssignments'] != tst_vlan['fixedIpAssignments'] and azp_vlan['fixedIpAssignments']:
            vlan_changes.append(f"Add {len(azp_vlan['fixedIpAssignments'])} fixed IP assignments")
        
        if vlan_changes:
            changes_needed = True
            print(f"\nVLAN {vlan_id} - {azp_vlan['name']}:")
            for change in vlan_changes:
                print(f"  • {change}")
    
    if not changes_needed:
        print("\n✓ No DHCP configuration changes needed - TST 01 matches AZP 30")

def main():
    """Main function"""
    # Load configurations
    azp_config = load_config('/usr/local/bin/Main/azp_30_full_config_20250709_170149.json')
    tst_config = load_config('/usr/local/bin/Main/tst_01_full_config_20250709_170125.json')
    
    # Extract VLANs
    azp_vlans = azp_config.get('vlans', [])
    tst_vlans = tst_config.get('vlans', [])
    
    # Compare configurations
    compare_vlans(azp_vlans, tst_vlans)

if __name__ == "__main__":
    main()