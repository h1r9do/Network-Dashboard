#\!/usr/bin/env python3
"""
Simple Sequential SNMP Inventory Collector
Collects SNMP data from network devices one at a time
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pysnmp.hlapi import *
import socket
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_models import (
    get_db_session, NetworkDevice, NetworkInterface, 
    DeviceInventory, DeviceModule, InterfaceStatistics
)

# Standard MIBs for device information
STANDARD_OIDS = {
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysObjectID': '1.3.6.1.2.1.1.2.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysContact': '1.3.6.1.2.1.1.4.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysLocation': '1.3.6.1.2.1.1.6.0',
    'sysServices': '1.3.6.1.2.1.1.7.0'
}

# Interface MIBs
INTERFACE_OIDS = {
    'ifDescr': '1.3.6.1.2.1.2.2.1.2',
    'ifType': '1.3.6.1.2.1.2.2.1.3',
    'ifMtu': '1.3.6.1.2.1.2.2.1.4',
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
    'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
    'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
    'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
    'ifAlias': '1.3.6.1.2.1.31.1.1.1.18'
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SNMPCollector:
    def __init__(self):
        self.session = get_db_session()
        self.v2c_community = os.environ.get('SNMP_COMMUNITY', 'DTC4nmgt')
        self.v3_user = os.environ.get('SNMPV3_USER', 'dtsnmpuser')
        self.v3_auth_key = os.environ.get('SNMPV3_AUTH_KEY', 'N0Acc3ss\!')
        self.v3_priv_key = os.environ.get('SNMPV3_PRIV_KEY', 'dtPrivP@ss')
        
    def test_device(self, hostname, ip_address):
        """Test a single device with both SNMP v2c and v3"""
        logger.info(f"Testing device: {hostname} ({ip_address})")
        
        # Try SNMP v2c first
        result = self._test_snmp_v2c(ip_address)
        if result['success']:
            logger.info(f"SUCCESS v2c: {hostname} ({ip_address}) - {self.v2c_community} - {result['item_count']} items")
            return 'v2c', result
            
        # Try SNMP v3
        result = self._test_snmp_v3(ip_address)
        if result['success']:
            logger.info(f"SUCCESS v3: {hostname} ({ip_address}) - {self.v3_user} - {result['item_count']} items")
            return 'v3', result
            
        logger.warning(f"FAILED: {hostname} ({ip_address}) - No SNMP access")
        return None, None
        
    def _test_snmp_v2c(self, ip_address):
        """Test SNMP v2c connectivity"""
        try:
            items = {}
            engine = SnmpEngine()
            
            # Test with sysDescr
            iterator = getCmd(
                engine,
                CommunityData(self.v2c_community),
                UdpTransportTarget((ip_address, 161), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(STANDARD_OIDS['sysDescr']))
            )
            
            for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                if errorIndication or errorStatus:
                    return {'success': False, 'error': str(errorIndication or errorStatus)}
                    
                for varBind in varBinds:
                    items['sysDescr'] = str(varBind[1])
                    
            # If we got here, v2c works - collect all standard OIDs
            for oid_name, oid in STANDARD_OIDS.items():
                if oid_name == 'sysDescr':  # Already have it
                    continue
                    
                iterator = getCmd(
                    engine,
                    CommunityData(self.v2c_community),
                    UdpTransportTarget((ip_address, 161), timeout=2, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )
                
                for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if not errorIndication and not errorStatus:
                        for varBind in varBinds:
                            items[oid_name] = str(varBind[1])
                            
            return {'success': True, 'item_count': len(items), 'items': items}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _test_snmp_v3(self, ip_address):
        """Test SNMP v3 connectivity"""
        try:
            items = {}
            engine = SnmpEngine()
            
            # Configure SNMPv3 user
            user_data = UsmUserData(
                self.v3_user,
                authKey=self.v3_auth_key,
                privKey=self.v3_priv_key,
                authProtocol=usmHMACSHAAuthProtocol,
                privProtocol=usmAesCfb128Protocol
            )
            
            # Test with sysDescr
            iterator = getCmd(
                engine,
                user_data,
                UdpTransportTarget((ip_address, 161), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(STANDARD_OIDS['sysDescr']))
            )
            
            for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                if errorIndication or errorStatus:
                    return {'success': False, 'error': str(errorIndication or errorStatus)}
                    
                for varBind in varBinds:
                    items['sysDescr'] = str(varBind[1])
                    
            # If we got here, v3 works - collect all standard OIDs
            for oid_name, oid in STANDARD_OIDS.items():
                if oid_name == 'sysDescr':  # Already have it
                    continue
                    
                iterator = getCmd(
                    engine,
                    user_data,
                    UdpTransportTarget((ip_address, 161), timeout=2, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )
                
                for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if not errorIndication and not errorStatus:
                        for varBind in varBinds:
                            items[oid_name] = str(varBind[1])
                            
            return {'success': True, 'item_count': len(items), 'items': items}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def collect_all_devices(self):
        """Collect SNMP data from all devices"""
        try:
            # Get all devices from NetworkDevice table
            devices = self.session.query(NetworkDevice).all()
            logger.info(f"Found {len(devices)} devices in NetworkDevice table")
            
            results = {
                'v2c_success': 0,
                'v3_success': 0,
                'failed': 0,
                'devices': []
            }
            
            for device in devices:
                version, result = self.test_device(device.hostname, device.ip_address)
                
                if version == 'v2c':
                    results['v2c_success'] += 1
                elif version == 'v3':
                    results['v3_success'] += 1
                else:
                    results['failed'] += 1
                    
                results['devices'].append({
                    'hostname': device.hostname,
                    'ip_address': device.ip_address,
                    'snmp_version': version,
                    'success': version is not None,
                    'data': result['items'] if result else None
                })
                
                # Add a small delay to avoid overwhelming devices
                time.sleep(0.5)
                
            return results
            
        except Exception as e:
            logger.error(f"Error collecting devices: {e}")
            return None
        finally:
            self.session.close()

def main():
    parser = argparse.ArgumentParser(description='Simple SNMP Inventory Collector')
    parser.add_argument('--test-device', help='Test a specific device by IP')
    parser.add_argument('--save-results', action='store_true', help='Save results to JSON file')
    args = parser.parse_args()
    
    collector = SNMPCollector()
    
    if args.test_device:
        # Test a single device
        version, result = collector.test_device(args.test_device, args.test_device)
        if version:
            print(f"\nSNMP {version} SUCCESS\!")
            print(f"Items collected: {result['item_count']}")
            print("\nData collected:")
            for key, value in result['items'].items():
                print(f"  {key}: {value}")
        else:
            print(f"\nSNMP FAILED for {args.test_device}")
    else:
        # Collect from all devices
        logger.info("Starting SNMP collection from all devices...")
        results = collector.collect_all_devices()
        
        if results:
            print(f"\nCollection Summary:")
            print(f"  SNMP v2c Success: {results['v2c_success']}")
            print(f"  SNMP v3 Success: {results['v3_success']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Total: {len(results['devices'])}")
            
            if args.save_results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'snmp_collection_results_{timestamp}.json'
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\nResults saved to: {filename}")

if __name__ == '__main__':
    main()
ENDSCRIPT < /dev/null
