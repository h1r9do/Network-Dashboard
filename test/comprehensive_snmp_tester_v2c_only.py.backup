#\!/usr/bin/env python3
"""
Comprehensive SNMP Inventory Tester - Test ALL devices in inventory
"""

import subprocess
import json
import time
import logging
import psycopg2
from datetime import datetime
import re
import sys
from collections import defaultdict

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/comprehensive_snmp_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

SNMP_COMMUNITIES = ['DTC4nmgt', 'DTC4nmgt98', '3$laM3Plz', 'DTC4nmgt@es0', 'DTC4nmgt98@es0']

def run_snmp_test(ip_address, community, timeout=5):
    try:
        cmd = ['snmpwalk', '-v', '2c', '-c', community, '-t', str(timeout), '-r', '1', ip_address, '1.3.6.1.2.1.1.1.0']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        
        if result.returncode == 0 and result.stdout.strip():
            match = re.search(r'STRING:\s*(.*)', result.stdout)
            sys_descr = match.group(1).strip() if match else result.stdout.strip()
            return True, sys_descr[:100] + "..." if len(sys_descr) > 100 else sys_descr
        else:
            return False, result.stderr.strip() or "No response"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_all_devices():
    devices = []
    
    # Load from connection files
    connection_files = [
        '/var/www/html/meraki-data/device_connections_sample_full.json',
        '/var/www/html/meraki-data/device_connections_sample.json'
    ]
    
    for file_path in connection_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'devices' in data:
                    for hostname, device_info in data['devices'].items():
                        devices.append({
                            'hostname': hostname,
                            'ip': device_info.get('ip', ''),
                            'source': 'connections_file',
                            'device_type': device_info.get('device_type', 'Unknown'),
                            'model': device_info.get('model', 'Unknown')
                        })
                else:
                    for hostname, device_info in data.items():
                        if isinstance(device_info, dict) and 'ip' in device_info:
                            devices.append({
                                'hostname': hostname,
                                'ip': device_info['ip'],
                                'source': 'snmp_extracted',
                                'device_type': 'Unknown',
                                'model': 'Unknown'
                            })
        except Exception as e:
            logger.warning(f"Could not load {file_path}: {e}")
    
    # Load from comprehensive inventory (IP-keyed format)
    try:
        with open('/var/www/html/meraki-data/comprehensive_network_inventory.json', 'r') as f:
            comp_data = json.load(f)
            for ip_address, device_data in comp_data.items():
                if isinstance(device_data, dict):
                    # Extract hostname from various possible sources
                    hostname = 'Unknown'
                    device_type = 'Unknown'
                    model = 'Unknown'
                    vendor = 'Unknown'
                    site = 'Unknown'
                    
                    # Try SSH data first
                    if 'ssh_data' in device_data and 'basic_info' in device_data['ssh_data']:
                        ssh_info = device_data['ssh_data']['basic_info']
                        hostname = ssh_info.get('hostname', hostname)
                    
                    # Try Meraki data
                    if 'meraki_data' in device_data:
                        meraki_info = device_data['meraki_data']
                        if hostname == 'Unknown':
                            hostname = meraki_info.get('name', meraki_info.get('hostname', hostname))
                        device_type = meraki_info.get('model', device_type)
                        model = meraki_info.get('model', model)
                        if 'MX' in model or 'MR' in model or 'MS' in model:
                            vendor = 'Meraki'
                    
                    # Try SNMP data
                    if 'snmp_data' in device_data:
                        snmp_info = device_data['snmp_data']
                        if hostname == 'Unknown':
                            hostname = snmp_info.get('hostname', hostname)
                    
                    # Use IP as hostname if still unknown
                    if hostname == 'Unknown':
                        hostname = ip_address
                    
                    devices.append({
                        'hostname': hostname,
                        'ip': ip_address,
                        'source': 'comprehensive_inventory',
                        'device_type': device_type,
                        'model': model,
                        'vendor': vendor,
                        'site': site
                    })
    except Exception as e:
        logger.warning(f"Could not load comprehensive inventory: {e}")
    
    # Remove duplicates by IP and filter valid IPs
    seen_ips = set()
    unique_devices = []
    
    for device in devices:
        ip = device['ip']
        if ip and ip not in seen_ips and re.match(r'\d+\.\d+\.\d+\.\d+', ip):
            seen_ips.add(ip)
            unique_devices.append(device)
    
    logger.info(f"Loaded {len(unique_devices)} unique devices from {len(devices)} total entries")
    return unique_devices

def test_device_snmp_communities(device):
    hostname = device['hostname']
    ip = device['ip']
    
    test_result = {
        'hostname': hostname,
        'ip': ip,
        'source': device.get('source', 'unknown'),
        'device_type': device.get('device_type', 'Unknown'),
        'model': device.get('model', 'Unknown'),
        'vendor': device.get('vendor', 'Unknown'),
        'site': device.get('site', 'Unknown'),
        'snmp_success': False,
        'working_community': None,
        'system_description': None,
        'community_results': [],
        'test_timestamp': datetime.now().isoformat()
    }
    
    for community in SNMP_COMMUNITIES:
        success, message = run_snmp_test(ip, community)
        
        result = {
            'community': community,
            'success': success,
            'message': message
        }
        test_result['community_results'].append(result)
        
        if success and not test_result['snmp_success']:
            test_result['snmp_success'] = True
            test_result['working_community'] = community
            test_result['system_description'] = message
            logger.info(f"  ✅ {hostname} ({ip}) - SUCCESS with {community}")
            break
        
        time.sleep(0.2)
    
    if not test_result['snmp_success']:
        logger.warning(f"  ❌ {hostname} ({ip}) - ALL COMMUNITIES FAILED")
    
    return test_result

def main():
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE SNMP INVENTORY TESTING")
    logger.info(f"Testing all devices with communities: {', '.join(SNMP_COMMUNITIES)}")
    logger.info("=" * 80)
    
    devices = get_all_devices()
    
    if not devices:
        logger.error("No devices found to test!")
        return
    
    logger.info(f"Starting SNMP tests on {len(devices)} devices...")
    
    results = []
    successful_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, device in enumerate(devices, 1):
        if i % 10 == 1 or i == len(devices):
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(devices) - i) / rate if rate > 0 else 0
            logger.info(f"\n[{i}/{len(devices)}] Progress: {(i/len(devices)*100):.1f}%  < /dev/null |  "
                       f"Rate: {rate:.1f} devices/sec | ETA: {eta/60:.1f} min")
        
        logger.info(f"Testing {device['hostname']} ({device['ip']})...")
        
        result = test_device_snmp_communities(device)
        results.append(result)
        
        if result['snmp_success']:
            successful_count += 1
        else:
            failed_count += 1
        
        time.sleep(1)
    
    # Save results
    logger.info("\nSaving results...")
    
    output_file = '/tmp/comprehensive_snmp_test_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'test_timestamp': datetime.now().isoformat(),
            'total_devices_tested': len(devices),
            'successful_devices': successful_count,
            'failed_devices': failed_count,
            'communities_tested': SNMP_COMMUNITIES,
            'results': results
        }, f, indent=2)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total devices tested: {len(devices)}")
    logger.info(f"Successful SNMP access: {successful_count}")
    logger.info(f"Failed SNMP access: {failed_count}")
    logger.info(f"Overall success rate: {(successful_count/len(devices)*100):.1f}%")
    
    # Community usage
    community_usage = defaultdict(int)
    for result in results:
        if result['working_community']:
            community_usage[result['working_community']] += 1
    
    if community_usage:
        logger.info(f"\nWorking communities:")
        for community, count in sorted(community_usage.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {community}: {count} devices")
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Generate NMIS-compatible JSON
    generate_nmis_json(results)

def generate_nmis_json(results):
    """Generate NMIS-compatible JSON with inventory and working SNMP credentials"""
    
    nmis_data = {
        'generation_timestamp': datetime.now().isoformat(),
        'total_devices': len(results),
        'devices_with_snmp': sum(1 for r in results if r['snmp_success']),
        'devices': {}
    }
    
    for result in results:
        device_info = {
            'hostname': result['hostname'],
            'ip_address': result['ip'],
            'source': result.get('source', 'unknown'),
            'device_type': result.get('device_type', 'Unknown'),
            'model': result.get('model', 'Unknown'),
            'vendor': result.get('vendor', 'Unknown'),
            'site': result.get('site', 'Unknown'),
            'snmp_enabled': result['snmp_success'],
            'snmp_credentials': {}
        }
        
        if result['snmp_success']:
            device_info['snmp_credentials'] = {
                'working_community': result['working_community'],
                'version': '2c',
                'port': 161,
                'timeout': 10,
                'retries': 3,
                'system_description': result['system_description']
            }
            
            # Include all tested communities for reference
            device_info['all_communities_tested'] = [
                {'community': test['community'], 'success': test['success']} 
                for test in result['community_results']
            ]
        
        nmis_data['devices'][result['hostname']] = device_info
    
    # Save NMIS-compatible file
    nmis_file = '/tmp/nmis_inventory_with_snmp.json'
    with open(nmis_file, 'w') as f:
        json.dump(nmis_data, f, indent=2)
    
    logger.info(f"\nNMIS-compatible inventory saved to: {nmis_file}")
    logger.info(f"Total devices: {nmis_data['total_devices']}")
    logger.info(f"Devices with SNMP: {nmis_data['devices_with_snmp']}")
    
    # Create summary by vendor/type
    vendor_summary = defaultdict(lambda: {'total': 0, 'snmp_working': 0})
    for device in nmis_data['devices'].values():
        vendor = device['vendor']
        vendor_summary[vendor]['total'] += 1
        if device['snmp_enabled']:
            vendor_summary[vendor]['snmp_working'] += 1
    
    logger.info("\nSNMP Success by Vendor:")
    for vendor, stats in sorted(vendor_summary.items()):
        success_rate = (stats['snmp_working'] / stats['total'] * 100) if stats['total'] > 0 else 0
        logger.info(f"  {vendor}: {stats['snmp_working']}/{stats['total']} ({success_rate:.1f}%)")

if __name__ == "__main__":
    main()
