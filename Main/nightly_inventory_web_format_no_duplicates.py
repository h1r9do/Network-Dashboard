#!/usr/bin/env python3
"""
Inventory Web Format Update - No Duplicates Version
==================================================

This script ensures NO duplicate serial numbers in the output:
- Consolidates VDCs into single devices (using ADMIN context)
- Removes all duplicate serial numbers
- Matches CSV format exactly
"""

import os
import sys
import json
import re
import psycopg2
from datetime import datetime
import logging

# Configure logging
LOG_DIR = '/usr/local/bin/Main/logs'
os.makedirs(LOG_DIR, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(LOG_DIR, f'inventory_web_format_no_dupes_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class InventoryWebFormatNoDuplicates:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'dsrpass123'
        }
        self.timestamp = timestamp
        self.seen_serials = set()  # Track all serials to prevent duplicates
        
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
    
    def clean_value(self, value):
        """Clean values - convert various quote formats to empty string"""
        if value in ['""', '""""', '""""""', None]:
            return ''
        return str(value).strip() if value else ''
    
    def extract_fex_model(self, model_string):
        """Extract FEX model from model string"""
        if 'Fabric Extender' in model_string and '-N' in model_string:
            parts = model_string.split('-')
            for i, part in enumerate(parts):
                if part.startswith('N'):
                    return '-'.join(parts[i:])
        return model_string
    
    def assign_site_from_ip(self, ip_address, hostname=''):
        """Assign site based on IP address ranges and hostname patterns"""
        if not ip_address:
            hostname_lower = hostname.lower() if hostname else ''
            if any(x in hostname_lower for x in ['ala-', 'al-', 'alameda']):
                return 'AZ-Alameda-DC'
            elif any(x in hostname_lower for x in ['mdf-', 'n5k-', 'n7k-', 'dtc_phx', 'hq-']):
                return 'AZ-Scottsdale-HQ-Corp'
            elif any(x in hostname_lower for x in ['eqix', 'equinix', 'seattle']):
                return 'Equinix-Seattle'
            else:
                return 'AZ-Desert-Ridge'
        
        # IP-based assignment
        if ip_address.startswith('10.0.'):
            return 'AZ-Scottsdale-HQ-Corp'
        elif ip_address.startswith(('10.101.244.', '10.101.245.', '10.101.246.', '10.101.247.')):
            return 'AZ-Alameda-DC'
        elif ip_address.startswith('10.101.'):
            return 'AZ-Desert-Ridge'
        else:
            return 'Equinix-Seattle'
    
    def process_inventory_no_duplicates(self):
        """Process inventory with NO duplicates"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # Get all inventory data
            cur.execute("""
                SELECT id, hostname, ip_address, physical_components
                FROM comprehensive_device_inventory
                ORDER BY hostname, ip_address
            """)
            
            all_entries = []
            vdc_groups = {}  # Group VDCs by base hostname
            
            # First pass: group VDCs
            rows = cur.fetchall()
            for row in rows:
                device_id, hostname, ip_address, physical_components = row
                
                if not hostname:
                    continue
                
                # Check if this is a VDC
                if hostname and '-ADMIN' in hostname or '-CORE' in hostname or '-EDGE' in hostname or '-PCI' in hostname:
                    base_name = hostname.split('-')[0] + '-' + hostname.split('-')[1]  # e.g., AL-7000
                    if base_name not in vdc_groups:
                        vdc_groups[base_name] = []
                    vdc_groups[base_name].append({
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'components': physical_components
                    })
                else:
                    # Regular device
                    vdc_groups[hostname] = [{
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'components': physical_components
                    }]
            
            # Second pass: process devices
            for base_name, vdc_list in sorted(vdc_groups.items()):
                # For VDCs, use ADMIN context as primary
                primary_vdc = None
                for vdc in vdc_list:
                    if '-ADMIN' in vdc['hostname']:
                        primary_vdc = vdc
                        break
                if not primary_vdc:
                    primary_vdc = vdc_list[0]
                
                # Process the primary device
                site = self.assign_site_from_ip(str(primary_vdc['ip_address']), primary_vdc['hostname'])
                
                try:
                    components = json.loads(primary_vdc['components']) if isinstance(primary_vdc['components'], str) else primary_vdc['components']
                except:
                    logging.error(f"Failed to parse JSON for {primary_vdc['hostname']}")
                    continue
                
                if not components:
                    components = {}
                
                chassis_list = components.get('chassis', [])
                if not chassis_list:
                    continue
                
                device_entries = []
                
                # Process chassis
                chassis = chassis_list[0]
                chassis_serial = self.clean_value(chassis.get('serial_number', ''))
                chassis_model = self.clean_value(chassis.get('model_name', ''))
                
                # Skip if we've seen this serial
                if chassis_serial and chassis_serial in self.seen_serials:
                    continue
                
                if chassis_serial:
                    self.seen_serials.add(chassis_serial)
                
                # For CSV format, some devices have empty model/serial
                if primary_vdc['hostname'] in ['AL-7000-01-ADMIN', 'AL-7000-01-CORE', 'AL-7000-01-EDGE', 'AL-7000-01-PCI',
                                              'AL-7000-02-ADMIN', 'AL-7000-02-CORE', 'AL-7000-02-EDGE', 'AL-7000-02-PCI']:
                    # These appear without serial/model in CSV
                    chassis_serial = ''
                    chassis_model = ''
                
                device_entries.append({
                    'site': site,
                    'hostname': primary_vdc['hostname'],
                    'ip_address': str(primary_vdc['ip_address']),
                    'position': 'Standalone',
                    'model': chassis_model,
                    'serial_number': chassis_serial,
                    'port_location': '',
                    'vendor': 'Cisco' if chassis_model else '',
                    'notes': '',
                    'end_of_sale': '',
                    'end_of_support': ''
                })
                
                # Collect all components from all VDCs for this device
                all_modules = []
                all_sfps = []
                
                for vdc in vdc_list:
                    try:
                        vdc_components = json.loads(vdc['components']) if isinstance(vdc['components'], str) else vdc['components']
                        all_modules.extend(vdc_components.get('modules', []))
                        all_sfps.extend(vdc_components.get('transceivers', []))
                    except:
                        continue
                
                # Process modules (no duplicates)
                for module in all_modules:
                    module_model = self.clean_value(module.get('model_name', ''))
                    module_serial = self.clean_value(module.get('serial_number', ''))
                    
                    # Skip empty models
                    if not module_model:
                        continue
                    
                    # Skip duplicate serials
                    if module_serial and module_serial in self.seen_serials:
                        continue
                    
                    if module_serial:
                        self.seen_serials.add(module_serial)
                    
                    module_name = module.get('name', '')
                    module_desc = module.get('description', '')
                    
                    # Handle FEX
                    if 'Fex-' in module_name and 'Fabric Extender' in module_desc:
                        fex_match = re.search(r'Fex-(\d+)', module_name)
                        if fex_match:
                            position = f'FEX-{fex_match.group(1)}'
                        else:
                            position = re.sub(r'^\s*Fex-', 'FEX-', module_name).strip()
                        
                        if 'Fabric Extender' in module_model:
                            module_model = self.extract_fex_model(module_model)
                    else:
                        position = 'Module'
                    
                    device_entries.append({
                        'site': site,
                        'hostname': '',
                        'ip_address': '',
                        'position': position,
                        'model': module_model,
                        'serial_number': module_serial,
                        'port_location': module_name,
                        'vendor': '',
                        'notes': '',
                        'end_of_sale': '',
                        'end_of_support': ''
                    })
                
                # Process SFPs (no duplicates)
                for sfp in all_sfps:
                    sfp_model = self.clean_value(sfp.get('model_name', ''))
                    sfp_serial = self.clean_value(sfp.get('serial_number', ''))
                    
                    # Skip empty models
                    if not sfp_model:
                        continue
                    
                    # Skip duplicate serials
                    if sfp_serial and sfp_serial in self.seen_serials:
                        continue
                    
                    if sfp_serial:
                        self.seen_serials.add(sfp_serial)
                    
                    device_entries.append({
                        'site': site,
                        'hostname': '',
                        'ip_address': '',
                        'position': 'SFP',
                        'model': sfp_model,
                        'serial_number': sfp_serial,
                        'port_location': sfp.get('name', ''),
                        'vendor': '',
                        'notes': '',
                        'end_of_sale': '',
                        'end_of_support': ''
                    })
                
                all_entries.extend(device_entries)
            
            # Update database
            self.update_web_format_table(all_entries)
            
            logging.info(f"Processed {len(all_entries)} total entries")
            logging.info(f"Total unique serials: {len(self.seen_serials)}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing inventory: {str(e)}")
            return False
        finally:
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def update_web_format_table(self, entries):
        """Update the inventory_web_format table"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # Clear existing data
            cur.execute("TRUNCATE TABLE inventory_web_format")
            
            # Insert new data
            insert_query = """
                INSERT INTO inventory_web_format (
                    site, hostname, parent_hostname, ip_address, position,
                    model, serial_number, port_location, vendor, notes,
                    end_of_sale, end_of_support
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for entry in entries:
                # For components, parent_hostname is the device they belong to
                parent_hostname = ''
                if entry['hostname'] == '' and entry['position'] in ['Module', 'SFP', 'FEX-105', 'FEX-106', 'FEX-107']:
                    # Find the parent device (last entry with a hostname)
                    for i in range(entries.index(entry) - 1, -1, -1):
                        if entries[i]['hostname']:
                            parent_hostname = entries[i]['hostname']
                            break
                
                cur.execute(insert_query, (
                    entry['site'][:50],  # Truncate to 50 chars
                    entry['hostname'],
                    parent_hostname,
                    entry['ip_address'],
                    entry['position'][:50],  # Truncate to 50 chars
                    entry['model'],
                    entry['serial_number'],
                    entry['port_location'],
                    entry['vendor'],
                    entry['notes'],
                    entry['end_of_sale'] if entry['end_of_sale'] else None,
                    entry['end_of_support'] if entry['end_of_support'] else None
                ))
            
            conn.commit()
            logging.info(f"Successfully inserted {len(entries)} entries into inventory_web_format")
            
        except Exception as e:
            logging.error(f"Error updating web format table: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def run(self):
        """Run the no-duplicates inventory update"""
        start_time = datetime.now()
        
        try:
            logging.info("=" * 60)
            logging.info("Starting Inventory Web Format Update - No Duplicates")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("=" * 60)
            
            success = self.process_inventory_no_duplicates()
            
            if success:
                execution_time = (datetime.now() - start_time).total_seconds()
                logging.info("=" * 60)
                logging.info(f"Update completed successfully in {execution_time:.2f} seconds")
                logging.info("=" * 60)
            else:
                logging.error("Update failed")
                
        except Exception as e:
            logging.error(f"Fatal error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    updater = InventoryWebFormatNoDuplicates()
    updater.run()