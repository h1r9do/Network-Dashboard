#!/usr/bin/env python3
"""
Nightly Inventory Collection Script - Database Driven
Reads device access methods and credentials from database
Collects comprehensive inventory including Nexus 5K/2K relationships
"""

import sys
import os
import psycopg2
import paramiko
import json
import time
from datetime import datetime
import logging
from pysnmp.hlapi import *

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

# Setup logging
log_file = '/var/log/inventory_collection_db.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def create_device_access_table():
    """Create table to store device access methods and credentials"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create device access table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_access (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255) NOT NULL,
                mgmt_ip VARCHAR(50) NOT NULL,
                access_method VARCHAR(20) NOT NULL, -- 'ssh', 'snmp', 'api'
                username VARCHAR(100),
                password VARCHAR(255), -- Should be encrypted in production
                snmp_community VARCHAR(100),
                snmp_version VARCHAR(10),
                ssh_port INTEGER DEFAULT 22,
                enable_password VARCHAR(255),
                last_successful_access TIMESTAMP,
                last_failed_access TIMESTAMP,
                failure_count INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hostname, mgmt_ip, access_method)
            )
        """)
        
        # Create inventory collection history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_collection_history (
                id SERIAL PRIMARY KEY,
                device_id INTEGER,
                hostname VARCHAR(255),
                collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_method VARCHAR(20),
                status VARCHAR(20), -- 'success', 'failed', 'partial'
                items_collected INTEGER,
                error_message TEXT,
                collection_data JSONB
            )
        """)
        
        # Create FEX relationship table for Nexus 5K/2K
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nexus_fex_relationships (
                id SERIAL PRIMARY KEY,
                parent_hostname VARCHAR(255) NOT NULL, -- Nexus 5K
                parent_ip VARCHAR(50),
                fex_number INTEGER NOT NULL,
                fex_description VARCHAR(255),
                fex_model VARCHAR(100),
                fex_serial VARCHAR(100),
                fex_state VARCHAR(50),
                ports INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_hostname, fex_number)
            )
        """)
        
        conn.commit()
        logging.info("Device access tables created/verified successfully")
        
        # Initialize with known devices
        initialize_device_access(cursor, conn)
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def initialize_device_access(cursor, conn):
    """Initialize device access table with known credentials"""
    
    # Default SSH credentials
    default_ssh_devices = [
        ('HQ-56128P-01', '10.0.255.111', 'ssh', 'mbambic', 'Aud!o!994'),
        ('HQ-56128P-02', '10.0.255.112', 'ssh', 'mbambic', 'Aud!o!994'),
        ('AL-5000-01', '10.101.145.125', 'ssh', 'mbambic', 'Aud!o!994'),
        ('AL-5000-02', '10.101.145.126', 'ssh', 'mbambic', 'Aud!o!994'),
    ]
    
    for hostname, ip, method, username, password in default_ssh_devices:
        try:
            cursor.execute("""
                INSERT INTO device_access (hostname, mgmt_ip, access_method, username, password)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (hostname, mgmt_ip, access_method) DO UPDATE
                SET username = EXCLUDED.username, password = EXCLUDED.password
            """, (hostname, ip, method, username, password))
        except Exception as e:
            logging.warning(f"Could not insert {hostname}: {e}")
    
    # Add SNMP devices from Netdisco config
    try:
        # Read Netdisco config for SNMP communities
        with open('/home/netdisco/environments/deployment.yml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)
            
        snmp_communities = []
        if 'snmp_comm' in config:
            comms = config['snmp_comm']
            if isinstance(comms, list):
                snmp_communities = comms
            else:
                snmp_communities = [comms]
        
        # Add SNMP access for devices that don't have SSH
        if snmp_communities:
            cursor.execute("""
                INSERT INTO device_access (hostname, mgmt_ip, access_method, snmp_community, snmp_version)
                SELECT DISTINCT hostname, mgmt_ip, 'snmp', %s, 'v2c'
                FROM datacenter_inventory
                WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
                AND NOT EXISTS (
                    SELECT 1 FROM device_access 
                    WHERE device_access.hostname = datacenter_inventory.hostname
                    AND device_access.mgmt_ip = datacenter_inventory.mgmt_ip
                )
                ON CONFLICT DO NOTHING
            """, (snmp_communities[0],))
            
    except Exception as e:
        logging.warning(f"Could not read Netdisco config: {e}")
    
    conn.commit()

def collect_ssh_inventory(hostname, ip, username, password, enable_password=None):
    """Collect inventory via SSH"""
    
    logging.info(f"Collecting SSH inventory from {hostname} ({ip})")
    inventory_data = {
        'method': 'ssh',
        'timestamp': datetime.now().isoformat(),
        'basic_info': {},
        'inventory': [],
        'modules': [],
        'sfps': [],
        'fex_modules': [],
        'interfaces': []
    }
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=ip,
            username=username,
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Commands to run
        commands = [
            'show version',
            'show inventory',
            'show module',
            'show interface transceiver',
            'show fex',
            'show fex detail'
        ]
        
        for cmd in commands:
            try:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
                output = stdout.read().decode('utf-8', errors='ignore')
                
                if 'show version' in cmd:
                    inventory_data['basic_info'] = parse_show_version(output)
                elif 'show inventory' in cmd:
                    inventory_data['inventory'] = parse_show_inventory(output)
                elif 'show module' in cmd and 'fex' not in cmd:
                    inventory_data['modules'] = parse_show_module(output)
                elif 'transceiver' in cmd:
                    inventory_data['sfps'] = parse_show_transceiver(output)
                elif cmd == 'show fex':
                    inventory_data['fex_modules'] = parse_show_fex(output)
                
                time.sleep(1)  # Be nice to the device
                
            except Exception as e:
                logging.warning(f"Error running {cmd} on {hostname}: {e}")
        
        ssh.close()
        return True, inventory_data
        
    except Exception as e:
        logging.error(f"SSH connection failed to {hostname}: {e}")
        return False, {'error': str(e)}

def parse_show_fex(output):
    """Parse show fex output for N2K modules"""
    fex_modules = []
    
    for line in output.split('\n'):
        if line.strip() and not line.startswith('FEX') and not line.startswith('-'):
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                fex_modules.append({
                    'fex_number': int(parts[0]),
                    'description': parts[1],
                    'state': parts[2],
                    'model': parts[3],
                    'serial': parts[4] if len(parts) > 4 else ''
                })
    
    return fex_modules

def parse_show_version(output):
    """Parse show version output"""
    info = {}
    for line in output.split('\n'):
        if 'hostname' in line.lower():
            info['hostname'] = line.split()[-1]
        elif 'device name:' in line.lower():
            info['hostname'] = line.split(':')[-1].strip()
        elif 'model' in line.lower() or 'hardware' in line.lower():
            if 'cisco' in line.lower():
                info['model'] = line.strip()
    return info

def parse_show_inventory(output):
    """Parse show inventory output"""
    inventory = []
    current_item = {}
    
    for line in output.split('\n'):
        if line.startswith('NAME:'):
            if current_item:
                inventory.append(current_item)
            current_item = {'name': line.split('"')[1] if '"' in line else ''}
        elif 'DESCR:' in line and current_item:
            current_item['description'] = line.split('"')[1] if '"' in line else ''
        elif 'PID:' in line and current_item:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'PID:' and i+1 < len(parts):
                    current_item['pid'] = parts[i+1].rstrip(',')
                elif part == 'SN:' and i+1 < len(parts):
                    current_item['serial'] = parts[i+1].rstrip(',')
    
    if current_item:
        inventory.append(current_item)
    
    return inventory

def parse_show_module(output):
    """Parse show module output"""
    modules = []
    in_module_section = False
    
    for line in output.split('\n'):
        if 'Mod' in line and 'Ports' in line:
            in_module_section = True
            continue
        elif in_module_section and line.strip():
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                modules.append({
                    'module_number': int(parts[0]),
                    'ports': int(parts[1]) if parts[1].isdigit() else 0,
                    'card_type': ' '.join(parts[2:4]),
                    'model': parts[4] if len(parts) > 4 else '',
                    'status': parts[-1] if len(parts) > 5 else ''
                })
    
    return modules

def parse_show_transceiver(output):
    """Parse show interface transceiver output"""
    sfps = []
    current_interface = None
    
    for line in output.split('\n'):
        if line.startswith('Eth') or line.startswith('Te') or line.startswith('Gi'):
            current_interface = line.split()[0]
        elif current_interface and 'type' in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                sfps.append({
                    'interface': current_interface,
                    'type': parts[-1],
                    'status': 'present'
                })
    
    return sfps

def collect_snmp_inventory(hostname, ip, community, version='v2c'):
    """Collect inventory via SNMP"""
    
    logging.info(f"Collecting SNMP inventory from {hostname} ({ip})")
    inventory_data = {
        'method': 'snmp',
        'timestamp': datetime.now().isoformat(),
        'system_info': {},
        'interfaces': [],
        'inventory': []
    }
    
    try:
        # Get system info
        oids = [
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysObjectID', 0))
        ]
        
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0 if version == 'v1' else 1),
            UdpTransportTarget((ip, 161), timeout=10.0, retries=2),
            ContextData(),
            *oids
        )
        
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if errorIndication:
            logging.error(f"SNMP error for {hostname}: {errorIndication}")
            return False, {'error': str(errorIndication)}
        
        for varBind in varBinds:
            key = str(varBind[0].prettyPrint())
            value = str(varBind[1].prettyPrint())
            if 'sysDescr' in key:
                inventory_data['system_info']['description'] = value
            elif 'sysName' in key:
                inventory_data['system_info']['hostname'] = value
        
        return True, inventory_data
        
    except Exception as e:
        logging.error(f"SNMP collection failed for {hostname}: {e}")
        return False, {'error': str(e)}

def update_database_inventory(hostname, inventory_data):
    """Update database with collected inventory"""
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Update FEX modules if this is a Nexus 5K
        if 'fex_modules' in inventory_data and inventory_data['fex_modules']:
            for fex in inventory_data['fex_modules']:
                cursor.execute("""
                    INSERT INTO nexus_fex_relationships 
                    (parent_hostname, parent_ip, fex_number, fex_description, 
                     fex_model, fex_serial, fex_state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (parent_hostname, fex_number) DO UPDATE
                    SET fex_description = EXCLUDED.fex_description,
                        fex_model = EXCLUDED.fex_model,
                        fex_serial = EXCLUDED.fex_serial,
                        fex_state = EXCLUDED.fex_state,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    hostname,
                    inventory_data.get('mgmt_ip', ''),
                    fex['fex_number'],
                    fex['description'],
                    fex['model'],
                    fex['serial'],
                    fex['state']
                ))
        
        # Update chassis blades with proper parent relationships
        if 'modules' in inventory_data:
            # First, get the device_id
            cursor.execute("""
                SELECT id FROM datacenter_inventory 
                WHERE hostname = %s
                LIMIT 1
            """, (hostname,))
            
            result = cursor.fetchone()
            if result:
                device_id = result[0]
                
                # Clear old modules
                cursor.execute("""
                    DELETE FROM chassis_blades WHERE device_id = %s
                """, (device_id,))
                
                # Insert new modules
                for module in inventory_data['modules']:
                    cursor.execute("""
                        INSERT INTO chassis_blades
                        (device_id, module_number, card_type, model, serial_number, ports)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        device_id,
                        module['module_number'],
                        module['card_type'],
                        module['model'],
                        module.get('serial', ''),
                        module.get('ports', 0)
                    ))
        
        # Update SFP modules
        if 'sfps' in inventory_data and inventory_data['sfps']:
            cursor.execute("""
                SELECT id FROM datacenter_inventory 
                WHERE hostname = %s
                LIMIT 1
            """, (hostname,))
            
            result = cursor.fetchone()
            if result:
                device_id = result[0]
                
                # Clear old SFPs
                cursor.execute("""
                    DELETE FROM sfp_modules WHERE device_id = %s
                """, (device_id,))
                
                # Insert new SFPs
                for sfp in inventory_data['sfps']:
                    cursor.execute("""
                        INSERT INTO sfp_modules
                        (device_id, interface, module_type, status)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        device_id,
                        sfp['interface'],
                        sfp['type'],
                        sfp['status']
                    ))
        
        # Log collection history
        cursor.execute("""
            INSERT INTO inventory_collection_history
            (hostname, access_method, status, items_collected, collection_data)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            hostname,
            inventory_data.get('method', 'unknown'),
            'success',
            len(inventory_data.get('inventory', [])) + 
            len(inventory_data.get('modules', [])) + 
            len(inventory_data.get('sfps', [])),
            json.dumps(inventory_data)
        ))
        
        # Update last successful access
        cursor.execute("""
            UPDATE device_access
            SET last_successful_access = CURRENT_TIMESTAMP,
                failure_count = 0
            WHERE hostname = %s AND access_method = %s
        """, (hostname, inventory_data.get('method', 'unknown')))
        
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Database update failed for {hostname}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def run_inventory_collection():
    """Main function to run inventory collection"""
    
    logging.info("=== Starting Nightly Inventory Collection ===")
    
    # Create tables if needed
    if not create_device_access_table():
        logging.error("Failed to create/verify database tables")
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Get all devices with access methods
        cursor.execute("""
            SELECT DISTINCT
                da.hostname,
                da.mgmt_ip,
                da.access_method,
                da.username,
                da.password,
                da.snmp_community,
                da.snmp_version,
                da.enable_password
            FROM device_access da
            WHERE da.mgmt_ip IS NOT NULL AND da.mgmt_ip != ''
            AND (da.failure_count < 3 OR da.failure_count IS NULL)
            ORDER BY da.hostname
        """)
        
        devices = cursor.fetchall()
        logging.info(f"Found {len(devices)} devices to collect inventory from")
        
        success_count = 0
        failure_count = 0
        
        for device in devices:
            hostname, ip, method, username, password, snmp_comm, snmp_ver, enable_pass = device
            
            logging.info(f"Processing {hostname} ({ip}) via {method}")
            
            if method == 'ssh' and username and password:
                success, inventory_data = collect_ssh_inventory(
                    hostname, ip, username, password, enable_pass
                )
            elif method == 'snmp' and snmp_comm:
                success, inventory_data = collect_snmp_inventory(
                    hostname, ip, snmp_comm, snmp_ver or 'v2c'
                )
            else:
                logging.warning(f"No valid access method for {hostname}")
                continue
            
            if success:
                inventory_data['mgmt_ip'] = ip
                if update_database_inventory(hostname, inventory_data):
                    success_count += 1
                    logging.info(f"✅ Successfully collected inventory from {hostname}")
                else:
                    failure_count += 1
                    logging.error(f"❌ Failed to update database for {hostname}")
            else:
                failure_count += 1
                # Update failure count
                cursor.execute("""
                    UPDATE device_access
                    SET last_failed_access = CURRENT_TIMESTAMP,
                        failure_count = COALESCE(failure_count, 0) + 1
                    WHERE hostname = %s AND mgmt_ip = %s AND access_method = %s
                """, (hostname, ip, method))
                conn.commit()
            
            # Be nice to devices
            time.sleep(2)
        
        logging.info(f"=== Collection Complete: {success_count} success, {failure_count} failures ===")
        
    except Exception as e:
        logging.error(f"Collection error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Create lock file to prevent multiple runs
    lock_file = '/tmp/inventory_collection.lock'
    if os.path.exists(lock_file):
        logging.warning("Another instance is already running")
        sys.exit(1)
    
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        run_inventory_collection()
        
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)