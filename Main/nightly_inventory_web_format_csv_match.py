#!/usr/bin/env python3
"""
Inventory Web Format Update - CSV Match Version
==============================================

This script formats the inventory data to match EXACTLY the CSV format:
- Master/Standalone devices show hostname and IP
- Child components (Slave/Module/SFP) have empty hostname and IP
- NO SFP limits - shows ALL components
- Maintains hierarchical parent-child structure

The web display will look exactly like:
site    hostname    ip_address    position    model    serial_number
AZ-Scottsdale-HQ-Corp    MDF-3130-I9-StackA    10.0.255.51    Master    WS-CBS3130X-S-F    FOC1217H0FC
AZ-Scottsdale-HQ-Corp            Slave    WS-CBS3130X-S    FOC1414H06C
AZ-Scottsdale-HQ-Corp            Module    800-27645-01    FDO12120A23
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
log_file = os.path.join(LOG_DIR, f'inventory_web_format_csv_match_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class InventoryWebFormatCSVMatch:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'network_inventory',
            'user': 'postgres',
            'password': 'postgres'
        }
        self.timestamp = timestamp
        
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
    
    def clean_value(self, value):
        """Clean values - convert various quote formats to empty string"""
        if value in ['""', '""""', '""""""', None]:
            return ''
        return str(value).strip() if value else ''
    
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
    
    def process_inventory_csv_format(self):
        """Process inventory to match CSV format exactly"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # Get all inventory data
            cur.execute("""
                SELECT device_id, hostname, ip_address, device_data
                FROM comprehensive_device_inventory
                ORDER BY hostname, ip_address
            """)
            
            all_entries = []
            
            for row in cur.fetchall():
                device_id, hostname, ip_address, device_data = row
                
                if not hostname:
                    continue
                
                # Assign site
                site = self.assign_site_from_ip(ip_address, hostname)
                
                # Parse device data
                try:
                    data = json.loads(device_data) if isinstance(device_data, str) else device_data
                except:
                    logging.error(f"Failed to parse JSON for {hostname}")
                    continue
                
                components = data.get('physical_components', {})
                chassis_list = components.get('chassis', [])
                
                if not chassis_list:
                    continue
                
                # Process based on device type
                device_entries = []
                
                # Check if this is a stack (multiple chassis)
                if len(chassis_list) > 1:
                    # Stack configuration
                    # First chassis is Master with hostname and IP
                    master = chassis_list[0]
                    device_entries.append({
                        'site': site,
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'position': 'Master',
                        'model': self.clean_value(master.get('model_name', '')),
                        'serial_number': self.clean_value(master.get('serial_number', '')),
                        'port_location': '',
                        'vendor': 'Cisco',
                        'notes': '',
                        'end_of_sale': '',
                        'end_of_support': ''
                    })
                    
                    # Additional chassis are Slaves with empty hostname/IP
                    for chassis in chassis_list[1:]:
                        device_entries.append({
                            'site': site,
                            'hostname': '',  # Empty for slaves
                            'ip_address': '',  # Empty for slaves
                            'position': 'Slave',
                            'model': self.clean_value(chassis.get('model_name', '')),
                            'serial_number': self.clean_value(chassis.get('serial_number', '')),
                            'port_location': '',
                            'vendor': '',
                            'notes': '',
                            'end_of_sale': '',
                            'end_of_support': ''
                        })
                else:
                    # Single device - Standalone
                    chassis = chassis_list[0]
                    device_entries.append({
                        'site': site,
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'position': 'Standalone',
                        'model': self.clean_value(chassis.get('model_name', '')),
                        'serial_number': self.clean_value(chassis.get('serial_number', '')),
                        'port_location': '',
                        'vendor': 'Cisco',
                        'notes': '',
                        'end_of_sale': '',
                        'end_of_support': ''
                    })
                
                # Add ALL modules with empty hostname/IP
                for module in components.get('modules', []):
                    # Check if this is a FEX
                    module_name = module.get('name', '')
                    if 'Fex-' in module_name and 'Fabric Extender' in module.get('description', ''):
                        position = re.sub(r'^\s*Fex-', 'FEX-', module_name).strip()
                    else:
                        position = 'Module'
                    
                    device_entries.append({
                        'site': site,
                        'hostname': '',  # Empty for modules
                        'ip_address': '',  # Empty for modules
                        'position': position,
                        'model': self.clean_value(module.get('model_name', '')),
                        'serial_number': self.clean_value(module.get('serial_number', '')),
                        'port_location': module_name,
                        'vendor': '',
                        'notes': '',
                        'end_of_sale': '',
                        'end_of_support': ''
                    })
                
                # Add ALL SFPs with empty hostname/IP - NO LIMIT!
                for sfp in components.get('transceivers', []):
                    device_entries.append({
                        'site': site,
                        'hostname': '',  # Empty for SFPs
                        'ip_address': '',  # Empty for SFPs
                        'position': 'SFP',
                        'model': self.clean_value(sfp.get('model_name', '')),
                        'serial_number': self.clean_value(sfp.get('serial_number', '')),
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
            return True
            
        except Exception as e:
            logging.error(f"Error processing inventory: {str(e)}")
            return False
        finally:
            if cur:
                cur.close()
            if conn:
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
                if entry['hostname'] == '' and entry['position'] in ['Slave', 'Module', 'SFP', 'FEX-105', 'FEX-106', 'FEX-107']:
                    # Find the parent device (last entry with a hostname)
                    for i in range(entries.index(entry) - 1, -1, -1):
                        if entries[i]['hostname']:
                            parent_hostname = entries[i]['hostname']
                            break
                
                cur.execute(insert_query, (
                    entry['site'],
                    entry['hostname'],
                    parent_hostname,
                    entry['ip_address'],
                    entry['position'],
                    entry['model'],
                    entry['serial_number'],
                    entry['port_location'],
                    entry['vendor'],
                    entry['notes'],
                    entry['end_of_sale'],
                    entry['end_of_support']
                ))
            
            conn.commit()
            logging.info(f"Successfully inserted {len(entries)} entries into inventory_web_format")
            
        except Exception as e:
            logging.error(f"Error updating web format table: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    def run(self):
        """Run the CSV format matching update"""
        start_time = datetime.now()
        
        try:
            logging.info("=" * 60)
            logging.info("Starting Inventory Web Format Update - CSV Match Version")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("=" * 60)
            
            success = self.process_inventory_csv_format()
            
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
    updater = InventoryWebFormatCSVMatch()
    updater.run()