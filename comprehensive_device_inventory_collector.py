#!/usr/bin/env python3
"""
Comprehensive Device Inventory Collector
Collects complete device inventory including:
- Device details (hostname, IP, model, version)
- All installed components (SFPs, power supplies, modules, fans)
- Serial numbers for all components
- Hardware revision information
- Environmental data (temperature, power consumption)
"""

import subprocess
import json
import time
import logging
import psycopg2
from psycopg2.extras import Json, execute_values
from datetime import datetime
import re
import concurrent.futures
from threading import Lock
import ipaddress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/comprehensive-inventory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

# Thread-safe database operations
db_lock = Lock()

# SNMP OIDs for comprehensive inventory
SNMP_OIDS = {
    # System Information
    'system': {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'sysObjectID': '1.3.6.1.2.1.1.2.0',
        'sysUpTime': '1.3.6.1.2.1.1.3.0',
        'sysContact': '1.3.6.1.2.1.1.4.0',
        'sysName': '1.3.6.1.2.1.1.5.0',
        'sysLocation': '1.3.6.1.2.1.1.6.0',
        'sysServices': '1.3.6.1.2.1.1.7.0'
    },
    
    # Entity MIB - Physical components
    'entity': {
        'entPhysicalDescr': '1.3.6.1.2.1.47.1.1.1.1.2',      # Component description
        'entPhysicalVendorType': '1.3.6.1.2.1.47.1.1.1.1.3',  # Vendor type
        'entPhysicalContainedIn': '1.3.6.1.2.1.47.1.1.1.1.4', # Container
        'entPhysicalClass': '1.3.6.1.2.1.47.1.1.1.1.5',       # Component class
        'entPhysicalParentRelPos': '1.3.6.1.2.1.47.1.1.1.1.6', # Position
        'entPhysicalName': '1.3.6.1.2.1.47.1.1.1.1.7',        # Component name
        'entPhysicalHardwareRev': '1.3.6.1.2.1.47.1.1.1.1.8',  # Hardware revision
        'entPhysicalFirmwareRev': '1.3.6.1.2.1.47.1.1.1.1.9',  # Firmware revision
        'entPhysicalSoftwareRev': '1.3.6.1.2.1.47.1.1.1.1.10', # Software revision
        'entPhysicalSerialNum': '1.3.6.1.2.1.47.1.1.1.1.11',   # Serial number
        'entPhysicalMfgName': '1.3.6.1.2.1.47.1.1.1.1.12',     # Manufacturer
        'entPhysicalModelName': '1.3.6.1.2.1.47.1.1.1.1.13',   # Model name
        'entPhysicalAlias': '1.3.6.1.2.1.47.1.1.1.1.14',       # Alias
        'entPhysicalAssetID': '1.3.6.1.2.1.47.1.1.1.1.15',     # Asset ID
        'entPhysicalIsFRU': '1.3.6.1.2.1.47.1.1.1.1.16'        # Field replaceable unit
    },
    
    # Cisco specific OIDs
    'cisco': {
        'ciscoEnvMonSupplyStatusDescr': '1.3.6.1.4.1.9.9.13.1.5.1.2',  # Power supply description
        'ciscoEnvMonSupplyState': '1.3.6.1.4.1.9.9.13.1.5.1.3',        # Power supply state
        'ciscoEnvMonSupplySource': '1.3.6.1.4.1.9.9.13.1.5.1.4',       # Power supply source
        'ciscoEnvMonFanStatusDescr': '1.3.6.1.4.1.9.9.13.1.4.1.2',     # Fan description
        'ciscoEnvMonFanState': '1.3.6.1.4.1.9.9.13.1.4.1.3',           # Fan state
        'ciscoEnvMonTemperatureStatusDescr': '1.3.6.1.4.1.9.9.13.1.3.1.2', # Temperature sensor
        'ciscoEnvMonTemperatureStatusValue': '1.3.6.1.4.1.9.9.13.1.3.1.3', # Temperature value
        'cefcModuleOperStatus': '1.3.6.1.4.1.9.9.117.1.2.1.1.2',       # Module operational status
        'cefcModuleStatusLastChangeTime': '1.3.6.1.4.1.9.9.117.1.2.1.1.3' # Module last change
    },
    
    # Interface information
    'interfaces': {
        'ifDescr': '1.3.6.1.2.1.2.2.1.2',          # Interface description
        'ifType': '1.3.6.1.2.1.2.2.1.3',           # Interface type
        'ifMtu': '1.3.6.1.2.1.2.2.1.4',            # Interface MTU
        'ifSpeed': '1.3.6.1.2.1.2.2.1.5',          # Interface speed
        'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',    # Physical address
        'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',    # Admin status
        'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',     # Operational status
        'ifAlias': '1.3.6.1.2.1.31.1.1.1.18'       # Interface alias
    },
    
    # Stack information (for stackable switches)
    'stack': {
        'cswSwitchNumCurrent': '1.3.6.1.4.1.9.9.500.1.2.1.1.1',  # Current stack members
        'cswSwitchState': '1.3.6.1.4.1.9.9.500.1.2.1.1.6',       # Switch state in stack
        'cswSwitchRole': '1.3.6.1.4.1.9.9.500.1.2.1.1.3'         # Switch role in stack
    }
}

# Component class mappings
COMPONENT_CLASSES = {
    1: 'other',
    2: 'unknown',
    3: 'chassis',
    4: 'backplane',
    5: 'container',
    6: 'powerSupply',
    7: 'fan',
    8: 'sensor',
    9: 'module',
    10: 'port',
    11: 'stack',
    12: 'cpu'
}

def get_working_credentials():
    """Get working SNMP credentials from database"""
    with db_lock:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT hostname, ip_address, snmp_version, snmp_community,
                       snmp_v3_username, snmp_v3_auth_protocol, snmp_v3_auth_password,
                       snmp_v3_priv_protocol, snmp_v3_priv_password, snmp_v3_security_level
                FROM device_snmp_credentials 
                WHERE working = TRUE
                ORDER BY hostname
            """)
            
            devices = {}
            for row in cursor.fetchall():
                hostname, ip, version, community, v3_user, v3_auth_proto, v3_auth_pass, v3_priv_proto, v3_priv_pass, v3_sec_level = row
                
                devices[hostname] = {
                    'ip': str(ip),
                    'version': version,
                    'community': community,
                    'v3_creds': {
                        'username': v3_user,
                        'auth_protocol': v3_auth_proto,
                        'auth_password': v3_auth_pass,
                        'priv_protocol': v3_priv_proto,
                        'priv_password': v3_priv_pass,
                        'security_level': v3_sec_level
                    } if version == '3' else None
                }
            
            return devices
            
        finally:
            cursor.close()
            conn.close()

def run_snmpwalk(ip, oid, version='2c', community='DTC4nmgt', v3_creds=None, timeout=10):
    """Execute snmpwalk command with proper credentials"""
    if version == '2c':
        cmd = [
            'snmpwalk', '-v', '2c', '-c', community,
            '-t', str(timeout), '-r', '1', ip, oid
        ]
    else:  # SNMPv3
        cmd = [
            'snmpwalk', '-v', '3',
            '-l', v3_creds['security_level'],
            '-u', v3_creds['username'],
            '-a', v3_creds['auth_protocol'],
            '-A', v3_creds['auth_password'],
            '-x', v3_creds['priv_protocol'],
            '-X', v3_creds['priv_password'],
            '-t', str(timeout), '-r', '1', ip, oid
        ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, 'Timeout'
    except Exception as e:
        return False, str(e)

def parse_snmp_output(output):
    """Parse SNMP output into structured data"""
    entries = []
    if not output:
        return entries
    
    for line in output.split('\n'):
        if line.strip():
            # Parse format: OID = TYPE: VALUE
            match = re.match(r'(\S+)\s*=\s*(\w+):\s*(.*)', line)
            if match:
                oid, data_type, value = match.groups()
                # Extract index from OID
                index_match = re.search(r'\.(\d+)$', oid)
                index = index_match.group(1) if index_match else None
                
                entries.append({
                    'full_oid': oid,
                    'index': index,
                    'type': data_type,
                    'value': value.strip().strip('"')
                })
    
    return entries

def collect_device_inventory(hostname, device_info):
    """Collect comprehensive inventory for a single device"""
    ip = device_info['ip']
    version = device_info['version']
    community = device_info['community']
    v3_creds = device_info['v3_creds']
    
    logger.info(f"Collecting inventory for {hostname} ({ip})")
    
    inventory = {
        'hostname': hostname,
        'ip': ip,
        'timestamp': datetime.now().isoformat(),
        'system_info': {},
        'physical_components': [],
        'interfaces': [],
        'environmental': {},
        'cisco_specific': {},
        'stack_info': {}
    }
    
    # Collect system information
    for name, oid in SNMP_OIDS['system'].items():
        success, output = run_snmpwalk(ip, oid, version, community, v3_creds, timeout=5)
        if success:
            entries = parse_snmp_output(output)
            if entries:
                inventory['system_info'][name] = entries[0]['value']
    
    # Collect physical components (Entity MIB)
    physical_components = {}
    for name, oid in SNMP_OIDS['entity'].items():
        success, output = run_snmpwalk(ip, oid, version, community, v3_creds, timeout=15)
        if success:
            entries = parse_snmp_output(output)
            for entry in entries:
                if entry['index'] not in physical_components:
                    physical_components[entry['index']] = {}
                physical_components[entry['index']][name] = entry['value']
    
    # Convert to list and add component class names
    for index, component in physical_components.items():
        component['index'] = index
        if 'entPhysicalClass' in component:
            class_num = int(component['entPhysicalClass'])
            component['component_class'] = COMPONENT_CLASSES.get(class_num, 'unknown')
        inventory['physical_components'].append(component)
    
    # Collect interface information
    interface_data = {}
    for name, oid in SNMP_OIDS['interfaces'].items():
        success, output = run_snmpwalk(ip, oid, version, community, v3_creds, timeout=10)
        if success:
            entries = parse_snmp_output(output)
            for entry in entries:
                if entry['index'] not in interface_data:
                    interface_data[entry['index']] = {}
                interface_data[entry['index']][name] = entry['value']
    
    # Convert to list
    for index, interface in interface_data.items():
        interface['index'] = index
        inventory['interfaces'].append(interface)
    
    # Collect Cisco-specific environmental data
    for name, oid in SNMP_OIDS['cisco'].items():
        success, output = run_snmpwalk(ip, oid, version, community, v3_creds, timeout=10)
        if success:
            entries = parse_snmp_output(output)
            inventory['cisco_specific'][name] = entries
    
    # Collect stack information
    for name, oid in SNMP_OIDS['stack'].items():
        success, output = run_snmpwalk(ip, oid, version, community, v3_creds, timeout=5)
        if success:
            entries = parse_snmp_output(output)
            inventory['stack_info'][name] = entries
    
    # Calculate summary statistics
    inventory['summary'] = {
        'total_components': len(inventory['physical_components']),
        'component_types': {},
        'interfaces_count': len(inventory['interfaces']),
        'has_environmental_data': bool(inventory['cisco_specific']),
        'collection_success': True
    }
    
    # Count component types
    for component in inventory['physical_components']:
        comp_class = component.get('component_class', 'unknown')
        inventory['summary']['component_types'][comp_class] = inventory['summary']['component_types'].get(comp_class, 0) + 1
    
    logger.info(f"✓ {hostname} - {inventory['summary']['total_components']} components, {inventory['summary']['interfaces_count']} interfaces")
    
    return inventory

def save_inventory_to_db(inventory):
    """Save comprehensive inventory to database"""
    with db_lock:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Insert or update main inventory record
            cursor.execute("""
                INSERT INTO comprehensive_device_inventory (
                    hostname, ip_address, collection_timestamp, 
                    system_info, physical_components, interfaces,
                    environmental_data, cisco_specific, stack_info, summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hostname, ip_address) DO UPDATE SET
                    collection_timestamp = EXCLUDED.collection_timestamp,
                    system_info = EXCLUDED.system_info,
                    physical_components = EXCLUDED.physical_components,
                    interfaces = EXCLUDED.interfaces,
                    environmental_data = EXCLUDED.environmental_data,
                    cisco_specific = EXCLUDED.cisco_specific,
                    stack_info = EXCLUDED.stack_info,
                    summary = EXCLUDED.summary
            """, (
                inventory['hostname'],
                inventory['ip'],
                inventory['timestamp'],
                Json(inventory['system_info']),
                Json(inventory['physical_components']),
                Json(inventory['interfaces']),
                Json(inventory.get('environmental', {})),
                Json(inventory['cisco_specific']),
                Json(inventory['stack_info']),
                Json(inventory['summary'])
            ))
            
            # Insert individual components for easier querying
            for component in inventory['physical_components']:
                cursor.execute("""
                    INSERT INTO device_components (
                        hostname, ip_address, component_index, component_class,
                        description, serial_number, model_name, manufacturer,
                        hardware_revision, firmware_revision, software_revision,
                        physical_name, asset_id, is_fru, collection_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hostname, ip_address, component_index) DO UPDATE SET
                        component_class = EXCLUDED.component_class,
                        description = EXCLUDED.description,
                        serial_number = EXCLUDED.serial_number,
                        model_name = EXCLUDED.model_name,
                        manufacturer = EXCLUDED.manufacturer,
                        hardware_revision = EXCLUDED.hardware_revision,
                        firmware_revision = EXCLUDED.firmware_revision,
                        software_revision = EXCLUDED.software_revision,
                        physical_name = EXCLUDED.physical_name,
                        asset_id = EXCLUDED.asset_id,
                        is_fru = EXCLUDED.is_fru,
                        collection_timestamp = EXCLUDED.collection_timestamp
                """, (
                    inventory['hostname'],
                    inventory['ip'],
                    component.get('index'),
                    component.get('component_class'),
                    component.get('entPhysicalDescr'),
                    component.get('entPhysicalSerialNum'),
                    component.get('entPhysicalModelName'),
                    component.get('entPhysicalMfgName'),
                    component.get('entPhysicalHardwareRev'),
                    component.get('entPhysicalFirmwareRev'),
                    component.get('entPhysicalSoftwareRev'),
                    component.get('entPhysicalName'),
                    component.get('entPhysicalAssetID'),
                    component.get('entPhysicalIsFRU') == 'true',
                    inventory['timestamp']
                ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving inventory for {inventory['hostname']}: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def create_database_tables():
    """Create database tables for comprehensive inventory"""
    with db_lock:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Main inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comprehensive_device_inventory (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(255) NOT NULL,
                    ip_address INET NOT NULL,
                    collection_timestamp TIMESTAMP NOT NULL,
                    system_info JSONB,
                    physical_components JSONB,
                    interfaces JSONB,
                    environmental_data JSONB,
                    cisco_specific JSONB,
                    stack_info JSONB,
                    summary JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hostname, ip_address)
                )
            """)
            
            # Components table for easier querying
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_components (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(255) NOT NULL,
                    ip_address INET NOT NULL,
                    component_index VARCHAR(50) NOT NULL,
                    component_class VARCHAR(50),
                    description TEXT,
                    serial_number VARCHAR(255),
                    model_name VARCHAR(255),
                    manufacturer VARCHAR(255),
                    hardware_revision VARCHAR(100),
                    firmware_revision VARCHAR(100),
                    software_revision VARCHAR(100),
                    physical_name VARCHAR(255),
                    asset_id VARCHAR(100),
                    is_fru BOOLEAN,
                    collection_timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hostname, ip_address, component_index)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_comprehensive_inventory_hostname 
                ON comprehensive_device_inventory(hostname)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_comprehensive_inventory_ip 
                ON comprehensive_device_inventory(ip_address)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_components_hostname 
                ON device_components(hostname)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_components_class 
                ON device_components(component_class)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_components_serial 
                ON device_components(serial_number)
            """)
            
            conn.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """Main function for comprehensive inventory collection"""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE DEVICE INVENTORY COLLECTION")
    logger.info("=" * 80)
    
    # Create database tables
    create_database_tables()
    
    # Get devices with working credentials
    devices = get_working_credentials()
    logger.info(f"Found {len(devices)} devices with working SNMP credentials")
    
    if not devices:
        logger.error("No devices with working credentials found!")
        return
    
    # Statistics
    stats = {
        'total': len(devices),
        'successful': 0,
        'failed': 0,
        'total_components': 0,
        'total_interfaces': 0
    }
    
    # Collect inventory with parallel processing
    MAX_WORKERS = 15  # Reduced to prevent overwhelming devices
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all devices
        future_to_device = {
            executor.submit(collect_device_inventory, hostname, device_info): hostname
            for hostname, device_info in devices.items()
        }
        
        # Process results
        for future in concurrent.futures.as_completed(future_to_device):
            hostname = future_to_device[future]
            try:
                inventory = future.result()
                
                # Save to database
                save_inventory_to_db(inventory)
                
                stats['successful'] += 1
                stats['total_components'] += inventory['summary']['total_components']
                stats['total_interfaces'] += inventory['summary']['interfaces_count']
                
                # Progress update
                if stats['successful'] % 10 == 0:
                    progress = (stats['successful'] + stats['failed']) / stats['total'] * 100
                    logger.info(f"Progress: {progress:.1f}% - Success: {stats['successful']}, Failed: {stats['failed']}")
                
            except Exception as e:
                logger.error(f"Failed to collect inventory for {hostname}: {e}")
                stats['failed'] += 1
    
    # Save summary to file
    summary_file = '/var/www/html/meraki-data/comprehensive_inventory_summary.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'collection_timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'devices_processed': stats['successful'],
            'total_components_collected': stats['total_components'],
            'total_interfaces_collected': stats['total_interfaces']
        }, f, indent=2)
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE INVENTORY COLLECTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total devices: {stats['total']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total components collected: {stats['total_components']}")
    logger.info(f"Total interfaces collected: {stats['total_interfaces']}")
    logger.info(f"Success rate: {stats['successful']/stats['total']*100:.1f}%")
    logger.info(f"Summary saved to: {summary_file}")

if __name__ == '__main__':
    main()