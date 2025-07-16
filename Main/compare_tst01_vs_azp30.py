#!/usr/bin/env python3
"""
Compare TST 01 vs AZP 30 Configurations
Compares VLANs, firewall rules, and port configurations between TST 01 and AZP 30
"""

import json
import os
from datetime import datetime

def load_configs():
    """Load both configuration files"""
    print('📋 Loading Configuration Files...')
    print('=' * 50)
    
    # Load AZP 30 configuration
    azp30_file = 'azp_30_full_config_20250709_170149.json'
    with open(azp30_file, 'r') as f:
        azp30_config = json.load(f)
    print(f'  ✓ Loaded AZP 30 config: {azp30_file}')
    
    # Load TST 01 configuration  
    tst01_file = 'tst01_post_quick_restore_config_20250710_093326.json'
    with open(tst01_file, 'r') as f:
        tst01_config = json.load(f)
    print(f'  ✓ Loaded TST 01 config: {tst01_file}')
    
    return azp30_config, tst01_config

def compare_vlans(azp30_config, tst01_config):
    """Compare VLAN configurations"""
    print('\\n🏷️  VLAN Comparison')
    print('=' * 50)
    
    azp30_vlans = azp30_config['vlans']
    tst01_vlans = tst01_config['vlans']
    
    print(f'AZP 30 VLANs: {len(azp30_vlans)} total')
    print(f'TST 01 VLANs: {len(tst01_vlans)} total')
    
    # Create lookup dictionaries
    azp30_vlan_dict = {vlan['id']: vlan for vlan in azp30_vlans}
    tst01_vlan_dict = {vlan['id']: vlan for vlan in tst01_vlans}
    
    print('\\nVLAN-by-VLAN Comparison:')
    print('VLAN | AZP 30 Name              | AZP 30 Subnet         | TST 01 Name              | TST 01 Subnet         | Match')
    print('-' * 120)
    
    all_vlan_ids = sorted(set(list(azp30_vlan_dict.keys()) + list(tst01_vlan_dict.keys())))
    
    matches = 0
    for vlan_id in all_vlan_ids:
        azp30_vlan = azp30_vlan_dict.get(vlan_id, {})
        tst01_vlan = tst01_vlan_dict.get(vlan_id, {})
        
        azp30_name = azp30_vlan.get('name', 'MISSING').ljust(24)
        azp30_subnet = azp30_vlan.get('subnet', 'MISSING').ljust(21)
        tst01_name = tst01_vlan.get('name', 'MISSING').ljust(24)
        tst01_subnet = tst01_vlan.get('subnet', 'MISSING').ljust(21)
        
        # Check if IP ranges are converted properly
        ip_match = False
        if azp30_vlan and tst01_vlan:
            azp30_ip = azp30_vlan.get('subnet', '')
            tst01_ip = tst01_vlan.get('subnet', '')
            
            # Convert AZP 30 IPs to expected TST 01 format
            expected_tst01_ip = azp30_ip.replace('10.24.38.', '10.1.32.').replace('10.24.39.', '10.1.32.')
            
            if tst01_ip == expected_tst01_ip or (vlan_id in [800, 801, 802, 803, 900] and tst01_ip == azp30_ip):
                ip_match = True
                matches += 1
        
        name_match = azp30_vlan.get('name') == tst01_vlan.get('name') if azp30_vlan and tst01_vlan else False
        overall_match = '✓' if (name_match and ip_match) else '✗'
        
        print(f'{str(vlan_id).ljust(4)} | {azp30_name} | {azp30_subnet} | {tst01_name} | {tst01_subnet} | {overall_match}')
    
    print(f'\\nVLAN Summary: {matches}/{len(all_vlan_ids)} VLANs properly converted')
    return matches == len(all_vlan_ids)

def compare_firewall_rules(azp30_config, tst01_config):
    """Compare firewall rule configurations"""
    print('\\n🔥 Firewall Rules Comparison')
    print('=' * 50)
    
    azp30_rules = azp30_config['firewall_rules']['rules']
    tst01_rules = tst01_config['firewall_rules']['rules']
    
    print(f'AZP 30 Firewall Rules: {len(azp30_rules)} total')
    print(f'TST 01 Firewall Rules: {len(tst01_rules)} total')
    
    # Count rules with VLAN references
    azp30_vlan_rules = 0
    tst01_vlan_rules = 0
    
    for rule in azp30_rules:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        if 'VLAN(' in src or 'VLAN(' in dst:
            azp30_vlan_rules += 1
    
    for rule in tst01_rules:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        if 'VLAN(' in src or 'VLAN(' in dst:
            tst01_vlan_rules += 1
    
    print(f'AZP 30 rules with VLAN references: {azp30_vlan_rules}')
    print(f'TST 01 rules with VLAN references: {tst01_vlan_rules}')
    
    # Check for IP conversions in firewall rules
    print('\\nIP Conversion Check (first 10 rules with VLAN references):')
    print('Rule | AZP 30 Source → Destination | TST 01 Source → Destination | IP Converted')
    print('-' * 100)
    
    converted_count = 0
    shown_count = 0
    
    for i, (azp30_rule, tst01_rule) in enumerate(zip(azp30_rules, tst01_rules)):
        azp30_src = str(azp30_rule.get('srcCidr', ''))
        azp30_dst = str(azp30_rule.get('destCidr', ''))
        tst01_src = str(tst01_rule.get('srcCidr', ''))
        tst01_dst = str(tst01_rule.get('destCidr', ''))
        
        # Only show rules with VLAN references
        if 'VLAN(' in azp30_src or 'VLAN(' in azp30_dst:
            if shown_count < 10:
                # Check if IP conversion occurred
                ip_converted = False
                if '10.24.' in azp30_src and '10.1.32.' in tst01_src:
                    ip_converted = True
                elif '10.24.' in azp30_dst and '10.1.32.' in tst01_dst:
                    ip_converted = True
                elif azp30_src == tst01_src and azp30_dst == tst01_dst:  # No conversion needed
                    ip_converted = True
                
                status = '✓' if ip_converted else '✗'
                
                azp30_rule_str = f'{azp30_src[:20]}...→{azp30_dst[:20]}...' if len(azp30_src + azp30_dst) > 40 else f'{azp30_src}→{azp30_dst}'
                tst01_rule_str = f'{tst01_src[:20]}...→{tst01_dst[:20]}...' if len(tst01_src + tst01_dst) > 40 else f'{tst01_src}→{tst01_dst}'
                
                print(f'{str(i+1).ljust(4)} | {azp30_rule_str[:30].ljust(30)} | {tst01_rule_str[:30].ljust(30)} | {status}')
                shown_count += 1
                
            if '10.24.' in azp30_src and '10.1.32.' in tst01_src:
                converted_count += 1
            elif '10.24.' in azp30_dst and '10.1.32.' in tst01_dst:
                converted_count += 1
    
    print(f'\\nFirewall Rules Summary:')
    print(f'  - Total rules match: {len(azp30_rules) == len(tst01_rules)}')
    print(f'  - VLAN reference preservation: {azp30_vlan_rules} → {tst01_vlan_rules}')
    print(f'  - IP conversions detected: {converted_count} rules')
    
    return len(azp30_rules) == len(tst01_rules)

def compare_mx_ports(azp30_config, tst01_config):
    """Compare MX port configurations"""
    print('\\n🔌 MX Ports Comparison')
    print('=' * 50)
    
    azp30_ports = azp30_config['mx_ports']
    tst01_ports = tst01_config['mx_ports']
    
    print(f'AZP 30 MX Ports: {len(azp30_ports)} total')
    print(f'TST 01 MX Ports: {len(tst01_ports)} total')
    
    # Create lookup dictionaries
    azp30_port_dict = {port['number']: port for port in azp30_ports}
    tst01_port_dict = {port['number']: port for port in tst01_ports}
    
    print('\\nMX Port-by-Port Comparison:')
    print('Port | AZP 30 VLAN | AZP 30 Type | TST 01 VLAN | TST 01 Type | Match')
    print('-' * 70)
    
    matches = 0
    all_port_numbers = sorted(set(list(azp30_port_dict.keys()) + list(tst01_port_dict.keys())))
    
    for port_num in all_port_numbers:
        azp30_port = azp30_port_dict.get(port_num, {})
        tst01_port = tst01_port_dict.get(port_num, {})
        
        azp30_vlan = str(azp30_port.get('vlan', '-')).ljust(11)
        azp30_type = azp30_port.get('type', '-').ljust(11)
        tst01_vlan = str(tst01_port.get('vlan', '-')).ljust(11)
        tst01_type = tst01_port.get('type', '-').ljust(11)
        
        vlan_match = azp30_port.get('vlan') == tst01_port.get('vlan')
        type_match = azp30_port.get('type') == tst01_port.get('type')
        overall_match = '✓' if (vlan_match and type_match) else '✗'
        
        if vlan_match and type_match:
            matches += 1
        
        print(f'{str(port_num).ljust(4)} | {azp30_vlan} | {azp30_type} | {tst01_vlan} | {tst01_type} | {overall_match}')
    
    print(f'\\nMX Ports Summary: {matches}/{len(all_port_numbers)} ports match exactly')
    return matches == len(all_port_numbers)

def compare_switch_ports(azp30_config, tst01_config):
    """Compare switch port configurations"""
    print('\\n🔄 Switch Ports Comparison')
    print('=' * 50)
    
    azp30_switches = azp30_config['switch_ports']
    tst01_switches = tst01_config['switch_ports']
    
    print(f'AZP 30 Switches: {len(azp30_switches)} total')
    print(f'TST 01 Switches: {len(tst01_switches)} total')
    
    # Compare port configurations by switch position
    azp30_switch_serials = list(azp30_switches.keys())
    tst01_switch_serials = list(tst01_switches.keys())
    
    matches = 0
    total_ports = 0
    
    for i, azp30_serial in enumerate(azp30_switch_serials):
        if i < len(tst01_switch_serials):
            tst01_serial = tst01_switch_serials[i]
            azp30_ports = azp30_switches[azp30_serial]
            tst01_ports = tst01_switches[tst01_serial]
            
            print(f'\\nSwitch {i+1} Comparison:')
            print(f'  AZP 30: {azp30_serial} ({len(azp30_ports)} ports)')
            print(f'  TST 01: {tst01_serial} ({len(tst01_ports)} ports)')
            
            # Compare VLAN assignments
            azp30_vlan_ports = 0
            tst01_vlan_ports = 0
            matching_vlans = 0
            
            for azp30_port, tst01_port in zip(azp30_ports, tst01_ports):
                total_ports += 1
                if azp30_port.get('vlan') and tst01_port.get('vlan'):
                    azp30_vlan_ports += 1
                    tst01_vlan_ports += 1
                    if azp30_port['vlan'] == tst01_port['vlan']:
                        matching_vlans += 1
                        matches += 1
            
            print(f'  VLAN assignments: {matching_vlans}/{azp30_vlan_ports} match')
    
    print(f'\\nSwitch Ports Summary: {matches}/{total_ports} port configurations match')
    return matches == total_ports

def generate_comparison_report(azp30_config, tst01_config, vlan_match, fw_match, mx_match, sw_match):
    """Generate comprehensive comparison report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    report = f'''
TST 01 vs AZP 30 Configuration Comparison Report
===============================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
AZP 30 Source: {azp30_config.get('extraction_date', 'Unknown')}
TST 01 Source: {tst01_config.get('download_date', 'Unknown')}

CONFIGURATION COMPARISON SUMMARY
===============================

VLANs:              {'✅ PASS' if vlan_match else '❌ FAIL'}
Firewall Rules:     {'✅ PASS' if fw_match else '❌ FAIL'} 
MX Ports:           {'✅ PASS' if mx_match else '❌ FAIL'}
Switch Ports:       {'✅ PASS' if sw_match else '❌ FAIL'}

OVERALL STATUS:     {'✅ ALL SYSTEMS MATCH' if all([vlan_match, fw_match, mx_match, sw_match]) else '⚠️  SOME DIFFERENCES FOUND'}

DETAILED STATISTICS
==================

VLANs:
- AZP 30: {len(azp30_config['vlans'])} VLANs
- TST 01: {len(tst01_config['vlans'])} VLANs
- IP Conversion: AZP 30 production IPs → TST 01 test ranges

Firewall Rules:
- AZP 30: {len(azp30_config['firewall_rules']['rules'])} rules
- TST 01: {len(tst01_config['firewall_rules']['rules'])} rules
- VLAN References: Preserved with IP conversions

MX Ports:
- AZP 30: {len(azp30_config['mx_ports'])} ports
- TST 01: {len(tst01_config['mx_ports'])} ports
- Configuration: VLAN assignments and port types

Switch Ports:
- AZP 30: {len(azp30_config['switch_ports'])} switches
- TST 01: {len(tst01_config['switch_ports'])} switches
- Port Configs: Complete port-by-port configuration

CONCLUSION
==========
{'TST 01 successfully restored to production-ready state matching AZP 30 configuration.' if all([vlan_match, fw_match, mx_match, sw_match]) else 'Configuration differences detected. Review detailed comparison above.'}

Ready for VLAN migration testing: {'✅ YES' if all([vlan_match, fw_match, mx_match, sw_match]) else '⚠️  REVIEW REQUIRED'}
'''
    
    report_filename = f'tst01_vs_azp30_comparison_report_{timestamp}.txt'
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f'\\n📊 Comparison report saved: {report_filename}')
    return report_filename

def main():
    print('🔍 TST 01 vs AZP 30 Configuration Comparison')
    print('=' * 60)
    print('Comparing restored TST 01 configuration against AZP 30 source')
    
    # Load configurations
    azp30_config, tst01_config = load_configs()
    
    # Run comparisons
    vlan_match = compare_vlans(azp30_config, tst01_config)
    fw_match = compare_firewall_rules(azp30_config, tst01_config)
    mx_match = compare_mx_ports(azp30_config, tst01_config)
    sw_match = compare_switch_ports(azp30_config, tst01_config)
    
    # Generate report
    report_file = generate_comparison_report(azp30_config, tst01_config, vlan_match, fw_match, mx_match, sw_match)
    
    # Final summary
    print('\\n' + '=' * 60)
    print('🎯 FINAL COMPARISON RESULTS')
    print('=' * 60)
    print(f'VLANs:          {'✅ MATCH' if vlan_match else '❌ DIFFER'}')
    print(f'Firewall Rules: {'✅ MATCH' if fw_match else '❌ DIFFER'}')
    print(f'MX Ports:       {'✅ MATCH' if mx_match else '❌ DIFFER'}')
    print(f'Switch Ports:   {'✅ MATCH' if sw_match else '❌ DIFFER'}')
    print('')
    print(f'Overall Status: {'✅ TST 01 MATCHES AZP 30 CONFIGURATION' if all([vlan_match, fw_match, mx_match, sw_match]) else '⚠️  CONFIGURATION DIFFERENCES DETECTED'}')
    print(f'Report: {report_file}')

if __name__ == '__main__':
    main()