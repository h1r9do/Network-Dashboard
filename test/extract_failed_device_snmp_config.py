#\!/usr/bin/env python3
"""
Extract SNMP Communities and ACLs from Failed SNMP Devices
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
SSH_PASSWORD = 'Aud!o!994'

# Failed devices from comprehensive test
FAILED_DEVICES = [
    {'hostname': 'EQX-CldTrst-8500-01', 'ip': '10.44.158.41', 'type': 'Catalyst 8500'},
    {'hostname': 'EQX-CldTrst-8500-02', 'ip': '10.44.158.42', 'type': 'Catalyst 8500'},
    {'hostname': 'FP-DAL-ASR1001-01', 'ip': '10.42.255.16', 'type': 'ASR1001'},
    {'hostname': 'FP-DAL-ASR1001-02', 'ip': '10.42.255.26', 'type': 'ASR1001'},
    {'hostname': 'FP-ATL-ASR1001', 'ip': '10.43.255.16', 'type': 'ASR1001'},
    {'hostname': 'EQX-EdgeDIA-8300-01', 'ip': '10.44.158.51', 'type': 'Catalyst 8300'},
    {'hostname': 'EQX-EdgeDIA-8300-02', 'ip': '10.44.158.52', 'type': 'Catalyst 8300'},
    {'hostname': 'EQX-MPLS-8300-01', 'ip': '10.44.158.61', 'type': 'Catalyst 8300'},
    {'hostname': 'EQX-MPLS-8300-02', 'ip': '10.44.158.62', 'type': 'Catalyst 8300'},
    {'hostname': 'DMZ-7010-01', 'ip': '192.168.255.4', 'type': 'ASA 7010'},
    {'hostname': 'DMZ-7010-02', 'ip': '192.168.255.5', 'type': 'ASA 7010'},
    {'hostname': 'AL-DMZ-7010-01', 'ip': '192.168.200.10', 'type': 'ASA 7010'},
    {'hostname': 'AL-DMZ-7010-02', 'ip': '192.168.200.11', 'type': 'ASA 7010'},
    {'hostname': 'FW-9400-01', 'ip': '192.168.255.12', 'type': 'Firepower 9400'},
    {'hostname': 'FW-9400-02', 'ip': '192.168.255.13', 'type': 'Firepower 9400'},
    {'hostname': 'HQ-ATT-DIA', 'ip': '192.168.255.15', 'type': 'Internet Circuit'},
    {'hostname': 'HQ-LUMEN-DIA', 'ip': '192.168.255.14', 'type': 'Internet Circuit'}
]

def ssh_connect(hostname, ip):
    """Connect to device via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD, timeout=15)
        return ssh, None
    except Exception as e:
        return None, str(e)

def get_device_snmp_config(ssh_client, hostname, device_type):
    """Extract SNMP configuration and ACLs from device"""
    config_data = {
        'hostname': hostname,
        'device_type': device_type,
        'extraction_timestamp': datetime.now().isoformat(),
        'ssh_success': True,
        'snmp_communities': [],
        'acl_rules': {},
        'raw_snmp_config': '',
        'raw_acl_config': '',
        'device_info': {},
        'errors': []
    }
    
    # Commands vary by device type
    if 'ASA' in device_type or 'Firepower' in device_type:
        commands = [
            'show version  < /dev/null |  include Version',
            'show running-config | grep snmp-server',
            'show running-config | grep access-list',
            'show access-list',
            'show snmp-server'
        ]
    else:  # IOS/IOS-XE devices
        commands = [
            'show version | include Version',
            'show running-config | section snmp-server',
            'show running-config | include snmp-server',
            'show ip access-lists',
            'show access-lists',
            'show snmp community'
        ]
    
    for cmd in commands:
        try:
            logger.info(f"  Running: {cmd}")
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=20)
            output = stdout.read().decode('utf-8', errors='ignore')
            error_output = stderr.read().decode('utf-8', errors='ignore')
            
            if 'version' in cmd.lower():
                config_data['device_info']['version'] = output.strip()
            elif 'snmp' in cmd:
                config_data['raw_snmp_config'] += f"\n=== {cmd} ===\n{output}"
            elif 'access' in cmd:
                config_data['raw_acl_config'] += f"\n=== {cmd} ===\n{output}"
            
            if error_output:
                config_data['errors'].append(f"Command '{cmd}' stderr: {error_output}")
                
            time.sleep(1)
        except Exception as e:
            logger.warning(f"  Command failed: {cmd} - {e}")
            config_data['errors'].append(f"Command '{cmd}' failed: {str(e)}")
    
    # Parse SNMP communities from raw config
    config_data['snmp_communities'] = parse_snmp_communities(config_data['raw_snmp_config'], device_type)
    
    # Parse ACLs
    config_data['acl_rules'] = parse_acl_rules(config_data['raw_acl_config'], device_type)
    
    return config_data

def parse_snmp_communities(snmp_output, device_type):
    """Parse SNMP communities from configuration output"""
    communities = []
    
    if 'ASA' in device_type or 'Firepower' in device_type:
        # ASA SNMP format: snmp-server community <community> <permission>
        patterns = [
            r'snmp-server community (\S+) (\S+)',
            r'snmp-server community (\S+)'
        ]
    else:
        # IOS SNMP format: snmp-server community <community> [RO|RW] [acl]
        patterns = [
            r'snmp-server community (\S+) (?:RO|RW)\s+(\S+)',
            r'snmp-server community (\S+) (\S+)',
            r'snmp-server community (\S+)'
        ]
    
    for pattern in patterns:
        matches = re.findall(pattern, snmp_output, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                if len(match) == 2:
                    community, acl_or_perm = match
                    # Check if second part is an ACL name or permission
                    if acl_or_perm.upper() not in ['RO', 'RW', 'READ', 'WRITE']:
                        communities.append({'community': community, 'acl': acl_or_perm, 'permission': 'unknown'})
                    else:
                        communities.append({'community': community, 'acl': None, 'permission': acl_or_perm})
                else:
                    communities.append({'community': match, 'acl': None, 'permission': 'unknown'})
            else:
                communities.append({'community': match, 'acl': None, 'permission': 'unknown'})
    
    # Remove duplicates
    unique_communities = []
    seen = set()
    for comm in communities:
        key = comm['community']
        if key not in seen:
            seen.add(key)
            unique_communities.append(comm)
    
    return unique_communities

def parse_acl_rules(acl_output, device_type):
    """Parse ACL rules from configuration output"""
    acl_rules = {}
    
    if 'ASA' in device_type or 'Firepower' in device_type:
        # ASA ACL format
        acl_matches = re.findall(r'access-list (\S+) extended (permit|deny) (\S+) (\S+) (\S+)', acl_output)
        for match in acl_matches:
            acl_name, action, protocol, source, dest = match
            if acl_name not in acl_rules:
                acl_rules[acl_name] = []
            acl_rules[acl_name].append({
                'action': action,
                'protocol': protocol,
                'source': source,
                'destination': dest
            })
    else:
        # IOS Standard/Extended ACLs
        # Standard ACL format
        std_matches = re.findall(r'Standard IP access list (\S+)', acl_output)
        for acl_name in std_matches:
            if acl_name not in acl_rules:
                acl_rules[acl_name] = []
            
            # Find rules for this ACL
            acl_section = re.search(rf'Standard IP access list {acl_name}(.*?)(?=\n\w|\\Z)', acl_output, re.DOTALL)
            if acl_section:
                section_content = acl_section.group(1)
                rule_matches = re.findall(r'(permit|deny)\s+(\S+)(?:\s+(\S+))?', section_content)
                for rule_match in rule_matches:
                    action, network, wildcard = rule_match
                    acl_rules[acl_name].append({
                        'action': action,
                        'network': network,
                        'wildcard': wildcard if wildcard else '0.0.0.0'
                    })
        
        # Extended ACL format
        ext_matches = re.findall(r'Extended IP access list (\S+)', acl_output)
        for acl_name in ext_matches:
            if acl_name not in acl_rules:
                acl_rules[acl_name] = []
    
    return acl_rules

def analyze_snmp_access(device_config, target_ip='10.0.145.130'):
    """Analyze if target IP has SNMP access based on ACLs"""
    analysis = {
        'target_ip': target_ip,
        'communities_with_access': [],
        'blocked_communities': [],
        'analysis_notes': []
    }
    
    for community_info in device_config['snmp_communities']:
        community = community_info['community']
        acl_name = community_info.get('acl')
        
        if not acl_name or acl_name not in device_config['acl_rules']:
            # No ACL means usually open access
            analysis['communities_with_access'].append({
                'community': community,
                'reason': 'No ACL restriction'
            })
        else:
            # Check ACL rules for target IP
            access_granted = check_ip_in_acl(target_ip, device_config['acl_rules'][acl_name])
            if access_granted:
                analysis['communities_with_access'].append({
                    'community': community,
                    'acl': acl_name,
                    'reason': 'IP matches ACL permit rule'
                })
            else:
                analysis['blocked_communities'].append({
                    'community': community,
                    'acl': acl_name,
                    'reason': 'IP blocked by ACL'
                })
    
    return analysis

def check_ip_in_acl(target_ip, acl_rules):
    """Check if target IP is permitted by ACL rules"""
    import ipaddress
    
    try:
        target_ip_obj = ipaddress.IPv4Address(target_ip)
    except:
        return False
    
    for rule in acl_rules:
        if rule['action'].lower() == 'permit':
            network = rule.get('network', '')
            wildcard = rule.get('wildcard', '0.0.0.0')
            
            if network == 'any':
                return True
            
            try:
                # Convert wildcard to CIDR
                if wildcard == '0.0.0.0':
                    cidr_net = f"{network}/32"
                else:
                    # Convert wildcard mask to prefix length
                    wildcard_parts = [int(x) for x in wildcard.split('.')]
                    subnet_parts = [255 - x for x in wildcard_parts]
                    
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
                        else:
                            break
                    
                    cidr_net = f"{network}/{prefix_len}"
                
                network_obj = ipaddress.IPv4Network(cidr_net, strict=False)
                if target_ip_obj in network_obj:
                    return True
            except:
                continue
    
    return False

def main():
    logger.info("=" * 80)
    logger.info("EXTRACTING SNMP CONFIGURATIONS FROM FAILED DEVICES")
    logger.info(f"Target IP for access analysis: 10.0.145.130")
    logger.info("=" * 80)
    
    results = {
        'extraction_timestamp': datetime.now().isoformat(),
        'target_analysis_ip': '10.0.145.130',
        'total_devices': len(FAILED_DEVICES),
        'successful_extractions': 0,
        'failed_connections': 0,
        'devices': {}
    }
    
    for i, device in enumerate(FAILED_DEVICES, 1):
        hostname = device['hostname']
        ip = device['ip']
        device_type = device['type']
        
        logger.info(f"\n[{i}/{len(FAILED_DEVICES)}] Connecting to {hostname} ({ip})...")
        
        ssh_client, error = ssh_connect(hostname, ip)
        if not ssh_client:
            logger.error(f"  SSH connection failed: {error}")
            results['devices'][hostname] = {
                'hostname': hostname,
                'ip': ip,
                'device_type': device_type,
                'ssh_success': False,
                'connection_error': error,
                'extraction_timestamp': datetime.now().isoformat()
            }
            results['failed_connections'] += 1
            continue
        
        try:
            logger.info(f"  Connected successfully, extracting configuration...")
            device_config = get_device_snmp_config(ssh_client, hostname, device_type)
            
            # Analyze SNMP access for our IP
            access_analysis = analyze_snmp_access(device_config)
            device_config['snmp_access_analysis'] = access_analysis
            
            results['devices'][hostname] = device_config
            results['successful_extractions'] += 1
            
            # Log summary
            community_count = len(device_config['snmp_communities'])
            acl_count = len(device_config['acl_rules'])
            accessible_communities = len(access_analysis['communities_with_access'])
            
            logger.info(f"  ✅ Extracted: {community_count} communities, {acl_count} ACLs")
            logger.info(f"     Accessible communities: {accessible_communities}")
            
            if access_analysis['communities_with_access']:
                for comm in access_analysis['communities_with_access']:
                    logger.info(f"     📱 {comm['community']} - {comm['reason']}")
            
        except Exception as e:
            logger.error(f"  Configuration extraction failed: {e}")
            results['devices'][hostname] = {
                'hostname': hostname,
                'ip': ip,
                'device_type': device_type,
                'ssh_success': True,
                'extraction_error': str(e),
                'extraction_timestamp': datetime.now().isoformat()
            }
        finally:
            ssh_client.close()
        
        time.sleep(2)
    
    # Save results
    output_file = '/var/www/html/meraki-data/failed_devices_snmp_config.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total devices: {results['total_devices']}")
    logger.info(f"Successful extractions: {results['successful_extractions']}")
    logger.info(f"Failed connections: {results['failed_connections']}")
    
    # Summary by device type
    device_types = {}
    accessible_devices = 0
    
    for hostname, device_data in results['devices'].items():
        if device_data.get('ssh_success') and 'snmp_access_analysis' in device_data:
            device_type = device_data['device_type']
            if device_type not in device_types:
                device_types[device_type] = {'total': 0, 'with_access': 0}
            device_types[device_type]['total'] += 1
            
            if device_data['snmp_access_analysis']['communities_with_access']:
                device_types[device_type]['with_access'] += 1
                accessible_devices += 1
    
    logger.info(f"\nDevices with SNMP access for 10.0.145.130: {accessible_devices}")
    
    if device_types:
        logger.info("\nAccess summary by device type:")
        for dev_type, stats in device_types.items():
            logger.info(f"  {dev_type}: {stats['with_access']}/{stats['total']}")
    
    logger.info(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
