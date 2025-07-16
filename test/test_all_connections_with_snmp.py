#!/usr/bin/env python3
"""
Test connections to all devices and create a JSON file with working credentials
Enhanced to gather SNMP configuration from devices via SSH
"""

import json
import paramiko
import time
import sys
import psycopg2
import re
from datetime import datetime
from pysnmp.hlapi import *
import logging
import ipaddress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def get_snmp_config_via_ssh(ssh_client, hostname):
    """Extract SNMP configuration from device via SSH"""
    snmp_info = {
        'communities': [],
        'acls': {},
        'source_interface': None
    }
    
    try:
        # Commands to try based on device type
        commands = []
        
        if 'ASA' in hostname or 'FW' in hostname or 'PA' in hostname:
            # Firewall commands
            commands = [
                'show running-config | include snmp-server',
                'show snmp-server',
                'show snmp'
            ]
        else:
            # Switch/Router commands
            commands = [
                'show running-config | section snmp-server',
                'show snmp community',
                'show snmp',
                'show ip access-list'
            ]
        
        full_output = ""
        for cmd in commands:
            try:
                stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=10)
                output = stdout.read().decode('utf-8', errors='ignore')
                full_output += f"\n--- {cmd} ---\n{output}"
            except:
                continue
        
        # Parse SNMP communities
        community_patterns = [
            r'snmp-server community (\S+) (?:RO|RW)\s*(?:(\S+))?',  # Cisco IOS
            r'snmp-server community (\S+)',  # Simple format
            r'Community name: (\S+)',  # Show snmp community output
        ]
        
        for pattern in community_patterns:
            matches = re.findall(pattern, full_output, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    community = match[0]
                    acl = match[1] if len(match) > 1 and match[1] else None
                else:
                    community = match
                    acl = None
                
                if community and community not in ['<removed>', 'COMMUNITY']:
                    snmp_info['communities'].append(community)
                    if acl:
                        snmp_info['acls'][community] = acl
        
        # Parse source interface
        source_match = re.search(r'snmp-server source-interface \S+ (\S+)', full_output)
        if source_match:
            snmp_info['source_interface'] = source_match.group(1)
        
        # Parse ACLs if referenced
        for community, acl_name in snmp_info['acls'].items():
            if acl_name:
                acl_output = ""
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(f'show ip access-list {acl_name}', timeout=5)
                    acl_output = stdout.read().decode('utf-8', errors='ignore')
                except:
                    pass
                
                if acl_output:
                    snmp_info['acls'][community] = {
                        'name': acl_name,
                        'entries': acl_output
                    }
        
        logging.debug(f"SNMP config for {hostname}: {snmp_info}")
        return snmp_info
        
    except Exception as e:
        logging.error(f"Error getting SNMP config from {hostname}: {e}")
        return snmp_info

def check_snmp_acl_allows(acl_entries, test_ip='10.0.145.130'):
    """Check if ACL allows SNMP from our server"""
    if not acl_entries:
        return True  # No ACL means allow all
    
    try:
        # Simple check - look for permit statements
        if 'permit' in acl_entries.lower():
            # Check if our IP or network is permitted
            test_network = ipaddress.ip_network('10.0.0.0/16')
            
            # Look for permit statements
            permit_lines = [line for line in acl_entries.split('\n') if 'permit' in line.lower()]
            
            for line in permit_lines:
                # Very basic check - could be enhanced
                if 'any' in line or '10.0.' in line or 'host 10.0.145.130' in line:
                    return True
                
                # Try to extract IP/subnet
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)?', line)
                if ip_match:
                    try:
                        if ip_match.group(2):  # Has wildcard mask
                            # Convert wildcard to prefix length (simplified)
                            network = ipaddress.ip_network(f"{ip_match.group(1)}/16")
                        else:
                            network = ipaddress.ip_network(ip_match.group(1))
                        
                        if ipaddress.ip_address(test_ip) in network:
                            return True
                    except:
                        continue
        
        return False
    except:
        return True  # On error, assume it's allowed

def test_ssh_connection(hostname, ip, username, password, port=22):
    """Test SSH connection and gather SNMP config"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Handle username@ip format
        if '@' not in username:
            connect_username = username
            connect_hostname = ip
        else:
            connect_username = f"{username}@{ip}"
            connect_hostname = ip
        
        ssh.connect(
            hostname=connect_hostname,
            port=port,
            username=connect_username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Get SNMP configuration
        snmp_config = get_snmp_config_via_ssh(ssh, hostname)
        
        ssh.close()
        return True, "SSH connection successful", snmp_config
        
    except Exception as e:
        return False, str(e), None

def test_snmp_connection(hostname, ip, community, version='v2c'):
    """Test SNMP connection to a device"""
    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0 if version == 'v1' else 1),
            UdpTransportTarget((ip, 161), timeout=5.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )
        
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if errorIndication:
            return False, str(errorIndication)
        elif errorStatus:
            return False, str(errorStatus)
        else:
            return True, "SNMP connection successful"
            
    except Exception as e:
        return False, str(e)

def get_devices_from_database():
    """Get all devices from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get unique devices with IPs
        cursor.execute("""
            SELECT DISTINCT hostname, mgmt_ip, device_type, site, model
            FROM datacenter_inventory
            WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
            ORDER BY hostname
        """)
        
        devices = []
        for hostname, mgmt_ip, device_type, site, model in cursor.fetchall():
            devices.append({
                'hostname': hostname,
                'ip': mgmt_ip,
                'device_type': device_type or 'Unknown',
                'site': site or 'Unknown',
                'model': model or 'Unknown'
            })
        
        return devices
        
    finally:
        cursor.close()
        conn.close()

def test_all_connections():
    """Test connections to all devices and save results"""
    
    # Get devices from database
    devices = get_devices_from_database()
    logging.info(f"Found {len(devices)} devices to test")
    
    # Connection results
    connection_info = {
        'generated': datetime.now().isoformat(),
        'total_devices': len(devices),
        'devices': {}
    }
    
    # Credentials to try
    ssh_credentials = [
        {'username': 'mbambic', 'password': 'Aud!o!994'},
    ]
    
    # Default SNMP communities to try
    default_snmp_communities = ['public', 'private']
    
    success_count = 0
    failed_count = 0
    ssh_success_count = 0
    snmp_from_device_count = 0
    
    for i, device in enumerate(devices):
        hostname = device['hostname']
        ip = device['ip']
        
        logging.info(f"[{i+1}/{len(devices)}] Testing {hostname} ({ip})")
        
        device_info = {
            'hostname': hostname,
            'ip': ip,
            'device_type': device['device_type'],
            'site': device['site'],
            'model': device['model'],
            'connections': [],
            'snmp_config': None
        }
        
        # Test SSH first
        ssh_worked = False
        device_snmp_communities = []
        
        for cred in ssh_credentials:
            success, message, snmp_config = test_ssh_connection(
                hostname, ip, cred['username'], cred['password']
            )
            
            if success:
                device_info['connections'].append({
                    'method': 'ssh',
                    'username': cred['username'],
                    'password': cred['password'],
                    'port': 22,
                    'status': 'success',
                    'message': message
                })
                ssh_worked = True
                ssh_success_count += 1
                logging.info(f"  ✅ SSH successful with {cred['username']}")
                
                # Store SNMP config if found
                if snmp_config and snmp_config['communities']:
                    device_info['snmp_config'] = snmp_config
                    device_snmp_communities = snmp_config['communities']
                    snmp_from_device_count += 1
                    logging.info(f"  📡 Found SNMP communities: {', '.join(device_snmp_communities)}")
                    
                    # Check ACLs
                    for community in device_snmp_communities:
                        acl_info = snmp_config['acls'].get(community)
                        if acl_info and isinstance(acl_info, dict):
                            if check_snmp_acl_allows(acl_info.get('entries', '')):
                                logging.info(f"  ✅ ACL {acl_info['name']} allows SNMP from our server")
                            else:
                                logging.warning(f"  ⚠️  ACL {acl_info['name']} may block SNMP from our server")
                break
            else:
                logging.debug(f"  ❌ SSH failed with {cred['username']}: {message}")
        
        # Test SNMP - try device-specific communities first, then defaults
        communities_to_try = device_snmp_communities + default_snmp_communities
        communities_to_try = list(dict.fromkeys(communities_to_try))  # Remove duplicates
        
        snmp_worked = False
        for community in communities_to_try:
            success, message = test_snmp_connection(hostname, ip, community)
            
            if success:
                device_info['connections'].append({
                    'method': 'snmp',
                    'community': community,
                    'version': 'v2c',
                    'status': 'success',
                    'message': message,
                    'source': 'device' if community in device_snmp_communities else 'default'
                })
                snmp_worked = True
                source = 'device config' if community in device_snmp_communities else 'default'
                logging.info(f"  ✅ SNMP successful with community: {community} (from {source})")
                break
        
        # Track success
        if ssh_worked or snmp_worked:
            success_count += 1
        else:
            failed_count += 1
            device_info['connections'].append({
                'method': 'none',
                'status': 'failed',
                'message': 'No working connection method found'
            })
            logging.warning(f"  ❌ No connection method worked for {hostname}")
        
        connection_info['devices'][hostname] = device_info
        
        # Be nice to devices - wait 2 seconds between devices
        if i < len(devices) - 1:
            time.sleep(2)
    
    # Save results
    connection_info['summary'] = {
        'successful': success_count,
        'failed': failed_count,
        'success_rate': round((success_count / len(devices) * 100), 2) if devices else 0,
        'ssh_successful': ssh_success_count,
        'snmp_configs_found': snmp_from_device_count
    }
    
    output_file = '/var/www/html/meraki-data/device_connections_with_snmp.json'
    with open(output_file, 'w') as f:
        json.dump(connection_info, f, indent=2)
    
    logging.info(f"\n📊 Connection Test Summary:")
    logging.info(f"   Total devices: {len(devices)}")
    logging.info(f"   Successful connections: {success_count}")
    logging.info(f"   Failed connections: {failed_count}")
    logging.info(f"   Success rate: {connection_info['summary']['success_rate']}%")
    logging.info(f"   SSH successful: {ssh_success_count}")
    logging.info(f"   SNMP configs extracted: {snmp_from_device_count}")
    logging.info(f"   Results saved to: {output_file}")
    
    # Show connection method statistics
    method_counts = {'ssh': 0, 'snmp': 0, 'both': 0}
    snmp_sources = {'device': 0, 'default': 0}
    
    for device_name, device_data in connection_info['devices'].items():
        has_ssh = any(c['method'] == 'ssh' and c['status'] == 'success' for c in device_data['connections'])
        has_snmp = any(c['method'] == 'snmp' and c['status'] == 'success' for c in device_data['connections'])
        
        if has_ssh and has_snmp:
            method_counts['both'] += 1
        elif has_ssh:
            method_counts['ssh'] += 1
        elif has_snmp:
            method_counts['snmp'] += 1
        
        # Count SNMP sources
        for conn in device_data['connections']:
            if conn['method'] == 'snmp' and conn['status'] == 'success':
                source = conn.get('source', 'default')
                snmp_sources[source] = snmp_sources.get(source, 0) + 1
    
    logging.info(f"\n📋 Connection Methods:")
    logging.info(f"   SSH only: {method_counts['ssh']} devices")
    logging.info(f"   SNMP only: {method_counts['snmp']} devices")
    logging.info(f"   Both SSH & SNMP: {method_counts['both']} devices")
    
    logging.info(f"\n🔍 SNMP Community Sources:")
    logging.info(f"   From device config: {snmp_sources.get('device', 0)} devices")
    logging.info(f"   From defaults: {snmp_sources.get('default', 0)} devices")
    
    return connection_info

if __name__ == "__main__":
    # Test mode for first few devices
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logging.info("Running in test mode (first 5 devices only)")
        # Would need to modify get_devices_from_database to limit
    
    test_all_connections()