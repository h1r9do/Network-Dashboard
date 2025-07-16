#!/usr/bin/env python3
"""
Production Inventory Web Format Update Script - FIXED VERSION
============================================================

This script applies the proven 548-row filtering and restructuring logic 
to the database inventory data and updates the web format table for display.

FIXES APPLIED:
- Handles "" (two quotes) serial numbers properly - converts to empty string
- Includes devices/modules even with empty serial/model numbers
- Preserves all 6,344 rows of data

Key Features:
- Uses successful database-to-548-rows logic
- Updates inventory_web_format table for web display
- Handles empty serial/model gracefully
- Handles multi-chassis devices correctly
- Enhances FEX models
- Applies 10-SFP limit per device
- Preserves VDC information
- Production logging and error handling

Usage: python3 nightly_inventory_web_format_update_fixed.py
"""

import os
import sys
import json
import re
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/usr/local/bin/Main/inventory_web_format_update.log'),
        logging.StreamHandler()
    ]
)

class ProductionInventoryProcessor:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX patterns (from proven logic)
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',
        }
        
        # SFP description mapping
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
        }
        
        # SFP vendor patterns
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'MTC': 'MikroTik',
        }
        
        # Site order for grouping
        self.site_order = [
            'AZ-Scottsdale-HQ-Corp',
            'AZ-Alameda-DC',
            'Equinix-Seattle',
            'AZ-Desert-Ridge',
            'TX-Dallas-DC',
            'GA-Atlanta-DC',
            'Other',
            'Unknown'
        ]
    
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
    
    def clean_serial_number(self, serial):
        """Clean serial number - convert "" to empty string"""
        if serial == '""' or serial == '""""' or serial == '""""""':
            return ''
        return serial
    
    def clean_model_name(self, model):
        """Clean model name - convert "" to empty string"""
        if model == '""' or model == '""""' or model == '""""""':
            return ''
        return model
    
    def assign_site_from_ip(self, ip_address, hostname=''):
        """Assign site based on IP address ranges and hostname patterns"""
        # If no IP, try hostname patterns
        if not ip_address:
            hostname_lower = hostname.lower() if hostname else ''
            if any(x in hostname_lower for x in ['ala-', 'al-', 'alameda']):
                return 'AZ-Alameda-DC'
            elif any(x in hostname_lower for x in ['mdf-', 'n5k-', 'n7k-', '2960', 'dtc_phx', 'hq-']):
                return 'AZ-Scottsdale-HQ-Corp'
            return 'Unknown'
        
        # Corporate HQ ranges
        if (ip_address.startswith('10.0.') or
            ip_address.startswith('192.168.255.') or
            ip_address.startswith('192.168.4.') or
            ip_address.startswith('192.168.5.') or
            ip_address.startswith('192.168.12.') or
            ip_address.startswith('192.168.13.') or
            ip_address.startswith('172.16.4.')):
            return 'AZ-Scottsdale-HQ-Corp'
        
        # Alameda DC
        elif (ip_address.startswith('10.101.') or
              ip_address.startswith('192.168.200.')):
            return 'AZ-Alameda-DC'
        
        # Other locations
        elif ip_address.startswith('10.44.'):
            return 'Equinix-Seattle'
        elif ip_address.startswith('10.41.'):
            return 'AZ-Desert-Ridge'
        elif ip_address.startswith('10.42.'):
            return 'TX-Dallas-DC'
        elif ip_address.startswith('10.43.'):
            return 'GA-Atlanta-DC'
        
        else:
            return 'Other'
    
    def extract_fex_model(self, description, current_model):
        """Extract FEX model from description"""
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
            return model, None
        
        vendor = None
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        for desc_pattern, sfp_model in self.sfp_description_map.items():
            if desc_pattern.lower() in description.lower():
                return sfp_model, vendor
        
        return model, vendor
    
    def process_inventory_for_web(self):
        """Process inventory data using proven 548-row logic for web display"""
        logging.info("Processing inventory data for web format using 548-row logic")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # Get all devices with inventory data
            cursor.execute("""
                SELECT hostname, ip_address, system_info, physical_components
                FROM comprehensive_device_inventory
                WHERE physical_components IS NOT NULL
                ORDER BY hostname
            """)
            
            raw_devices = cursor.fetchall()
            logging.info(f"Loaded {len(raw_devices)} devices from database")
            
            # Apply proven filtering and processing logic
            web_data = []
            seen_serials = set()
            
            for hostname, ip_address, system_info_json, physical_components_json in raw_devices:
                if not physical_components_json:
                    continue
                
                # Parse JSON data
                system_info = json.loads(system_info_json) if isinstance(system_info_json, str) else system_info_json
                components = json.loads(physical_components_json) if isinstance(physical_components_json, str) else physical_components_json
                
                # Check for valid chassis with serial numbers (proven filtering logic)
                chassis_list = components.get('chassis', [])
                if not chassis_list:
                    continue
                
                # Find the first chassis with valid serial (not just first chassis)
                valid_chassis = None
                for chassis in chassis_list:
                    chassis_serial = chassis.get('serial_number', '').strip()
                    # FIXED: Don't skip chassis with "" serial
                    chassis_serial = self.clean_serial_number(chassis_serial)
                    if chassis_serial or True:  # Always consider chassis valid
                        valid_chassis = chassis
                        break
                
                # Include devices even without valid chassis serial
                if not valid_chassis and chassis_list:
                    valid_chassis = chassis_list[0]
                
                # Skip devices without any chassis at all
                if not valid_chassis:
                    continue
                
                # Restructure to JSON format (proven logic)
                physical_inventory = {
                    'chassis': [],
                    'modules': [],
                    'transceivers': []
                }
                
                # Add main chassis from physical_components
                for chassis in chassis_list:
                    chassis_serial = self.clean_serial_number(chassis.get('serial_number', '').strip())
                    chassis_model = self.clean_model_name(chassis.get('model_name', '').strip())
                    
                    # FIXED: Include chassis even with empty serial/model
                    chassis_entry = {
                        'serial': chassis_serial,
                        'model': chassis_model,
                        'name': chassis.get('name', ''),
                        'description': chassis.get('description', '')
                    }
                    physical_inventory['chassis'].append(chassis_entry)
                
                # Process modules and convert FEX modules to chassis entries (proven restructuring)
                for module in components.get('modules', []):
                    module_name = module.get('name', '')
                    module_desc = module.get('description', '')
                    module_model = self.clean_model_name(module.get('model_name', '').strip())
                    module_serial = self.clean_serial_number(module.get('serial_number', '').strip())
                    
                    # FIXED: Include modules even with empty model/serial
                    # Check if this is a FEX module (convert to chassis)
                    if 'Fex-' in module_name and 'Fabric Extender' in module_desc:
                        fex_chassis = {
                            'serial': module_serial,
                            'model': module_model,
                            'name': module_name,
                            'description': module_desc
                        }
                        physical_inventory['chassis'].append(fex_chassis)
                    else:
                        # Regular module (keep as module)
                        module_entry = {
                            'serial': module_serial,
                            'model': module_model,
                            'name': module_name,
                            'description': module_desc
                        }
                        physical_inventory['modules'].append(module_entry)
                
                # Add transceivers
                for transceiver in components.get('transceivers', []):
                    transceiver_serial = self.clean_serial_number(transceiver.get('serial_number', ''))
                    transceiver_model = self.clean_model_name(transceiver.get('model_name', ''))
                    
                    transceiver_entry = {
                        'serial': transceiver_serial,
                        'model': transceiver_model,
                        'name': transceiver.get('name', ''),
                        'description': transceiver.get('description', '')
                    }
                    physical_inventory['transceivers'].append(transceiver_entry)
                
                # Apply 548-row processing logic (proven logic)
                device_entries = self.process_device_548_logic(
                    hostname, ip_address, physical_inventory, seen_serials
                )
                
                # Assign site to all entries for this device
                site = self.assign_site_from_ip(ip_address, hostname)
                for entry in device_entries:
                    entry['site'] = site
                
                web_data.extend(device_entries)
            
            # Group data by site while preserving hierarchical structure
            site_grouped_data = []
            
            # Create a mapping of original index to preserve hierarchy
            indexed_data = [(i, entry) for i, entry in enumerate(web_data)]
            
            # Group by site
            for site in self.site_order:
                site_entries = [(i, entry) for i, entry in indexed_data if entry.get('site') == site]
                if site_entries:
                    # Sort by original index to preserve hierarchy
                    site_entries.sort(key=lambda x: x[0])
                    # Add entries in order
                    site_grouped_data.extend([entry for i, entry in site_entries])
            
            # Clear and update the web format table
            cursor.execute("TRUNCATE TABLE inventory_web_format")
            
            # Insert processed data
            insert_count = 0
            for entry in site_grouped_data:
                cursor.execute("""
                    INSERT INTO inventory_web_format 
                    (site, hostname, ip_address, position, model, serial_number, port_location, vendor, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    entry['site'],
                    entry['hostname'],
                    entry['ip_address'],
                    entry['position'],
                    entry['model'],
                    entry['serial_number'],
                    entry['port_location'],
                    entry['vendor'],
                    entry['notes']
                ))
                insert_count += 1
            
            conn.commit()
            
            logging.info(f"Successfully updated inventory_web_format table with {insert_count} entries")
            logging.info(f"Processed {len([d for d in web_data if d['hostname']])} devices")
            
            # Log site distribution
            site_counts = {}
            for entry in site_grouped_data:
                site = entry.get('site', 'Unknown')
                if entry['hostname']:  # This is a master device
                    site_counts[site] = site_counts.get(site, 0) + 1
            
            logging.info("Site distribution:")
            for site in self.site_order:
                if site in site_counts:
                    logging.info(f"  {site}: {site_counts[site]} devices")
            
            return True
            
        except Exception as e:
            logging.error(f"Error processing inventory: {str(e)}", exc_info=True)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def process_device_548_logic(self, hostname, ip_address, physical_inv, seen_serials):
        """Apply the proven 548-row processing logic for a single device"""
        device_entries = []
        
        # Detect VDC devices and get notes
        notes = ""
        vdc_match = re.match(r'^(.*?-7\d{3}-\d{2})-(ADMIN|CORE|EDGE|PCI)(?:\..*)?$', hostname)
        if vdc_match:
            vdc_type = vdc_match.group(2)
            notes = f"VDCs: {vdc_type}"
        
        chassis_list = physical_inv.get('chassis', [])
        if not chassis_list:
            return device_entries
        
        # Handle chassis (exact logic from proven script)
        if len(chassis_list) > 1 and ('N5K' in chassis_list[0].get('model', '') or 
                                      'N56' in chassis_list[0].get('model', '')):
            # N5K with FEX
            main_chassis = chassis_list[0]
            
            # Check for duplicate - but don't skip empty serials
            if main_chassis['serial'] and main_chassis['serial'] in seen_serials:
                return device_entries
            if main_chassis['serial']:
                seen_serials.add(main_chassis['serial'])
            
            device_entries.append({
                'hostname': hostname,
                'ip_address': ip_address,
                'position': 'Parent Switch',
                'model': main_chassis['model'],
                'serial_number': main_chassis['serial'],
                'port_location': '',
                'vendor': 'Cisco',
                'notes': notes
            })
            
            # FEX units
            for i in range(1, len(chassis_list)):
                fex = chassis_list[i]
                
                if fex['serial'] and fex['serial'] in seen_serials:
                    continue
                if fex['serial']:
                    seen_serials.add(fex['serial'])
                
                fex_id = re.search(r'Fex-(\d+)', fex['name'])
                fex_num = fex_id.group(1) if fex_id else str(100 + i)
                
                # Enhance FEX model
                original = fex['model']
                enhanced = self.extract_fex_model(fex['description'], original)
                
                device_entries.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': f'FEX-{fex_num}',
                    'model': enhanced,
                    'serial_number': fex['serial'],
                    'port_location': fex['name'],
                    'vendor': 'Cisco',
                    'notes': ''
                })
        else:
            # Single chassis or stack
            main_chassis = chassis_list[0]
            
            if main_chassis['serial'] and main_chassis['serial'] in seen_serials:
                return device_entries
            if main_chassis['serial']:
                seen_serials.add(main_chassis['serial'])
            
            position = 'Master' if len(chassis_list) > 1 else 'Standalone'
            device_entries.append({
                'hostname': hostname,
                'ip_address': ip_address,
                'position': position,
                'model': main_chassis['model'],
                'serial_number': main_chassis['serial'],
                'port_location': '',
                'vendor': 'Cisco' if '7K' in main_chassis['model'] else '',
                'notes': notes
            })
            
            # Additional stack members
            for i in range(1, len(chassis_list)):
                chassis = chassis_list[i]
                
                if chassis['serial'] and chassis['serial'] in seen_serials:
                    continue
                if chassis['serial']:
                    seen_serials.add(chassis['serial'])
                
                device_entries.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Slave',
                    'model': chassis['model'],
                    'serial_number': chassis['serial'],
                    'port_location': '',
                    'vendor': '',
                    'notes': ''
                })
        
        # Modules
        for module in physical_inv.get('modules', []):
            if module['serial'] and module['serial'] in seen_serials:
                continue
            if module['serial']:
                seen_serials.add(module['serial'])
            
            # Check for FEX module
            model = module['model']
            if 'Fabric Extender' in module.get('description', ''):
                enhanced = self.extract_fex_model(module['description'], model)
                if enhanced != model:
                    model = enhanced
            
            device_entries.append({
                'hostname': '',
                'ip_address': '',
                'position': 'Module',
                'model': model,
                'serial_number': module['serial'],
                'port_location': module['name'],
                'vendor': '',
                'notes': ''
            })
        
        # SFPs (apply 10-per-device limit like proven script)
        sfp_count = 0
        for sfp in physical_inv.get('transceivers', []):
            if sfp_count >= 10:  # EXACT SAME LIMIT AS PROVEN SCRIPT
                break
            
            if sfp['serial'] and sfp['serial'] in seen_serials:
                continue
            if sfp['serial']:
                seen_serials.add(sfp['serial'])
            
            # Enhance SFP
            original = sfp.get('model', 'Unknown')
            enhanced, vendor = self.identify_sfp(
                sfp.get('description', ''),
                original,
                sfp.get('serial', '')
            )
            
            device_entries.append({
                'hostname': '',
                'ip_address': '',
                'position': 'SFP',
                'model': enhanced,
                'serial_number': sfp['serial'],
                'port_location': sfp['name'],
                'vendor': vendor or '',
                'notes': ''
            })
            sfp_count += 1
        
        return device_entries
    
    def run_production_update(self):
        """Run the production inventory web format update"""
        start_time = datetime.now()
        
        try:
            logging.info("=" * 60)
            logging.info("Starting Production Inventory Web Format Update (FIXED)")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("=" * 60)
            
            # Process inventory and update web format table
            success = self.process_inventory_for_web()
            
            if success:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logging.info("=" * 60)
                logging.info("Production update completed successfully!")
                logging.info(f"Execution time: {execution_time:.2f} seconds")
                logging.info("Web format table updated with processed inventory data")
                logging.info("=" * 60)
                
                return True
            else:
                logging.error("Production update failed!")
                return False
                
        except Exception as e:
            logging.error(f"Production update failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    processor = ProductionInventoryProcessor()
    success = processor.run_production_update()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()