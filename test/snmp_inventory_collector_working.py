#\!/usr/bin/env python3
"""
Working SNMP Inventory Collector using snmpwalk command line tool
"""

import subprocess
import json
import time
import logging
import psycopg2
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

SNMP_COMMUNITY = 'DTC4nmgt'

def run_snmpwalk(ip_address, oid, timeout=10):
    try:
        cmd = ['snmpwalk', '-v', '2c', '-c', SNMP_COMMUNITY, '-t', str(timeout), ip_address, oid]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, f"Command error: {str(e)}"

def parse_snmp_output(output):
    entries = []
    for line in output.split('\n'):
        if line.strip():
            match = re.match(r'(\S+)\s*=\s*(\w+):\s*(.*)', line)
            if match:
                oid, data_type, value = match.groups()
                entries.append({
                    'oid': oid,
                    'type': data_type,
                    'value': value.strip()
                })
    return entries

def collect_device_inventory(hostname, ip_address):
    inventory = {
        'hostname': hostname,
        'ip_address': ip_address,
        'collection_timestamp': datetime.now().isoformat(),
        'system_info': {},
        'physical_entities': [],
        'collection_status': 'success',
        'errors': []
    }
    
    logger.info(f"Collecting SNMP inventory from {hostname} ({ip_address})")
    
    # System information
    system_oids = {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'sysName': '1.3.6.1.2.1.1.5.0',
        'sysUpTime': '1.3.6.1.2.1.1.3.0'
    }
    
    for info_name, oid in system_oids.items():
        success, output = run_snmpwalk(ip_address, oid)
        if success:
            parsed = parse_snmp_output(output)
            if parsed:
                inventory['system_info'][info_name] = parsed[0]['value']
                logger.info(f"  {info_name}: {parsed[0]['value'][:50]}...")
        else:
            logger.warning(f"  Failed to get {info_name}: {output}")
            inventory['errors'].append(f"Failed {info_name}: {output}")
    
    # Physical entities
    entity_oids = {
        'entPhysicalDescr': '1.3.6.1.2.1.47.1.1.1.1.2',
        'entPhysicalName': '1.3.6.1.2.1.47.1.1.1.1.7',
        'entPhysicalModelName': '1.3.6.1.2.1.47.1.1.1.1.13',
        'entPhysicalSerialNum': '1.3.6.1.2.1.47.1.1.1.1.11'
    }
    
    logger.info(f"  Collecting physical entities...")
    for entity_name, oid in entity_oids.items():
        success, output = run_snmpwalk(ip_address, oid)
        if success:
            parsed = parse_snmp_output(output)
            for entry in parsed:
                index_match = re.search(r'\.(\d+)$', entry['oid'])
                if index_match:
                    index = index_match.group(1)
                    entity = next((e for e in inventory['physical_entities'] if e['index'] == index), None)
                    if not entity:
                        entity = {'index': index}
                        inventory['physical_entities'].append(entity)
                    entity[entity_name] = entry['value']
        else:
            logger.warning(f"  Failed to get {entity_name}: {output}")
            inventory['errors'].append(f"Failed {entity_name}: {output}")
    
    entity_count = len(inventory['physical_entities'])
    logger.info(f"  Collected: {entity_count} physical entities")
    
    if inventory['errors']:
        inventory['collection_status'] = 'partial'
    
    return inventory

def save_to_database(inventory_data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO inventory_collections (total_devices, successful_devices, collection_type, notes)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (1, 1 if inventory_data['collection_status'] == 'success' else 0, 'snmp', 'SNMP via snmpwalk'))
        
        collection_id = cursor.fetchone()[0]
        
        # Save entities that have descriptions
        saved_entities = 0
        for entity in inventory_data['physical_entities']:
            if entity.get('entPhysicalDescr'):
                cursor.execute("""
                    INSERT INTO collected_chassis 
                    (collection_id, hostname, name, description, pid, vid, serial_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    collection_id,
                    inventory_data['hostname'],
                    entity.get('entPhysicalName', ''),
                    entity.get('entPhysicalDescr', ''),
                    entity.get('entPhysicalModelName', ''),
                    '',  # vid not available
                    entity.get('entPhysicalSerialNum', '')
                ))
                saved_entities += 1
        
        cursor.execute("""
            INSERT INTO collected_raw_inventory 
            (collection_id, hostname, command, output)
            VALUES (%s, %s, %s, %s)
        """, (
            collection_id,
            inventory_data['hostname'],
            'snmp_system_info',
            json.dumps(inventory_data['system_info'])
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"  Saved {saved_entities} entities to database (collection_id: {collection_id})")
        return collection_id
        
    except Exception as e:
        logger.error(f"  Database save failed: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info("SNMP Inventory Collector - Working Version")
    logger.info(f"Using community: {SNMP_COMMUNITY}")
    logger.info("=" * 60)
    
    test_devices = [
        {'hostname': '2960-CX-Series-NOC', 'ip': '10.0.255.10'},
        {'hostname': 'AL-5000-01', 'ip': '10.101.145.125'},
        {'hostname': 'AL-7000-01-ADMIN', 'ip': '10.101.145.123'}
    ]
    
    results = []
    successful_collections = 0
    
    for i, device in enumerate(test_devices, 1):
        hostname = device['hostname']
        ip = device['ip']
        
        logger.info(f"\n[{i}/{len(test_devices)}] Processing {hostname}...")
        
        inventory = collect_device_inventory(hostname, ip)
        collection_id = save_to_database(inventory)
        
        if collection_id:
            inventory['collection_id'] = collection_id
            successful_collections += 1
        
        results.append(inventory)
        
        if i < len(test_devices):
            time.sleep(3)
    
    output_file = '/var/www/html/meraki-data/snmp_inventory_collection_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'collection_timestamp': datetime.now().isoformat(),
            'total_devices': len(test_devices),
            'successful_collections': successful_collections,
            'snmp_community': SNMP_COMMUNITY,
            'results': results
        }, f, indent=2)
    
    logger.info("\n" + "=" * 60)
    logger.info("COLLECTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Devices processed: {len(test_devices)}")
    logger.info(f"Successful collections: {successful_collections}")
    logger.info(f"Success rate: {(successful_collections/len(test_devices)*100):.1f}%")
    
    for result in results:
        status = "✅" if result['collection_status'] == 'success' else "⚠️" 
        entity_count = len(result['physical_entities'])
        logger.info(f"  {status} {result['hostname']}: {entity_count} entities")
    
    logger.info(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
