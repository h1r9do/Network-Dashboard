#\!/usr/bin/env python3
"""
SNMP ACL Configuration Examiner - Find which IP ranges are allowed SNMP access
"""

import paramiko
import json
import re
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SSH_USERNAME = 'mbambic'
SSH_PASSWORD = 'Aud\!o\!994'

def ssh_connect(hostname, ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD, timeout=10)
        return ssh, None
    except Exception as e:
        return None, str(e)

def get_snmp_acl_config(ssh_client, hostname):
    config_data = {
        'hostname': hostname,
        'snmp_communities': [],
        'acl_rules': {},
        'raw_snmp_config': '',
        'raw_acl_config': ''
    }
    
    commands = [
        'show running-config  < /dev/null |  section snmp-server',
        'show running-config | include "snmp-server"',
        'show ip access-lists',
        'show access-lists'
    ]
    
    for cmd in commands:
        try:
            logger.info(f"  Running: {cmd}")
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=15)
            output = stdout.read().decode('utf-8', errors='ignore')
            
            if 'snmp-server' in cmd:
                config_data['raw_snmp_config'] += output + "\n"
            elif 'access-list' in cmd:
                config_data['raw_acl_config'] += output + "\n"
                
            time.sleep(1)
        except Exception as e:
            logger.warning(f"  Command failed: {cmd} - {e}")
    
    # Parse SNMP communities and ACLs
    snmp_patterns = [
        r'snmp-server community (\S+) (?:RO|RW)\s+(\S+)',
        r'snmp-server community (\S+) (?:RO|RW)',
        r'snmp-server community (\S+)\s+(\S+)'
    ]
    
    for pattern in snmp_patterns:
        matches = re.findall(pattern, config_data['raw_snmp_config'], re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple) and len(match) == 2:
                community, acl = match
                if acl and not acl.upper() in ['RO', 'RW', 'READ', 'WRITE']:
                    config_data['snmp_communities'].append({'community': community, 'acl': acl})
                    
                    # Parse the ACL rules
                    acl_rules = parse_acl_rules(config_data['raw_acl_config'], acl)
                    if acl_rules:
                        config_data['acl_rules'][acl] = acl_rules
                else:
                    config_data['snmp_communities'].append({'community': community, 'acl': None})
            else:
                config_data['snmp_communities'].append({'community': match, 'acl': None})
    
    return config_data

def parse_acl_rules(acl_output, acl_name):
    rules = []
    
    # Look for standard ACL patterns
    patterns = [
        rf'Standard IP access list {acl_name}(.*?)(?=\n\w|\nStandard|\nExtended|\Z)',
        rf'access-list {acl_name} (permit|deny) (\S+)(?: (\S+))?'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, acl_output, re.DOTALL | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 2:
                if match[0] in ['permit', 'deny']:
                    rules.append({
                        'action': match[0],
                        'network': match[1],
                        'wildcard': match[2] if len(match) > 2 and match[2] else '0.0.0.0'
                    })
    
    # Also look for inline rules in the ACL section
    acl_section = re.search(rf'Standard IP access list {acl_name}(.*?)(?=\n\w|\Z)', acl_output, re.DOTALL)
    if acl_section:
        section_content = acl_section.group(1)
        rule_matches = re.findall(r'(permit|deny)\s+(\S+)(?:\s+(\S+))?', section_content)
        for match in rule_matches:
            rules.append({
                'action': match[0],
                'network': match[1],
                'wildcard': match[2] if match[2] else '0.0.0.0'
            })
    
    return rules

def analyze_ip_access(acl_rules, target_ip):
    import ipaddress
    
    try:
        target_ip_obj = ipaddress.IPv4Address(target_ip)
    except:
        return False, "Invalid IP address"
    
    for rule in acl_rules:
        try:
            network = rule['network']
            wildcard = rule['wildcard']
            
            # Handle special cases
            if network == 'any':
                return rule['action'] == 'permit', f"Matched 'any' rule: {rule['action']}"
            
            if network == 'host':
                continue  # Skip malformed rules
            
            # Convert wildcard to CIDR
            if wildcard == '0.0.0.0':
                cidr_net = f"{network}/32"
            else:
                # Convert wildcard mask to prefix length
                wildcard_parts = [int(x) for x in wildcard.split('.')]
                # Wildcard is inverted subnet mask
                subnet_parts = [255 - x for x in wildcard_parts]
                
                # Calculate prefix length
                prefix_len = 0
                for part in subnet_parts:
                    if part == 255:
                        prefix_len += 8
                    elif part == 254:
                        prefix_len += 7
                    elif part == 252:
                        prefix_len += 6
                    elif part == 248:
                        prefix_len += 5
                    elif part == 240:
                        prefix_len += 4
                    elif part == 224:
                        prefix_len += 3
                    elif part == 192:
                        prefix_len += 2
                    elif part == 128:
                        prefix_len += 1
                    break
                
                cidr_net = f"{network}/{prefix_len}"
            
            network_obj = ipaddress.IPv4Network(cidr_net, strict=False)
            
            if target_ip_obj in network_obj:
                return rule['action'] == 'permit', f"Matched {cidr_net}: {rule['action']}"
                
        except Exception as e:
            logger.debug(f"Error analyzing rule {rule}: {e}")
            continue
    
    return False, "No matching rules (implicit deny)"

def main():
    logger.info("=" * 60)
    logger.info("SNMP ACL Configuration Examiner")
    logger.info("Analyzing SNMP access for IP: 10.0.145.130")
    logger.info("=" * 60)
    
    # Get first few devices to test
    test_devices = [
        {'hostname': '2960-CX-Series-NOC', 'ip': '10.0.255.10'},
        {'hostname': 'AL-5000-01', 'ip': '10.101.145.125'},
        {'hostname': 'AL-7000-01-ADMIN', 'ip': '10.101.145.123'}
    ]
    
    results = []
    target_ip = "10.0.145.130"
    
    for i, device in enumerate(test_devices, 1):
        hostname = device['hostname']
        ip = device['ip']
        
        logger.info(f"\n[{i}/{len(test_devices)}] Examining {hostname} ({ip})")
        
        ssh_client, error = ssh_connect(hostname, ip)
        if not ssh_client:
            logger.error(f"  SSH connection failed: {error}")
            continue
        
        try:
            config_data = get_snmp_acl_config(ssh_client, hostname)
            
            logger.info(f"  Found {len(config_data['snmp_communities'])} SNMP communities")
            
            # Analyze each community
            for community_info in config_data['snmp_communities']:
                community = community_info['community'] 
                acl_name = community_info['acl']
                
                if acl_name and acl_name in config_data['acl_rules']:
                    allowed, reason = analyze_ip_access(config_data['acl_rules'][acl_name], target_ip)
                    status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
                    logger.info(f"    Community '{community}' (ACL: {acl_name}): {status}")
                    logger.info(f"      Reason: {reason}")
                    
                    # Show ACL rules
                    logger.info(f"      ACL Rules:")
                    for rule in config_data['acl_rules'][acl_name]:
                        logger.info(f"        {rule['action']} {rule['network']} {rule['wildcard']}")
                else:
                    logger.info(f"    Community '{community}': No ACL (likely allows any)")
                    
            results.append(config_data)
            
        except Exception as e:
            logger.error(f"  Analysis failed: {e}")
        finally:
            ssh_client.close()
        
        time.sleep(2)
    
    # Save results
    output_file = '/var/www/html/meraki-data/snmp_acl_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_timestamp': datetime.now().isoformat(),
            'target_ip': target_ip,
            'results': results
        }, f, indent=2)
    
    logger.info(f"\nAnalysis complete. Results saved to: {output_file}")

if __name__ == "__main__":
    main()
