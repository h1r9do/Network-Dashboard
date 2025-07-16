#!/usr/bin/env python3
"""
Nightly SNMP Inventory Collection - Web Format V2
Maintains parent hostname in all rows for better identification
"""
import psycopg2
import json
import logging
from datetime import datetime
from collections import defaultdict

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nightly_inventory_web_format_v2')

def get_site_from_ip(ip):
    """Determine site based on IP address"""
    if not ip:
        return 'Unknown'
    
    if ip.startswith('10.0.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.255.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.4.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.5.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.12.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.13.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('172.16.4.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('192.168.200.'):
        return 'AZ-Alameda-DC'
    elif ip.startswith('10.101.'):
        return 'AZ-Alameda-DC'
    elif ip.startswith('10.44.'):
        return 'Equinix-Seattle'
    elif ip.startswith('10.41.'):
        return 'AZ-Desert-Ridge'
    elif ip.startswith('10.42.'):
        return 'TX-Dallas-DC'
    elif ip.startswith('10.43.'):
        return 'GA-Atlanta-DC'
    else:
        return 'Other'

def get_site_from_hostname(hostname):
    """Determine site based on hostname patterns"""
    if not hostname:
        return None
    
    hostname_lower = hostname.lower()
    if hostname_lower.startswith(('ala-', 'al-', 'ala')):
        return 'AZ-Alameda-DC'
    elif hostname_lower.startswith(('mdf-', 'n5k-', 'n7k-', '2960')):
        return 'AZ-Scottsdale-HQ-Corp'
    elif 'dtc_phx' in hostname_lower:
        return 'AZ-Scottsdale-HQ-Corp'
    
    return None

def get_comprehensive_inventory():
    """Get inventory from comprehensive_device_inventory table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    inventory = []
    
    try:
        cursor.execute("""
            SELECT hostname, ip_address, 
                   system_info->>'detected_model' as model,
                   system_info->>'serial_number' as serial_number,
                   system_info->>'software_version' as software_version,
                   system_info->>'system_uptime' as uptime_seconds,
                   physical_components,
                   summary->>'status' as status
            FROM comprehensive_device_inventory
            WHERE updated_at >= NOW() - INTERVAL '1 day'
            ORDER BY hostname
        """)
        
        for row in cursor.fetchall():
            hostname, ip, model, serial, sw_version, uptime, components, status = row
            
            device = {
                'hostname': hostname,
                'ip_address': ip,
                'model': model,
                'serial_number': serial,
                'software_version': sw_version,
                'uptime_seconds': uptime,
                'components': components,
                'status': status
            }
            
            inventory.append(device)
        
        logger.info(f"Retrieved {len(inventory)} devices from comprehensive inventory")
        
    except Exception as e:
        logger.error(f"Error retrieving inventory: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return inventory

def transform_to_web_format(inventory):
    """Transform comprehensive inventory to web format with parent hostname in all rows"""
    web_format = []
    row_order = 0
    
    for device in inventory:
        hostname = device['hostname']
        ip = device['ip_address']
        model = device['model']
        serial = device['serial_number']
        
        # Determine position based on device type and model
        position = 'Standalone'
        if 'stack' in device.get('device_type', '').lower():
            position = 'Master'
        elif '7K' in model or 'N7K' in model:
            position = 'Parent Switch'
        
        # Determine site
        site = get_site_from_hostname(hostname) or get_site_from_ip(ip)
        
        # Add main device row
        row_order += 1
        web_format.append({
            'hostname': hostname,
            'ip_address': ip,
            'position': position,
            'model': model,
            'serial_number': serial,
            'port_location': '',
            'vendor': 'Cisco',
            'notes': '',
            'parent_hostname': hostname,  # Parent is self for main device
            'relationship': position,
            'site': site,
            'row_order': row_order
        })
        
        # Process physical components (skip chassis since we already have main device)
        physical_components = device.get('components')
        if physical_components and isinstance(physical_components, dict):
            # Skip chassis components to avoid duplicates
            
            # Process modules
            if 'modules' in physical_components:
                for module in physical_components['modules']:
                    # Skip empty modules
                    if not module.get('model_name') or module.get('model_name', '').strip('\"') == '':
                        continue
                    row_order += 1
                    web_format.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'Module',
                        'model': module.get('model_name', '').strip('\"'),
                        'serial_number': module.get('serial_number', '').strip('\"'),
                        'port_location': module.get('description', ''),
                        'vendor': 'Cisco',
                        'notes': '',
                        'parent_hostname': hostname,
                        'relationship': 'Component',
                        'site': site,
                        'row_order': row_order
                    })
            
            # Process FEX units  
            if 'fex_units' in physical_components:
                for fex in physical_components['fex_units']:
                    row_order += 1
                    web_format.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': f'FEX-{fex.get("name", "")}',
                        'model': fex.get('model_name', ''),
                        'serial_number': fex.get('serial_number', ''),
                        'port_location': fex.get('description', ''),
                        'vendor': 'Cisco',
                        'notes': '',
                        'parent_hostname': hostname,
                        'relationship': 'Component',
                        'site': site,
                        'row_order': row_order
                    })
            
            # Process transceivers/SFPs
            if 'transceivers' in physical_components:
                for sfp in physical_components['transceivers']:
                    # Skip empty transceivers
                    if not sfp.get('model_name') or sfp.get('model_name', '').strip('\"') == '':
                        continue
                    row_order += 1
                    web_format.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'SFP',
                        'model': sfp.get('model_name', '').strip('\"'),
                        'serial_number': sfp.get('serial_number', '').strip('\"'),
                        'port_location': sfp.get('description', ''),
                        'vendor': 'Cisco',
                        'notes': '',
                        'parent_hostname': hostname,
                        'relationship': 'Component',
                        'site': site,
                        'row_order': row_order
                    })
        
        # Handle old component structures for backward compatibility    
        elif device.get('components'):
            # Handle different component structures
            if isinstance(device['components'], dict):
                # Skip chassis components to avoid duplicates - we already have the main device
                
                # Stack members
                if 'stack_members' in device['components']:
                    for member in device['components']['stack_members']:
                        if member.get('role') != 'Master':
                            row_order += 1
                            web_format.append({
                                'hostname': '',  # Empty for component
                                'ip_address': '',
                                'position': 'Slave',
                                'model': member.get('model', ''),
                                'serial_number': member.get('serial', ''),
                                'port_location': '',
                                'vendor': 'Cisco',
                                'notes': '',
                                'parent_hostname': hostname,  # Parent device name
                                'relationship': 'Slave',
                                'site': site,
                                'row_order': row_order
                            })
                
                # VDCs
                if 'vdcs' in device['components']:
                    # Skip VDCs but process their modules
                    pass
                
                # Modules
                if 'modules' in device['components']:
                    for module in device['components']['modules']:
                        row_order += 1
                        web_format.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Module',
                            'model': module.get('model', ''),
                            'serial_number': module.get('serial', ''),
                            'port_location': module.get('description', ''),
                            'vendor': 'Cisco',
                            'notes': '',
                            'parent_hostname': hostname,
                            'relationship': 'Component',
                            'site': site,
                            'row_order': row_order
                        })
                
                # FEX units
                if 'fex_units' in device['components']:
                    for fex in device['components']['fex_units']:
                        row_order += 1
                        fex_id = fex.get('fex_id', '')
                        web_format.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_id}',
                            'model': fex.get('model', ''),
                            'serial_number': fex.get('serial', ''),
                            'port_location': fex.get('description', ''),
                            'vendor': 'Cisco',
                            'notes': '',
                            'parent_hostname': hostname,
                            'relationship': 'Component',
                            'site': site,
                            'row_order': row_order
                        })
                
                # SFP/Transceivers
                if 'sfps' in device['components']:
                    for sfp in device['components']['sfps']:
                        row_order += 1
                        web_format.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'SFP',
                            'model': sfp.get('model', ''),
                            'serial_number': sfp.get('serial', ''),
                            'port_location': sfp.get('port', ''),
                            'vendor': sfp.get('vendor', 'Unknown'),
                            'notes': '',
                            'parent_hostname': hostname,
                            'relationship': 'Component',
                            'site': site,
                            'row_order': row_order
                        })
    
    logger.info(f"Transformed {len(inventory)} devices into {len(web_format)} components")
    return web_format

def update_database(web_format_data):
    """Update database with web format data including new fields"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Add new columns if they don't exist
        cursor.execute("""
            ALTER TABLE inventory_web_format 
            ADD COLUMN IF NOT EXISTS parent_hostname VARCHAR(255),
            ADD COLUMN IF NOT EXISTS relationship VARCHAR(50),
            ADD COLUMN IF NOT EXISTS row_order INTEGER,
            ADD COLUMN IF NOT EXISTS site VARCHAR(50)
        """)
        
        # Get EOL data from datacenter_inventory
        cursor.execute("""
            SELECT model, announcement_date, end_of_sale_date, end_of_support_date
            FROM datacenter_inventory
            WHERE end_of_support_date IS NOT NULL
        """)
        eol_data = {row[0]: {'announce': row[1], 'eos': row[2], 'eol': row[3]} 
                    for row in cursor.fetchall()}
        
        # Track existing serials
        cursor.execute("SELECT serial_number FROM inventory_web_format")
        existing_serials = set(row[0] for row in cursor.fetchall())
        
        logger.info(f"Found {len(existing_serials)} existing components in database")
        
        # Insert/update data
        new_count = 0
        update_count = 0
        
        for component in web_format_data:
            serial = component['serial_number']
            model_eol = eol_data.get(component['model'], {})
            
            if serial in existing_serials:
                # Update existing
                cursor.execute("""
                    UPDATE inventory_web_format
                    SET hostname = %s,
                        ip_address = %s,
                        position = %s,
                        model = %s,
                        port_location = %s,
                        vendor = %s,
                        notes = %s,
                        parent_hostname = %s,
                        relationship = %s,
                        site = %s,
                        row_order = %s,
                        announcement_date = %s,
                        end_of_sale = %s,
                        end_of_support = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE serial_number = %s
                """, (
                    component['hostname'],
                    component['ip_address'],
                    component['position'],
                    component['model'],
                    component['port_location'],
                    component['vendor'],
                    component['notes'],
                    component['parent_hostname'],
                    component['relationship'],
                    component['site'],
                    component['row_order'],
                    model_eol.get('announce'),
                    model_eol.get('eos'),
                    model_eol.get('eol'),
                    serial
                ))
                update_count += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO inventory_web_format 
                    (hostname, ip_address, position, model, serial_number, 
                     port_location, vendor, notes, parent_hostname, relationship,
                     site, row_order, announcement_date, end_of_sale, end_of_support)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    component['hostname'],
                    component['ip_address'],
                    component['position'],
                    component['model'],
                    serial,
                    component['port_location'],
                    component['vendor'],
                    component['notes'],
                    component['parent_hostname'],
                    component['relationship'],
                    component['site'],
                    component['row_order'],
                    model_eol.get('announce'),
                    model_eol.get('eos'),
                    model_eol.get('eol')
                ))
                new_count += 1
        
        conn.commit()
        logger.info(f"Database update complete: {new_count} new, {update_count} updated")
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Main execution function"""
    logger.info("Starting nightly inventory web format collection V2")
    
    # Get inventory from comprehensive table
    inventory = get_comprehensive_inventory()
    
    if not inventory:
        logger.warning("No inventory data retrieved")
        return
    
    # Transform to web format
    web_format_data = transform_to_web_format(inventory)
    
    # Save to temp JSON (optional)
    temp_file = f'/tmp/inventory_web_format_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(temp_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_components': len(web_format_data),
            'data': web_format_data
        }, f, indent=2)
    logger.info(f"Saved to temp file: {temp_file}")
    
    # Update database
    update_database(web_format_data)
    
    logger.info("Nightly inventory collection complete")

if __name__ == "__main__":
    main()