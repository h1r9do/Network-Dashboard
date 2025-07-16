#!/usr/bin/env python3
"""
Modified Nightly SNMP Inventory Collection for Web Format
- Collects inventory via SNMP
- Processes and enhances data (VDC consolidation, FEX/SFP identification)
- Writes to temporary JSON file
- Updates database with clean structure matching CSV format
"""
import json
import psycopg2
from datetime import datetime
import os
import sys
import logging
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

class InventoryEnhancer:
    """Handles all inventory enhancements"""
    
    def __init__(self):
        # FEX patterns for model identification
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',
        }
        
        # SFP mappings
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
        }
        
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'MTC': 'MikroTik',
        }
    
    def extract_fex_model(self, description, current_model):
        """Extract proper FEX model from description"""
        if '-N2K-' in current_model:
            match = re.search(r'(N2K-[A-Z0-9\-]+)', current_model)
            if match:
                return match.group(1)
        
        full_text = f"{description} {current_model}"
        
        for pattern, model in self.fex_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        if 'Nexus2232' in description:
            return 'N2K-C2232PP-10GE'
        elif 'Nexus2248' in description:
            return 'N2K-C2248TP-1GE'
        elif 'Nexus2200DELL' in description:
            return 'N2K-B22DELL-P'
        
        return current_model
    
    def identify_sfp(self, description, model, serial):
        """Identify SFP model and vendor"""
        if model and model not in ['Unspecified', '""', '']:
            identified_model = model
        else:
            identified_model = 'Unknown'
            
            for desc_pattern, sfp_model in self.sfp_description_map.items():
                if desc_pattern.lower() in description.lower():
                    identified_model = sfp_model
                    break
        
        vendor = None
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        return identified_model, vendor

def collect_inventory_from_database():
    """Collect inventory from comprehensive_device_inventory table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    inventory_data = []
    
    try:
        cursor.execute("""
            SELECT 
                hostname, 
                ip_address, 
                collection_timestamp,
                physical_components,
                summary
            FROM comprehensive_device_inventory
            ORDER BY hostname
        """)
        
        for row in cursor.fetchall():
            hostname, ip, timestamp, components, summary = row
            inventory_data.append({
                'hostname': hostname,
                'ip_address': str(ip),
                'collection_timestamp': timestamp.isoformat() if timestamp else None,
                'physical_components': components or {},
                'summary': summary or {}
            })
        
        logger.info(f"Collected {len(inventory_data)} devices from database")
        
    except Exception as e:
        logger.error(f"Error collecting inventory: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return inventory_data

def consolidate_vdcs(inventory_data):
    """Consolidate Nexus 7K VDCs into single device entries"""
    vdc_groups = defaultdict(list)
    non_vdc_devices = []
    
    for device in inventory_data:
        hostname = device['hostname']
        
        # Check if it's a VDC
        if '-VDC' in hostname or '_VDC' in hostname:
            # Extract base hostname
            base_name = re.sub(r'[-_]VDC\d*[-_]?\w*', '', hostname)
            vdc_groups[base_name].append(device)
        else:
            non_vdc_devices.append(device)
    
    # Consolidate VDCs
    consolidated_devices = []
    
    for base_name, vdc_list in vdc_groups.items():
        # Take the first VDC as the primary
        primary = vdc_list[0]
        
        # Extract VDC names for notes
        vdc_names = [dev['hostname'] for dev in vdc_list]
        vdc_types = set()
        for name in vdc_names:
            if '-ADMIN' in name:
                vdc_types.add('ADMIN')
            elif '-CORE' in name:
                vdc_types.add('CORE')
            elif '-EDGE' in name:
                vdc_types.add('EDGE')
            elif '-PCI' in name:
                vdc_types.add('PCI')
        
        # Update the primary device
        primary['hostname'] = base_name
        primary['vdc_info'] = {
            'is_vdc': True,
            'vdc_names': vdc_names,
            'vdc_types': sorted(vdc_types)
        }
        
        consolidated_devices.append(primary)
    
    # Add non-VDC devices
    consolidated_devices.extend(non_vdc_devices)
    
    logger.info(f"Consolidated {len(inventory_data)} devices to {len(consolidated_devices)} devices")
    
    return consolidated_devices

def transform_to_web_format(inventory_data):
    """Transform inventory data to web format matching CSV structure"""
    enhancer = InventoryEnhancer()
    web_format_data = []
    seen_serials = set()
    
    for device in inventory_data:
        hostname = device['hostname']
        ip = device['ip_address']
        components = device.get('physical_components', {})
        
        # Get VDC notes if applicable
        notes = ""
        if device.get('vdc_info', {}).get('is_vdc'):
            vdc_types = device['vdc_info']['vdc_types']
            notes = f"VDCs: {', '.join(vdc_types)}"
        
        # Process chassis
        chassis_list = components.get('chassis', [])
        if not chassis_list:
            continue
        
        # Clean chassis data
        clean_chassis = []
        for chassis in chassis_list:
            model = chassis.get('model_name', '').strip()
            serial = chassis.get('serial_number', '').strip()
            
            if model and model != '""' and serial and serial != '""':
                clean_chassis.append({
                    'model': model,
                    'serial': serial,
                    'name': chassis.get('name', ''),
                    'description': chassis.get('description', '')
                })
        
        if not clean_chassis:
            continue
        
        # Determine device type and position
        if len(clean_chassis) > 1:
            first_model = clean_chassis[0]['model']
            if 'N5K' in first_model or 'N56' in first_model:
                # N5K with FEX
                main_chassis = clean_chassis[0]
                if main_chassis['serial'] not in seen_serials:
                    seen_serials.add(main_chassis['serial'])
                    web_format_data.append({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Parent Switch',
                        'model': main_chassis['model'],
                        'serial_number': main_chassis['serial'],
                        'port_location': '',
                        'vendor': 'Cisco',
                        'notes': notes
                    })
                
                # FEX units
                for i, fex in enumerate(clean_chassis[1:], 1):
                    if fex['serial'] not in seen_serials:
                        seen_serials.add(fex['serial'])
                        
                        # Extract FEX number
                        fex_num = str(100 + i)
                        if 'Fex-' in fex.get('name', ''):
                            match = re.search(r'Fex-(\d+)', fex['name'])
                            if match:
                                fex_num = match.group(1)
                        
                        # Enhance FEX model
                        enhanced_model = enhancer.extract_fex_model(
                            fex.get('description', ''), 
                            fex['model']
                        )
                        
                        web_format_data.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': enhanced_model,
                            'serial_number': fex['serial'],
                            'port_location': fex.get('name', ''),
                            'vendor': 'Cisco',
                            'notes': ''
                        })
            else:
                # Regular stack
                # Master
                main_chassis = clean_chassis[0]
                if main_chassis['serial'] not in seen_serials:
                    seen_serials.add(main_chassis['serial'])
                    web_format_data.append({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Master',
                        'model': main_chassis['model'],
                        'serial_number': main_chassis['serial'],
                        'port_location': '',
                        'vendor': 'Cisco' if '7K' in main_chassis['model'] else '',
                        'notes': notes
                    })
                
                # Slaves
                for chassis in clean_chassis[1:]:
                    if chassis['serial'] not in seen_serials:
                        seen_serials.add(chassis['serial'])
                        web_format_data.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Slave',
                            'model': chassis['model'],
                            'serial_number': chassis['serial'],
                            'port_location': '',
                            'vendor': '',
                            'notes': ''
                        })
        else:
            # Single device
            main_chassis = clean_chassis[0]
            if main_chassis['serial'] not in seen_serials:
                seen_serials.add(main_chassis['serial'])
                web_format_data.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Standalone',
                    'model': main_chassis['model'],
                    'serial_number': main_chassis['serial'],
                    'port_location': '',
                    'vendor': '',
                    'notes': notes
                })
        
        # Process modules (limit to significant ones)
        modules = components.get('modules', [])
        module_count = 0
        for module in modules:
            model = module.get('model_name', '').strip()
            serial = module.get('serial_number', '').strip()
            
            if not model or model == '""' or not serial or serial == '""':
                continue
            
            if serial in seen_serials:
                continue
            
            if module_count < 20:  # Limit per device
                seen_serials.add(serial)
                
                # Check if it's a FEX module
                if 'Fabric Extender' in module.get('description', ''):
                    model = enhancer.extract_fex_model(
                        module.get('description', ''), 
                        model
                    )
                
                web_format_data.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': model,
                    'serial_number': serial,
                    'port_location': module.get('name', ''),
                    'vendor': '',
                    'notes': ''
                })
                module_count += 1
        
        # Process SFPs (sample only)
        transceivers = components.get('transceivers', [])
        sfp_count = 0
        for sfp in transceivers:
            serial = sfp.get('serial_number', '').strip()
            
            if not serial or serial == '""' or serial in seen_serials:
                continue
            
            if sfp_count < 10:  # Limit per device
                seen_serials.add(serial)
                
                # Enhance SFP identification
                model, vendor = enhancer.identify_sfp(
                    sfp.get('description', ''),
                    sfp.get('model_name', ''),
                    serial
                )
                
                web_format_data.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': model,
                    'serial_number': serial,
                    'port_location': sfp.get('name', ''),
                    'vendor': vendor or '',
                    'notes': ''
                })
                sfp_count += 1
    
    logger.info(f"Transformed to {len(web_format_data)} components")
    
    return web_format_data

def save_to_temp_json(data):
    """Save data to temporary JSON file"""
    temp_file = f'/tmp/inventory_web_format_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(temp_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_components': len(data),
            'data': data
        }, f, indent=2)
    
    logger.info(f"Saved {len(data)} components to {temp_file}")
    
    return temp_file

def update_database(web_format_data):
    """Update database with web format data"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_web_format (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255),
                ip_address VARCHAR(45),
                position VARCHAR(50),
                model VARCHAR(255),
                serial_number VARCHAR(255) UNIQUE,
                port_location VARCHAR(255),
                vendor VARCHAR(100),
                notes TEXT,
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_web_serial 
            ON inventory_web_format(serial_number)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_web_hostname 
            ON inventory_web_format(hostname)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_web_model 
            ON inventory_web_format(model)
        """)
        
        # Track existing serials
        cursor.execute("SELECT serial_number FROM inventory_web_format")
        existing_serials = set(row[0] for row in cursor.fetchall())
        
        logger.info(f"Found {len(existing_serials)} existing components in database")
        
        # Insert/update data
        new_count = 0
        update_count = 0
        
        for component in web_format_data:
            serial = component['serial_number']
            
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
                    serial
                ))
                update_count += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO inventory_web_format 
                    (hostname, ip_address, position, model, serial_number, 
                     port_location, vendor, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    component['hostname'],
                    component['ip_address'],
                    component['position'],
                    component['model'],
                    serial,
                    component['port_location'],
                    component['vendor'],
                    component['notes']
                ))
                new_count += 1
        
        # Update EOL data from datacenter_inventory
        cursor.execute("""
            UPDATE inventory_web_format iwf
            SET 
                announcement_date = di.announcement_date,
                end_of_sale = di.end_of_sale_date,
                end_of_support = di.end_of_support_date
            FROM datacenter_inventory di
            WHERE iwf.serial_number = di.serial_number
            AND di.end_of_support_date IS NOT NULL
        """)
        
        eol_updated = cursor.rowcount
        
        # Update EOL data by model from meraki_eol_list (if table exists)
        try:
            cursor.execute("""
                UPDATE inventory_web_format iwf
                SET 
                    announcement_date = mel.announcement_date,
                    end_of_sale = mel.end_of_sale,
                    end_of_support = mel.end_of_support
                FROM meraki_eol_list mel
                WHERE iwf.model = mel.model
                AND iwf.end_of_support IS NULL
                AND mel.end_of_support IS NOT NULL
            """)
            
            eol_model_updated = cursor.rowcount
        except psycopg2.errors.UndefinedTable:
            logger.info("meraki_eol_list table not found, skipping model-based EOL update")
            eol_model_updated = 0
        
        conn.commit()
        
        logger.info(f"Database update complete:")
        logger.info(f"  - New components: {new_count}")
        logger.info(f"  - Updated components: {update_count}")
        logger.info(f"  - EOL data updated (by serial): {eol_updated}")
        logger.info(f"  - EOL data updated (by model): {eol_model_updated}")
        
        # Show summary
        cursor.execute("""
            SELECT position, COUNT(*) 
            FROM inventory_web_format 
            GROUP BY position 
            ORDER BY position
        """)
        
        print("\nInventory summary by position:")
        for position, count in cursor.fetchall():
            print(f"  {position}: {count}")
        
    except Exception as e:
        logger.error(f"Database update error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main execution function"""
    logger.info("=== Starting Nightly SNMP Inventory Web Format Update ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Collect inventory from database
        inventory_data = collect_inventory_from_database()
        
        if not inventory_data:
            logger.warning("No inventory data found in database")
            return
        
        # Step 2: Consolidate VDCs
        consolidated_data = consolidate_vdcs(inventory_data)
        
        # Step 3: Transform to web format
        web_format_data = transform_to_web_format(consolidated_data)
        
        # Step 4: Save to temporary JSON
        temp_file = save_to_temp_json(web_format_data)
        
        # Step 5: Update database
        update_database(web_format_data)
        
        # Clean up old temp files (keep last 7 days)
        import glob
        old_files = glob.glob('/tmp/inventory_web_format_*.json')
        for old_file in old_files:
            try:
                file_time = os.path.getmtime(old_file)
                if (datetime.now().timestamp() - file_time) > (7 * 24 * 60 * 60):
                    os.remove(old_file)
                    logger.info(f"Removed old temp file: {old_file}")
            except:
                pass
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"=== Completed in {duration:.2f} seconds ===")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()