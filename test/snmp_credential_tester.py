#\!/usr/bin/env python3
"""
SNMP Credential Tester - Test from Current Server IP (10.0.145.130)
"""

import json
import time
import sys
import logging
import socket
from datetime import datetime
from pysnmp.hlapi import nextCmd, getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

EXTRACTED_COMMUNITIES = ['DTC4nmgt', 'DTC4nmgt98', 'DTC4nmgt@es0', 'DTC4nmgt98@es0', '3$laM3Plz']

def get_current_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '10.0.145.130'

def test_snmp_access(hostname, ip, community, timeout=5):
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=timeout),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),
            lexicographicMode=False,
            maxRows=1
        ):
            if errorIndication:
                return False, f"SNMP Error: {errorIndication}"
            elif errorStatus:
                return False, f"SNMP Error: {errorStatus.prettyPrint()}"
            else:
                sys_descr = str(varBinds[0][1])
                return True, f"Success - System: {sys_descr[:100]}"
        return False, "No SNMP response"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def get_device_list():
    devices = []
    
    try:
        with open('/var/www/html/meraki-data/device_connections_sample_full.json', 'r') as f:
            conn_data = json.load(f)
            for hostname, device_info in conn_data.get('devices', {}).items():
                devices.append({
                    'hostname': hostname,
                    'ip': device_info['ip'],
                    'device_type': device_info.get('device_type', 'Unknown'),
                    'model': device_info.get('model', 'Unknown')
                })
    except Exception as e:
        logger.warning(f"Could not load device connections file: {e}")
    
    try:
        with open('/var/www/html/meraki-data/device_connections_sample.json', 'r') as f:
            snmp_data = json.load(f)
            for hostname, device_info in snmp_data.items():
                existing = next((d for d in devices if d['hostname'] == hostname), None)
                if existing:
                    existing['extracted_communities'] = device_info.get('device_snmp_communities', [])
    except Exception as e:
        logger.warning(f"Could not load SNMP extraction file: {e}")
    
    return devices

def test_device_snmp_access(device):
    hostname = device['hostname']
    ip = device['ip']
    
    logger.info(f"Testing {hostname} ({ip})")
    
    communities_to_test = []
    if 'extracted_communities' in device:
        communities_to_test.extend(device['extracted_communities'])
    communities_to_test.extend(EXTRACTED_COMMUNITIES)
    communities_to_test = list(dict.fromkeys(communities_to_test))
    
    result = {
        'hostname': hostname,
        'ip': ip,
        'device_type': device.get('device_type', 'Unknown'),
        'snmp_success': False,
        'working_communities': [],
        'community_tests': []
    }
    
    for community in communities_to_test:
        success, message = test_snmp_access(hostname, ip, community)
        
        test_result = {
            'community': community,
            'success': success,
            'message': message
        }
        result['community_tests'].append(test_result)
        
        if success:
            result['snmp_success'] = True
            result['working_communities'].append(community)
            logger.info(f"  ✅ SUCCESS with '{community}': {message[:50]}...")
        
        time.sleep(0.5)
    
    if not result['snmp_success']:
        logger.warning(f"  ❌ No SNMP access found for {hostname}")
    
    return result

def main():
    logger.info("=" * 60)
    logger.info("SNMP Credential Tester - Testing from Current Server IP")
    logger.info(f"Source IP: {get_current_ip()}")
    logger.info("=" * 60)
    
    devices = get_device_list()
    
    if not devices:
        logger.error("No devices found to test!")
        return
    
    logger.info(f"Testing SNMP access to {len(devices)} devices...")
    
    results = []
    successful_devices = 0
    
    for i, device in enumerate(devices, 1):
        logger.info(f"\n[{i}/{len(devices)}] Testing {device['hostname']}...")
        result = test_device_snmp_access(device)
        results.append(result)
        
        if result['snmp_success']:
            successful_devices += 1
        
        if i < len(devices):
            time.sleep(2)
    
    output_file = '/var/www/html/meraki-data/snmp_access_test_results.json'
    result_data = {
        'test_timestamp': datetime.now().isoformat(),
        'test_source_ip': get_current_ip(),
        'total_devices_tested': len(results),
        'successful_devices': successful_devices,
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    logger.info("\n" + "=" * 60)
    logger.info("SNMP ACCESS TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total devices tested: {len(devices)}")
    logger.info(f"Successful SNMP access: {successful_devices}")
    logger.info(f"Failed SNMP access: {len(devices) - successful_devices}")
    logger.info(f"Success rate: {(successful_devices/len(devices)*100):.1f}%")
    
    if successful_devices > 0:
        logger.info(f"\n✅ DEVICES WITH SNMP ACCESS:")
        for result in results:
            if result['snmp_success']:
                communities = ', '.join(result['working_communities'])
                logger.info(f"   {result['hostname']} ({result['ip']}) - Communities: {communities}")
    
    logger.info(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
