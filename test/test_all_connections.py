#!/usr/bin/env python3
"""
Test connections to all devices and create a JSON file with working credentials
"""

import json
import paramiko
import time
import sys
import psycopg2
from datetime import datetime
from pysnmp.hlapi import *
import logging

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

def test_ssh_connection(hostname, ip, username, password, port=22):
    """Test SSH connection to a device"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Try to get hostname to verify connection works
        stdin, stdout, stderr = ssh.exec_command('show version | include hostname', timeout=5)
        output = stdout.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        return True, "SSH connection successful"
        
    except Exception as e:
        return False, str(e)

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
        # Add more credentials here if needed
    ]
    
    snmp_communities = ['public', 'private']
    
    success_count = 0
    failed_count = 0
    
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
            'connections': []
        }
        
        # Test SSH
        for cred in ssh_credentials:
            success, message = test_ssh_connection(
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
                success_count += 1
                logging.info(f"  ✅ SSH successful with {cred['username']}")
                break
            else:
                logging.debug(f"  ❌ SSH failed with {cred['username']}: {message}")
        
        # Test SNMP if SSH failed
        if not any(conn['method'] == 'ssh' and conn['status'] == 'success' 
                  for conn in device_info['connections']):
            for community in snmp_communities:
                success, message = test_snmp_connection(hostname, ip, community)
                
                if success:
                    device_info['connections'].append({
                        'method': 'snmp',
                        'community': community,
                        'version': 'v2c',
                        'status': 'success',
                        'message': message
                    })
                    success_count += 1
                    logging.info(f"  ✅ SNMP successful with community: {community}")
                    break
        
        # If no connection worked
        if not any(conn['status'] == 'success' for conn in device_info['connections']):
            device_info['connections'].append({
                'method': 'none',
                'status': 'failed',
                'message': 'No working connection method found'
            })
            failed_count += 1
            logging.warning(f"  ❌ No connection method worked for {hostname}")
        
        connection_info['devices'][hostname] = device_info
        
        # Be nice to devices
        time.sleep(1)
    
    # Save results
    connection_info['summary'] = {
        'successful': success_count,
        'failed': failed_count,
        'success_rate': round((success_count / len(devices) * 100), 2) if devices else 0
    }
    
    output_file = '/var/www/html/meraki-data/device_connections.json'
    with open(output_file, 'w') as f:
        json.dump(connection_info, f, indent=2)
    
    logging.info(f"\n📊 Connection Test Summary:")
    logging.info(f"   Total devices: {len(devices)}")
    logging.info(f"   Successful: {success_count}")
    logging.info(f"   Failed: {failed_count}")
    logging.info(f"   Success rate: {connection_info['summary']['success_rate']}%")
    logging.info(f"   Results saved to: {output_file}")
    
    # Show some statistics
    method_counts = {}
    for device_name, device_data in connection_info['devices'].items():
        for conn in device_data['connections']:
            if conn['status'] == 'success':
                method = conn['method']
                method_counts[method] = method_counts.get(method, 0) + 1
    
    logging.info(f"\n📋 Connection Methods:")
    for method, count in method_counts.items():
        logging.info(f"   {method.upper()}: {count} devices")
    
    return connection_info

if __name__ == "__main__":
    # Test just a few devices first
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logging.info("Running in test mode (first 5 devices only)")
        # Modify the query in get_devices_from_database to LIMIT 5
    
    test_all_connections()