#!/usr/bin/env python3
"""
Direct inventory collection from devices
Simplified approach that collects and stores inventory
"""

import paramiko
import psycopg2
import json
import time
import re
import logging
from datetime import datetime

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

def get_all_devices():
    """Get all devices from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT hostname, mgmt_ip, device_type, site, model
            FROM datacenter_inventory
            WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
            ORDER BY hostname
            -- LIMIT 20  -- Removed to collect all devices
        """)
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'hostname': row[0],
                'ip': row[1],
                'device_type': row[2],
                'site': row[3],
                'model': row[4]
            })
        
        return devices
        
    finally:
        cursor.close()
        conn.close()

def collect_device_inventory(hostname, ip):
    """Collect inventory from a single device"""
    inventory = {
        'hostname': hostname,
        'ip': ip,
        'collection_time': datetime.now().isoformat(),
        'chassis': [],
        'modules': [],
        'sfps': [],
        'fex': [],
        'raw_outputs': {}
    }
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect using mbambic credentials
        ssh.connect(
            hostname=ip,
            username='mbambic',
            password='Aud!o!994',
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Commands to run based on device type
        if 'Nexus' in str(hostname) or '5000' in hostname or '7000' in hostname:
            commands = {
                'inventory': 'show inventory',
                'module': 'show module',
                'fex': 'show fex',
                'transceiver': 'show interface transceiver'
            }
        else:
            commands = {
                'inventory': 'show inventory',
                'module': 'show module'
            }
        
        # Run commands
        for cmd_name, cmd in commands.items():
            try:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
                output = stdout.read().decode('utf-8', errors='ignore')
                inventory['raw_outputs'][cmd_name] = output
                
                # Parse based on command
                if cmd_name == 'inventory':
                    parse_inventory(output, inventory)
                elif cmd_name == 'module':
                    parse_modules(output, inventory)
                elif cmd_name == 'fex':
                    parse_fex(output, inventory)
                elif cmd_name == 'transceiver':
                    parse_transceivers(output, inventory)
                    
            except Exception as e:
                logging.warning(f"Error running {cmd} on {hostname}: {e}")
        
        ssh.close()
        inventory['status'] = 'success'
        
    except Exception as e:
        logging.error(f"Failed to collect from {hostname}: {e}")
        inventory['status'] = 'failed'
        inventory['error'] = str(e)
    
    return inventory

def parse_inventory(output, inventory):
    """Parse show inventory output"""
    current_item = None
    
    for line in output.split('\n'):
        line = line.strip()
        
        if line.startswith('NAME:'):
            name_match = re.search(r'NAME:\s+"([^"]+)"', line)
            desc_match = re.search(r'DESCR:\s+"([^"]+)"', line)
            
            if name_match:
                current_item = {
                    'name': name_match.group(1),
                    'description': desc_match.group(1) if desc_match else ''
                }
        
        elif line.startswith('PID:') and current_item:
            pid_match = re.search(r'PID:\s+(\S+)', line)
            vid_match = re.search(r'VID:\s+(\S+)', line)
            sn_match = re.search(r'SN:\s+(\S+)', line)
            
            if pid_match and pid_match.group(1) not in ['', 'N/A']:
                current_item['pid'] = pid_match.group(1)
                current_item['vid'] = vid_match.group(1) if vid_match else ''
                current_item['serial_number'] = sn_match.group(1) if sn_match else ''
                
                # Categorize
                if 'chassis' in current_item['name'].lower() or 'chassis' in current_item['description'].lower():
                    inventory['chassis'].append(current_item)
                elif 'module' in current_item['name'].lower() or 'module' in current_item['description'].lower():
                    inventory['modules'].append(current_item)
            
            current_item = None

def parse_modules(output, inventory):
    """Parse show module output"""
    in_module_section = False
    
    for line in output.split('\n'):
        if 'Mod' in line and 'Ports' in line:
            in_module_section = True
            continue
        
        if in_module_section and line.strip() and not line.startswith('-'):
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                module = {
                    'slot': parts[0],
                    'ports': parts[1],
                    'module_type': parts[2],
                    'model': parts[3] if len(parts) > 3 else ''
                }
                
                # Check if already in inventory from show inventory
                if not any(m.get('name', '').endswith(f"slot {module['slot']}") for m in inventory['modules']):
                    inventory['modules'].append(module)

def parse_fex(output, inventory):
    """Parse show fex output"""
    in_fex_section = False
    
    for line in output.split('\n'):
        # Look for dashed separator line which comes after headers
        if '-----' in line:
            in_fex_section = True
            continue
        
        if in_fex_section and line.strip():
            # Parse FEX line - format: 105     AL-2000-01                Online     N2K-C2248TP-1GE   SSI141109BL
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                fex = {
                    'fex_id': parts[0],
                    'description': parts[1],
                    'state': parts[2],
                    'model': parts[3] if len(parts) > 3 else '',
                    'serial': parts[4] if len(parts) > 4 else ''
                }
                inventory['fex'].append(fex)

def parse_transceivers(output, inventory):
    """Parse transceiver information"""
    current_interface = None
    current_sfp = {}
    
    for line in output.split('\n'):
        if line.startswith('Ethernet') or line.startswith('fc'):
            # Save previous SFP if exists
            if current_sfp and 'interface' in current_sfp:
                inventory['sfps'].append(current_sfp)
            
            current_interface = line.split()[0]
            current_sfp = {'interface': current_interface}
            
        elif current_interface and 'type is' in line:
            current_sfp['type'] = line.split('type is')[-1].strip()
        elif current_interface and 'name is' in line:
            current_sfp['vendor'] = line.split('name is')[-1].strip()
        elif current_interface and 'serial number is' in line:
            current_sfp['serial_number'] = line.split('serial number is')[-1].strip()
    
    # Don't forget the last one
    if current_sfp and 'interface' in current_sfp and len(current_sfp) > 1:
        inventory['sfps'].append(current_sfp)

def save_to_database(all_inventory):
    """Save collected inventory to database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create collection record
        cursor.execute("""
            INSERT INTO inventory_collections 
            (collection_date, total_devices, successful_devices, collection_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            datetime.now(),
            len(all_inventory),
            sum(1 for inv in all_inventory if inv.get('status') == 'success'),
            'direct_collection'
        ))
        
        collection_id = cursor.fetchone()[0]
        
        # Save each device's inventory
        for device_inv in all_inventory:
            if device_inv.get('status') != 'success':
                continue
                
            hostname = device_inv['hostname']
            
            # Save chassis
            for chassis in device_inv.get('chassis', []):
                cursor.execute("""
                    INSERT INTO collected_chassis 
                    (collection_id, hostname, name, description, pid, serial_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    collection_id,
                    hostname,
                    chassis.get('name'),
                    chassis.get('description'),
                    chassis.get('pid'),
                    chassis.get('serial_number')
                ))
            
            # Save modules
            for module in device_inv.get('modules', []):
                cursor.execute("""
                    INSERT INTO collected_modules
                    (collection_id, hostname, module_number, module_type, model)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    collection_id,
                    hostname,
                    module.get('slot', module.get('name')),
                    module.get('module_type', module.get('description')),
                    module.get('model', module.get('pid'))
                ))
            
            # Save SFPs
            for sfp in device_inv.get('sfps', []):
                cursor.execute("""
                    INSERT INTO collected_sfps
                    (collection_id, hostname, interface, sfp_type, vendor, serial_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    collection_id,
                    hostname,
                    sfp.get('interface'),
                    sfp.get('type'),
                    sfp.get('vendor'),
                    sfp.get('serial_number')
                ))
            
            # Save FEX
            for fex in device_inv.get('fex', []):
                cursor.execute("""
                    INSERT INTO collected_fex_modules
                    (collection_id, parent_hostname, fex_number, description, model, serial_number, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    collection_id,
                    hostname,
                    fex.get('fex_id'),
                    fex.get('description'),
                    fex.get('model'),
                    fex.get('serial', ''),
                    fex.get('state')
                ))
        
        conn.commit()
        logging.info(f"✅ Saved to database - Collection ID: {collection_id}")
        return collection_id
        
    except Exception as e:
        logging.error(f"Database save failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main execution"""
    logging.info("Starting direct inventory collection...")
    
    # Get devices
    devices = get_all_devices()
    logging.info(f"Found {len(devices)} devices to collect from")
    
    # Collect inventory
    all_inventory = []
    
    for i, device in enumerate(devices):
        logging.info(f"[{i+1}/{len(devices)}] Collecting from {device['hostname']} ({device['ip']})")
        
        inventory = collect_device_inventory(device['hostname'], device['ip'])
        all_inventory.append(inventory)
        
        # Show summary
        if inventory['status'] == 'success':
            logging.info(f"  ✅ Success - Chassis: {len(inventory['chassis'])}, "
                        f"Modules: {len(inventory['modules'])}, "
                        f"SFPs: {len(inventory['sfps'])}, "
                        f"FEX: {len(inventory['fex'])}")
        else:
            logging.warning(f"  ❌ Failed: {inventory.get('error', 'Unknown error')}")
        
        # Be nice to devices
        if i < len(devices) - 1:
            time.sleep(3)
    
    # Save to JSON
    output_file = '/var/www/html/meraki-data/direct_inventory_collection.json'
    with open(output_file, 'w') as f:
        json.dump(all_inventory, f, indent=2)
    logging.info(f"✅ Saved to JSON: {output_file}")
    
    # Save to database
    try:
        collection_id = save_to_database(all_inventory)
        
        # Summary
        success_count = sum(1 for inv in all_inventory if inv.get('status') == 'success')
        logging.info(f"\n📊 Collection Summary:")
        logging.info(f"   Total devices: {len(devices)}")
        logging.info(f"   Successful: {success_count}")
        logging.info(f"   Failed: {len(devices) - success_count}")
        logging.info(f"   Success rate: {round(success_count/len(devices)*100, 2)}%")
        logging.info(f"   Database collection ID: {collection_id}")
        
    except Exception as e:
        logging.error(f"Failed to save to database: {e}")

if __name__ == "__main__":
    main()