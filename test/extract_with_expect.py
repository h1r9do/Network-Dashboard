#\!/usr/bin/env python3
"""
Extract SNMP configs using pexpect for slow typing
"""

import pexpect
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def slow_ssh_connect(hostname, ip, username, password):
    """Connect via SSH with slow password typing"""
    try:
        # Start SSH connection
        ssh = pexpect.spawn(f'ssh {username}@{ip}', timeout=60)
        ssh.logfile_read = open(f'/tmp/ssh_{hostname}.log', 'wb')
        
        # Wait for password prompt
        i = ssh.expect(['Password:', 'password:', pexpect.TIMEOUT, pexpect.EOF], timeout=30)
        
        if i in [0, 1]:  # Password prompt found
            logger.info(f"  Password prompt received, typing slowly...")
            
            # Wait 2 seconds then type password slowly
            time.sleep(2)
            for char in password:
                ssh.send(char)
                time.sleep(0.1)  # 0.1 second between characters
            ssh.sendline('')  # Send enter
            
            # Wait for device prompt
            i = ssh.expect([r'#', r'>', pexpect.TIMEOUT, pexpect.EOF], timeout=30)
            
            if i in [0, 1]:  # Got device prompt
                logger.info(f"  ✅ Successfully connected to {hostname}")
                return ssh, None
            else:
                return None, "Did not receive device prompt after authentication"
        else:
            return None, "Did not receive password prompt"
            
    except Exception as e:
        return None, f"SSH connection failed: {str(e)}"

def extract_snmp_config(ssh, hostname, device_type):
    """Extract SNMP configuration using pexpect session"""
    config_data = {
        'hostname': hostname,
        'device_type': device_type,
        'extraction_timestamp': datetime.now().isoformat(),
        'ssh_success': True,
        'raw_snmp_config': '',
        'raw_acl_config': '',
        'device_info': {},
        'extraction_log': []
    }
    
    commands = [
        'show version  < /dev/null |  include Version',
        'show running-config | include snmp-server',
        'show ip access-lists'
    ]
    
    for cmd in commands:
        try:
            logger.info(f"    Running: {cmd}")
            
            # Send command
            ssh.sendline(cmd)
            
            # Wait for command to complete and return to prompt
            ssh.expect([r'#', r'>'], timeout=30)
            
            # Get the output
            output = ssh.before.decode('utf-8', errors='ignore')
            
            # Store output based on command type
            if 'version' in cmd.lower():
                config_data['device_info']['version'] = output
            elif 'snmp' in cmd:
                config_data['raw_snmp_config'] += f"\n=== {cmd} ===\n{output}"
            elif 'access' in cmd:
                config_data['raw_acl_config'] += f"\n=== {cmd} ===\n{output}"
            
            config_data['extraction_log'].append(f"SUCCESS: {cmd}")
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"    Command failed: {cmd} - {e}")
            config_data['extraction_log'].append(f"FAILED: {cmd} - {str(e)}")
    
    return config_data

def main():
    logger.info("=" * 80)
    logger.info("EXTRACTING SNMP CONFIGS WITH SLOW TYPING METHOD")
    logger.info("=" * 80)
    
    # Test with first 3 failed devices
    test_devices = [
        {'hostname': 'EQX-CldTrst-8500-01', 'ip': '10.44.158.41', 'type': 'Catalyst 8500'},
        {'hostname': 'FP-DAL-ASR1001-01', 'ip': '10.42.255.16', 'type': 'ASR1001'},
        {'hostname': 'DMZ-7010-01', 'ip': '192.168.255.4', 'type': 'ASA 7010'}
    ]
    
    username = 'mbambic'
    password = 'Aud\!o\!994'
    
    results = {
        'extraction_timestamp': datetime.now().isoformat(),
        'method': 'pexpect_slow_typing',
        'total_devices': len(test_devices),
        'successful_extractions': 0,
        'devices': {}
    }
    
    for i, device in enumerate(test_devices, 1):
        hostname = device['hostname']
        ip = device['ip']
        device_type = device['type']
        
        logger.info(f"\n[{i}/{len(test_devices)}] Connecting to {hostname} ({ip})...")
        
        ssh, error = slow_ssh_connect(hostname, ip, username, password)
        
        if ssh:
            try:
                config_data = extract_snmp_config(ssh, hostname, device_type)
                results['devices'][hostname] = config_data
                results['successful_extractions'] += 1
                
                logger.info(f"  ✅ Successfully extracted config from {hostname}")
                
                # Show summary
                snmp_lines = len([l for l in config_data['raw_snmp_config'].split('\n') if l.strip()])
                acl_lines = len([l for l in config_data['raw_acl_config'].split('\n') if l.strip()])
                logger.info(f"     SNMP config: {snmp_lines} lines")
                logger.info(f"     ACL config: {acl_lines} lines")
                
                ssh.close()
                
            except Exception as e:
                logger.error(f"  Configuration extraction failed: {e}")
                results['devices'][hostname] = {
                    'hostname': hostname,
                    'ssh_success': True,
                    'extraction_error': str(e)
                }
                ssh.close()
        else:
            logger.error(f"  SSH connection failed: {error}")
            results['devices'][hostname] = {
                'hostname': hostname,
                'ssh_success': False,
                'connection_error': error
            }
        
        time.sleep(3)  # Wait between devices
    
    # Save results
    output_file = '/var/www/html/meraki-data/slow_typing_snmp_extraction.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n" + "=" * 80)
    logger.info("SLOW TYPING EXTRACTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total devices: {results['total_devices']}")
    logger.info(f"Successful extractions: {results['successful_extractions']}")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
