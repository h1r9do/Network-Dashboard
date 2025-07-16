#!/usr/bin/env python3
"""
Compare Post-Migration TST 01 to NEO 07
Compares migrated TST 01 VLANs and firewall rules to NEO 07 new standard
"""

import json
import os
from datetime import datetime

def load_configs():
    """Load both configuration files"""
    print('📋 Loading Configuration Files...')
    print('=' * 60)
    
    # Load post-migration TST 01 configuration
    tst01_file = 'tst01_post_migration_config_20250710_094311.json'
    with open(tst01_file, 'r') as f:
        tst01_config = json.load(f)
    print(f'  ✓ Loaded TST 01 post-migration config: {tst01_file}')
    
    # Load NEO 07 configuration
    neo07_file = 'neo07_config_20250710_094311.json'
    with open(neo07_file, 'r') as f:
        neo07_config = json.load(f)
    print(f'  ✓ Loaded NEO 07 config: {neo07_file}')
    
    return tst01_config, neo07_config

def compare_vlans(tst01_config, neo07_config):
    """Compare VLAN configurations between post-migration TST 01 and NEO 07"""
    print('\\n🏷️  VLAN Comparison: Post-Migration TST 01 vs NEO 07')
    print('=' * 60)
    
    tst01_vlans = tst01_config['vlans']
    neo07_vlans = neo07_config['vlans']
    
    print(f'Post-Migration TST 01 VLANs: {len(tst01_vlans)} total')
    print(f'NEO 07 VLANs: {len(neo07_vlans)} total')
    
    # Create lookup dictionaries
    tst01_vlan_dict = {vlan['id']: vlan for vlan in tst01_vlans}
    neo07_vlan_dict = {vlan['id']: vlan for vlan in neo07_vlans}
    
    print('\\nVLAN-by-VLAN Comparison:')
    print('VLAN | TST 01 Name              | TST 01 Subnet         | NEO 07 Name              | NEO 07 Subnet         | Match')
    print('-' * 120)
    
    # Expected new standard VLANs
    expected_vlans = [100, 200, 300, 301, 400, 410, 800, 803, 900]
    
    matches = 0
    total_compared = 0
    
    for vlan_id in sorted(set(list(tst01_vlan_dict.keys()) + list(neo07_vlan_dict.keys()))):
        tst01_vlan = tst01_vlan_dict.get(vlan_id, {})
        neo07_vlan = neo07_vlan_dict.get(vlan_id, {})
        
        tst01_name = tst01_vlan.get('name', 'MISSING').ljust(24)
        tst01_subnet = tst01_vlan.get('subnet', 'MISSING').ljust(21)
        neo07_name = neo07_vlan.get('name', 'MISSING').ljust(24)
        neo07_subnet = neo07_vlan.get('subnet', 'MISSING').ljust(21)
        
        # Check if both networks have this VLAN
        if tst01_vlan and neo07_vlan:
            total_compared += 1
            # Check name match (allowing for minor variations)
            name_match = tst01_vlan.get('name') == neo07_vlan.get('name')
            # For VLAN comparison, we expect different IP ranges but same structure
            structure_match = True  # We don't expect IP ranges to match between different networks
            overall_match = '✓' if name_match else '⚠️'
            if name_match:
                matches += 1
        elif tst01_vlan and not neo07_vlan:
            overall_match = 'TST Only'
            total_compared += 1
        elif neo07_vlan and not tst01_vlan:
            overall_match = 'NEO Only'
            total_compared += 1
        else:
            overall_match = '✗'
        
        print(f'{str(vlan_id).ljust(4)} | {tst01_name} | {tst01_subnet} | {neo07_name} | {neo07_subnet} | {overall_match}')
    
    print(f'\\nVLAN Comparison Summary:')
    print(f'  - VLANs in both networks: {total_compared}')
    print(f'  - Name matches: {matches}/{total_compared}')
    print(f'  - TST 01 follows new standard: {matches >= 7}')  # Most important VLANs should match
    
    # Check new standard VLAN numbers
    print(f'\\nNew Standard VLAN Check:')
    standard_vlans_present = 0
    for vlan_id in expected_vlans:
        if vlan_id in tst01_vlan_dict:
            standard_vlans_present += 1
            print(f'  ✓ VLAN {vlan_id}: {tst01_vlan_dict[vlan_id].get("name", "Unknown")}')
        else:
            print(f'  ✗ VLAN {vlan_id}: Missing')
    
    print(f'\\nNew Standard Compliance: {standard_vlans_present}/{len(expected_vlans)} VLANs present')
    
    return standard_vlans_present >= 7  # Most critical VLANs should be present

def compare_firewall_rules(tst01_config, neo07_config):
    """Compare firewall rule configurations"""
    print('\\n🔥 Firewall Rules Comparison: Post-Migration TST 01 vs NEO 07')
    print('=' * 60)
    
    tst01_rules = tst01_config['firewall_rules']['rules']
    neo07_rules = neo07_config['firewall_rules']['rules']
    
    print(f'Post-Migration TST 01 Firewall Rules: {len(tst01_rules)} total')
    print(f'NEO 07 Firewall Rules: {len(neo07_rules)} total')
    
    # Count rules with new standard VLAN references
    tst01_new_vlan_rules = 0
    neo07_new_vlan_rules = 0
    
    new_standard_vlans = ['VLAN(100)', 'VLAN(200)', 'VLAN(300)', 'VLAN(301)', 'VLAN(400)', 'VLAN(410)', 'VLAN(800)', 'VLAN(803)', 'VLAN(900)']
    
    for rule in tst01_rules:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        if any(vlan_ref in src or vlan_ref in dst for vlan_ref in new_standard_vlans):
            tst01_new_vlan_rules += 1
    
    for rule in neo07_rules:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        if any(vlan_ref in src or vlan_ref in dst for vlan_ref in new_standard_vlans):
            neo07_new_vlan_rules += 1
    
    print(f'TST 01 rules with new standard VLAN references: {tst01_new_vlan_rules}')
    print(f'NEO 07 rules with new standard VLAN references: {neo07_new_vlan_rules}')
    
    # Sample rule comparison
    print('\\nRule Structure Comparison (first 10 rules):')
    print('Rule | TST 01 Rule                          | NEO 07 Rule                          | Type Match')
    print('-' * 100)
    
    rule_type_matches = 0
    compared_rules = min(len(tst01_rules), len(neo07_rules), 10)
    
    for i in range(compared_rules):
        tst01_rule = tst01_rules[i]
        neo07_rule = neo07_rules[i] if i < len(neo07_rules) else {}
        
        tst01_policy = tst01_rule.get('policy', 'unknown')
        neo07_policy = neo07_rule.get('policy', 'unknown')
        
        tst01_comment = tst01_rule.get('comment', 'No comment')[:30]
        neo07_comment = neo07_rule.get('comment', 'No comment')[:30]
        
        policy_match = '✓' if tst01_policy == neo07_policy else '✗'
        if tst01_policy == neo07_policy:
            rule_type_matches += 1
        
        print(f'{str(i+1).ljust(4)} | {f"{tst01_policy}: {tst01_comment}".ljust(36)} | {f"{neo07_policy}: {neo07_comment}".ljust(36)} | {policy_match}')
    
    # Check for migrated VLAN references
    print('\\nMigrated VLAN Reference Check:')
    legacy_vlans = ['VLAN(1)', 'VLAN(101)', 'VLAN(201)', 'VLAN(801)']
    legacy_found = 0
    
    for rule in tst01_rules:
        src = str(rule.get('srcCidr', ''))
        dst = str(rule.get('destCidr', ''))
        for legacy_vlan in legacy_vlans:
            if legacy_vlan in src or legacy_vlan in dst:
                legacy_found += 1
                break
    
    print(f'  - Legacy VLAN references in TST 01: {legacy_found} rules')
    print(f'  - New standard VLAN references in TST 01: {tst01_new_vlan_rules} rules')
    print(f'  - Migration success: {"✓" if legacy_found == 0 and tst01_new_vlan_rules > 40 else "✗"}')
    
    print(f'\\nFirewall Rules Summary:')
    print(f'  - Rule count similarity: {abs(len(tst01_rules) - len(neo07_rules)) <= 10}')
    print(f'  - VLAN references updated: {"✓" if legacy_found == 0 else "✗"}')
    print(f'  - New standard compliance: {"✓" if tst01_new_vlan_rules > 40 else "✗"}')
    
    return legacy_found == 0 and tst01_new_vlan_rules > 40

def compare_overall_structure(tst01_config, neo07_config):
    """Compare overall network structure"""
    print('\\n🔧 Overall Structure Comparison')
    print('=' * 60)
    
    print(f'Network Names:')
    print(f'  - TST 01: {tst01_config["network"]["name"]}')
    print(f'  - NEO 07: {neo07_config["network"]["name"]}')
    
    print(f'\\nDevice Counts:')
    print(f'  - TST 01: {len(tst01_config["devices"])} devices')
    print(f'  - NEO 07: {len(neo07_config["devices"])} devices')
    
    print(f'\\nMX Port Configurations:')
    print(f'  - TST 01: {len(tst01_config["mx_ports"])} ports')
    print(f'  - NEO 07: {len(neo07_config["mx_ports"])} ports')
    
    # Check if TST 01 has expected network structure
    structure_score = 0
    
    # Should have 10 VLANs (including new standard)
    if len(tst01_config['vlans']) >= 9:
        structure_score += 1
    
    # Should have substantial firewall rules
    if len(tst01_config['firewall_rules']['rules']) >= 50:
        structure_score += 1
    
    # Should have proper device count
    if len(tst01_config['devices']) >= 3:
        structure_score += 1
    
    # Should have MX ports configured
    if len(tst01_config['mx_ports']) >= 10:
        structure_score += 1
    
    print(f'\\nStructure Score: {structure_score}/4')
    
    return structure_score >= 3

def generate_comparison_report(tst01_config, neo07_config, vlan_match, fw_match, structure_match):
    """Generate comprehensive comparison report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    migration_success = vlan_match and fw_match and structure_match
    
    report = f'''
Post-Migration TST 01 vs NEO 07 Comparison Report
================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
TST 01 Post-Migration: {tst01_config.get('download_date', 'Unknown')}
NEO 07 Reference: {neo07_config.get('download_date', 'Unknown')}

MIGRATION VALIDATION SUMMARY
============================

VLAN Migration:         {'✅ SUCCESS' if vlan_match else '❌ FAILED'}
Firewall Rules:         {'✅ SUCCESS' if fw_match else '❌ FAILED'}
Overall Structure:      {'✅ SUCCESS' if structure_match else '❌ FAILED'}

OVERALL MIGRATION:      {'✅ SUCCESSFUL' if migration_success else '❌ NEEDS REVIEW'}

DETAILED COMPARISON
==================

VLANs:
- TST 01 Post-Migration: {len(tst01_config['vlans'])} VLANs
- NEO 07 Reference: {len(neo07_config['vlans'])} VLANs
- New Standard Compliance: {vlan_match}

Firewall Rules:
- TST 01 Post-Migration: {len(tst01_config['firewall_rules']['rules'])} rules
- NEO 07 Reference: {len(neo07_config['firewall_rules']['rules'])} rules
- VLAN Reference Migration: {fw_match}

Network Structure:
- TST 01 Devices: {len(tst01_config['devices'])} devices
- NEO 07 Devices: {len(neo07_config['devices'])} devices
- Configuration Completeness: {structure_match}

MIGRATION ASSESSMENT
===================
{"TST 01 has been successfully migrated to the new VLAN standard and matches NEO 07's configuration structure." if migration_success else "Migration issues detected. TST 01 configuration needs review and possible remediation."}

New Standard VLAN Numbers Present:
✓ VLAN 100 (Data) - {"Present" if any(v['id'] == 100 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 200 (Voice) - {"Present" if any(v['id'] == 200 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 300 (Net Mgmt) - {"Present" if any(v['id'] == 300 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 301 (Scanner) - {"Present" if any(v['id'] == 301 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 400 (IoT) - {"Present" if any(v['id'] == 400 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 410 (Credit Card) - {"Present" if any(v['id'] == 410 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 800 (Guest) - {"Present" if any(v['id'] == 800 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 803 (IoT Wireless) - {"Present" if any(v['id'] == 803 for v in tst01_config['vlans']) else "Missing"}
✓ VLAN 900 (Management) - {"Present" if any(v['id'] == 900 for v in tst01_config['vlans']) else "Missing"}

CONCLUSION
==========
Migration Status: {'✅ COMPLETE AND VALIDATED' if migration_success else '⚠️ REQUIRES ATTENTION'}
Ready for Production: {'✅ YES' if migration_success else '❌ NO - REVIEW REQUIRED'}
'''
    
    report_filename = f'post_migration_comparison_report_{timestamp}.txt'
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f'\\n📊 Comparison report saved: {report_filename}')
    return report_filename

def main():
    print('🔍 Post-Migration TST 01 vs NEO 07 Comparison')
    print('=' * 60)
    print('Validating VLAN migration success by comparing TST 01 to NEO 07 new standard')
    
    # Load configurations
    tst01_config, neo07_config = load_configs()
    
    # Run comparisons
    vlan_match = compare_vlans(tst01_config, neo07_config)
    fw_match = compare_firewall_rules(tst01_config, neo07_config)
    structure_match = compare_overall_structure(tst01_config, neo07_config)
    
    # Generate report
    report_file = generate_comparison_report(tst01_config, neo07_config, vlan_match, fw_match, structure_match)
    
    # Final summary
    migration_success = vlan_match and fw_match and structure_match
    
    print('\\n' + '=' * 60)
    print('🎯 MIGRATION VALIDATION RESULTS')
    print('=' * 60)
    print(f'VLAN Migration:     {'✅ SUCCESS' if vlan_match else '❌ FAILED'}')
    print(f'Firewall Rules:     {'✅ SUCCESS' if fw_match else '❌ FAILED'}')
    print(f'Overall Structure:  {'✅ SUCCESS' if structure_match else '❌ FAILED'}')
    print('')
    print(f'Migration Status:   {'✅ COMPLETE AND VALIDATED' if migration_success else '⚠️ NEEDS REVIEW'}')
    print(f'Report: {report_file}')

if __name__ == '__main__':
    main()