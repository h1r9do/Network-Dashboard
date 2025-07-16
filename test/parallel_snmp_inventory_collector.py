#\!/usr/bin/env python3
"""
Parallel SNMP Inventory Collector with v2c and v3 credential testing
"""

import subprocess
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CRED_FILE = '/usr/local/bin/test/snmp_credentials.json'
RESULTS_FILE = '/var/www/html/meraki-data/parallel_snmp_results.json'
WORKING_CREDS_FILE = '/var/www/html/meraki-data/snmp_working_credentials.json'

# Global results
results_lock = threading.Lock()
results = {
    'timestamp': datetime.now().isoformat(),
    'stats': {'total': 0, 'tested': 0, 'v2c_success': 0, 'v3_success': 0, 'failed': 0},
    'devices': {},
    'working_credentials': {}
}

def load_credentials():
    """Load SNMP credentials"""
    try:
        with open(CRED_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'v2c': ['DTC4nmgt'], 'v3': []}

def test_snmp_v2c(ip, community):
    """Test SNMP v2c access"""
    cmd = ['snmpwalk', '-v', '2c', '-c', community, '-t', '5', ip, '1.3.6.1.2.1.1.1.0']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout
    except:
        return False, ""

def test_snmp_v3(ip, v3_cred):
    """Test SNMP v3 access"""
    cmd = [
        'snmpwalk', '-v', '3', '-l', 'authPriv',
        '-u', v3_cred['authname'],
        '-a', v3_cred['authalgo'],
        '-A', v3_cred['authpass'],
        '-x', v3_cred['cryptoalgo'],
        '-X', v3_cred['cryptopass'],
        '-t', '5', ip, '1.3.6.1.2.1.1.1.0'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout
    except:
        return False, ""

def collect_inventory(ip, version, credential):
    """Collect full inventory using working credential"""
    # Collect physical entities
    if version == '2c':
        cmd = ['snmpwalk', '-v', '2c', '-c', credential, '-t', '10', ip, '1.3.6.1.2.1.47.1.1.1']
    else:
        cmd = [
            'snmpwalk', '-v', '3', '-l', 'authPriv',
            '-u', credential['authname'],
            '-a', credential['authalgo'],
            '-A', credential['authpass'],
            '-x', credential['cryptoalgo'],
            '-X', credential['cryptopass'],
            '-t', '10', ip, '1.3.6.1.2.1.47.1.1.1'
        ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return parse_inventory(result.stdout)
    except:
        pass
    return []

def parse_inventory(output):
    """Parse SNMP output into inventory items"""
    items = []
    for line in output.split('\n'):
        if 'STRING:' in line:
            items.append(line.split('STRING:')[-1].strip())
    return items

def test_device(device):
    """Test a single device with all credentials"""
    hostname = device.get('hostname', device.get('name', 'Unknown'))
    ip = device.get('ip', device.get('ip_address', ''))
    
    if not ip:
        return None
    
    credentials = load_credentials()
    
    # Try v2c first
    for community in credentials['v2c']:
        success, output = test_snmp_v2c(ip, community)
        if success:
            inventory = collect_inventory(ip, '2c', community)
            result = {
                'hostname': hostname,
                'ip': ip,
                'working': True,
                'version': '2c',
                'credential': community,
                'inventory_count': len(inventory),
                'test_time': datetime.now().isoformat()
            }
            
            with results_lock:
                results['devices'][ip] = result
                results['working_credentials'][ip] = {'version': '2c', 'credential': community}
                results['stats']['v2c_success'] += 1
            
            logger.info(f"SUCCESS v2c: {hostname} ({ip}) - {community} - {len(inventory)} items")
            return result
    
    # Try v3
    for v3_cred in credentials['v3']:
        success, output = test_snmp_v3(ip, v3_cred)
        if success:
            inventory = collect_inventory(ip, 'v3', v3_cred)
            result = {
                'hostname': hostname,
                'ip': ip,
                'working': True,
                'version': 'v3',
                'credential': v3_cred['authname'],
                'inventory_count': len(inventory),
                'test_time': datetime.now().isoformat()
            }
            
            with results_lock:
                results['devices'][ip] = result
                results['working_credentials'][ip] = {'version': 'v3', 'credential': v3_cred}
                results['stats']['v3_success'] += 1
            
            logger.info(f"SUCCESS v3: {hostname} ({ip}) - {v3_cred['authname']} - {len(inventory)} items")
            return result
    
    # Failed
    with results_lock:
        results['stats']['failed'] += 1
    
    logger.warning(f"FAILED: {hostname} ({ip})")
    return {'hostname': hostname, 'ip': ip, 'working': False}

def load_devices():
    """Load all devices from various sources"""
    devices = []
    seen_ips = set()
    
    # Try to load from files
    files = [
        '/var/www/html/meraki-data/comprehensive_network_inventory.json',
        '/var/www/html/meraki-data/device_connections_sample_full.json'
    ]
    
    for file_path in files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, dict):
                                ip = v.get('ip', v.get('ip_address', ''))
                                if ip and ip not in seen_ips:
                                    v['hostname'] = k
                                    devices.append(v)
                                    seen_ips.add(ip)
                    elif isinstance(data, list):
                        for d in data:
                            ip = d.get('ip', d.get('ip_address', ''))
                            if ip and ip not in seen_ips:
                                devices.append(d)
                                seen_ips.add(ip)
        except:
            pass
    
    return devices

def main():
    """Main execution"""
    logger.info("Starting parallel SNMP inventory collection")
    
    devices = load_devices()
    results['stats']['total'] = len(devices)
    
    if not devices:
        logger.error("No devices found")
        return
    
    logger.info(f"Testing {len(devices)} devices with 5 parallel threads")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_device, device): device for device in devices}
        
        for future in as_completed(futures):
            with results_lock:
                results['stats']['tested'] += 1
                
            if results['stats']['tested'] % 10 == 0:
                logger.info(f"Progress: {results['stats']['tested']}/{len(devices)}")
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(WORKING_CREDS_FILE, 'w') as f:
        json.dump(results['working_credentials'], f, indent=2)
    
    # Summary
    logger.info(f"\nResults:")
    logger.info(f"Total: {results['stats']['total']}")
    logger.info(f"v2c Success: {results['stats']['v2c_success']}")
    logger.info(f"v3 Success: {results['stats']['v3_success']}")
    logger.info(f"Failed: {results['stats']['failed']}")

if __name__ == "__main__":
    main()
