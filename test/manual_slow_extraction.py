#\!/usr/bin/env python3
"""
Manual SNMP extraction with subprocess and manual typing simulation
"""

import subprocess
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_device_via_subprocess(hostname, ip):
    """Extract SNMP config using subprocess with manual command execution"""
    
    config_data = {
        'hostname': hostname,
        'ip': ip,
        'extraction_timestamp': datetime.now().isoformat(),
        'extraction_method': 'manual_subprocess',
        'commands_executed': [],
        'raw_outputs': {}
    }
    
    commands = [
        'show version  < /dev/null |  include Version',
        'show running-config | include snmp-server', 
        'show ip access-lists'
    ]
    
    logger.info(f"Extracting from {hostname} ({ip}) using manual method...")
    
    for cmd in commands:
        try:
            logger.info(f"  Executing: {cmd}")
            
            # Create the full SSH command with slow password typing simulation
            ssh_cmd = f'''
            sshpass -p 'Aud\!o\!994' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 mbambic@{ip} "{cmd}"
            '''
            
            # Execute command
            result = subprocess.run(
                ssh_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                config_data['raw_outputs'][cmd] = output
                config_data['commands_executed'].append(f"SUCCESS: {cmd}")
                
                logger.info(f"    ✅ Command successful: {len(output)} characters")
                
                # Show preview of output
                if output:
                    preview = output[:100].replace('\n', ' ')
                    logger.info(f"    Preview: {preview}...")
                
            else:
                error = result.stderr.strip()
                config_data['raw_outputs'][cmd] = f"ERROR: {error}"
                config_data['commands_executed'].append(f"FAILED: {cmd} - {error}")
                logger.warning(f"    ❌ Command failed: {error}")
            
            time.sleep(2)  # Wait between commands
            
        except subprocess.TimeoutExpired:
            logger.error(f"    ⏰ Command timeout: {cmd}")
            config_data['commands_executed'].append(f"TIMEOUT: {cmd}")
        except Exception as e:
            logger.error(f"    💥 Command error: {cmd} - {str(e)}")
            config_data['commands_executed'].append(f"ERROR: {cmd} - {str(e)}")
    
    return config_data

def parse_snmp_communities(raw_snmp_output):
    """Parse SNMP communities from raw output"""
    import re
    
    communities = []
    if raw_snmp_output and 'ERROR:' not in raw_snmp_output:
        # Look for snmp-server community lines
        patterns = [
            r'snmp-server community (\S+) (?:RO|RW)\s+(\S+)',
            r'snmp-server community (\S+) (\S+)',
            r'snmp-server community (\S+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, raw_snmp_output, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    community, acl = match[0], match[1]
                    if acl.upper() not in ['RO', 'RW']:
                        communities.append({'community': community, 'acl': acl})
                    else:
                        communities.append({'community': community, 'acl': None})
                elif isinstance(match, str):
                    communities.append({'community': match, 'acl': None})
    
    return communities

def main():
    logger.info("=" * 80)
    logger.info("MANUAL SNMP CONFIG EXTRACTION")
    logger.info("=" * 80)
    
    # Test with 3 failed devices
    test_devices = [
        {'hostname': 'EQX-CldTrst-8500-01', 'ip': '10.44.158.41'},
        {'hostname': 'FP-DAL-ASR1001-01', 'ip': '10.42.255.16'},
        {'hostname': 'DMZ-7010-01', 'ip': '192.168.255.4'}
    ]
    
    results = {
        'extraction_timestamp': datetime.now().isoformat(),
        'method': 'manual_subprocess_sshpass',
        'total_devices': len(test_devices),
        'successful_extractions': 0,
        'devices': {}
    }
    
    for i, device in enumerate(test_devices, 1):
        hostname = device['hostname']
        ip = device['ip']
        
        logger.info(f"\n[{i}/{len(test_devices)}] Processing {hostname}...")
        
        try:
            config_data = extract_device_via_subprocess(hostname, ip)
            
            # Parse SNMP communities
            snmp_output = config_data['raw_outputs'].get('show running-config | include snmp-server', '')
            config_data['snmp_communities'] = parse_snmp_communities(snmp_output)
            
            results['devices'][hostname] = config_data
            
            # Check if extraction was successful
            successful_commands = len([c for c in config_data['commands_executed'] if 'SUCCESS:' in c])
            if successful_commands > 0:
                results['successful_extractions'] += 1
                logger.info(f"  ✅ {hostname}: {successful_commands}/3 commands successful")
                
                # Show SNMP communities found
                communities = config_data['snmp_communities']
                if communities:
                    logger.info(f"     Found {len(communities)} SNMP communities:")
                    for comm in communities:
                        acl_info = f" (ACL: {comm['acl']})" if comm['acl'] else ""
                        logger.info(f"       - {comm['community']}{acl_info}")
                else:
                    logger.info(f"     No SNMP communities found")
            else:
                logger.warning(f"  ❌ {hostname}: All commands failed")
        
        except Exception as e:
            logger.error(f"  💥 {hostname}: Extraction failed - {str(e)}")
            results['devices'][hostname] = {
                'hostname': hostname,
                'ip': ip,
                'extraction_error': str(e)
            }
        
        time.sleep(3)
    
    # Save results
    output_file = '/var/www/html/meraki-data/manual_snmp_extraction.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n" + "=" * 80)
    logger.info("MANUAL EXTRACTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total devices: {results['total_devices']}")
    logger.info(f"Successful extractions: {results['successful_extractions']}")
    logger.info(f"Results saved to: {output_file}")
    
    # Summary of communities found
    all_communities = set()
    for hostname, data in results['devices'].items():
        if 'snmp_communities' in data:
            for comm in data['snmp_communities']:
                all_communities.add(comm['community'])
    
    if all_communities:
        logger.info(f"\nUnique SNMP communities discovered: {', '.join(sorted(all_communities))}")

if __name__ == "__main__":
    main()
