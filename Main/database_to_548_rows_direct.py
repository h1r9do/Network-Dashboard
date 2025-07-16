#!/usr/bin/env python3
"""
Database to 548-Row Direct Processing Script
==========================================

This script replicates the exact filtering and restructuring logic that was used 
to create the JSON files from the database, then applies the 548-row processing
logic to produce the exact same output as the known good CSV.

Key Steps:
1. Read raw database (physical_components format)
2. Apply JSON creation filtering logic
3. Restructure data (FEX → chassis, etc.)
4. Apply 548-row filtering (10 SFP limit, VDC consolidation, etc.)
5. Generate final CSV matching known good output
"""

import os
import sys
import json
import csv
import re
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseTo548Processor:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX patterns (from complete_inventory_enhancement.py)
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
    
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
    
    def apply_device_filtering(self, raw_devices):
        """Apply the same device filtering that was used to create JSON files"""
        logging.info("Step 1: Apply Device Filtering (DB → JSON logic)")
        
        filtered_devices = []
        
        for hostname, ip_address, system_info, physical_components in raw_devices:
            # Skip devices without valid data
            if not physical_components or not system_info:
                continue
            
            # Parse JSON data
            system_info = json.loads(system_info) if isinstance(system_info, str) else system_info
            components = json.loads(physical_components) if isinstance(physical_components, str) else physical_components
            
            # Check for valid chassis with serial numbers (actual filtering logic)
            chassis_list = components.get('chassis', [])
            if not chassis_list:
                continue
            
            # Find the first chassis with valid serial (not just first chassis)
            valid_chassis = None
            for chassis in chassis_list:
                chassis_serial = chassis.get('serial_number', '').strip()
                if chassis_serial and chassis_serial not in ['', '""', '""""']:
                    valid_chassis = chassis
                    break
            
            # Skip devices without any valid chassis
            if not valid_chassis:
                continue
            
            # This matches the device filtering pattern from the original scripts
            filtered_devices.append({
                'hostname': hostname,
                'ip': ip_address,
                'system_info': system_info,
                'components': components
            })
        
        logging.info(f"Device filtering: {len(raw_devices)} → {len(filtered_devices)} devices")
        return filtered_devices
    
    def restructure_to_json_format(self, filtered_devices):
        """Restructure data from DB format to JSON format (FEX → chassis, etc.)"""
        logging.info("Step 2: Restructure to JSON Format")
        
        json_format_devices = []
        
        for device in filtered_devices:
            hostname = device['hostname']
            ip = device['ip']
            system_info = device['system_info']
            components = device['components']
            
            # Create JSON-style physical_inventory structure
            physical_inventory = {
                'chassis': [],
                'modules': [],
                'transceivers': []
            }
            
            # Add main chassis from physical_components (use only valid chassis)
            chassis_list = components.get('chassis', [])
            for chassis in chassis_list:
                chassis_serial = chassis.get('serial_number', '').strip()
                chassis_model = chassis.get('model_name', '').strip()
                
                # Only include chassis with valid serial and model
                if (chassis_serial and chassis_serial not in ['', '""', '""""'] and
                    chassis_model and chassis_model not in ['', '""', '""""']):
                    chassis_entry = {
                        'serial': chassis_serial,
                        'model': chassis_model,
                        'name': chassis.get('name', ''),
                        'description': chassis.get('description', '')
                    }
                    physical_inventory['chassis'].append(chassis_entry)
            
            # Process modules and convert FEX modules to chassis entries (KEY RESTRUCTURING)
            for module in components.get('modules', []):
                module_name = module.get('name', '')
                module_desc = module.get('description', '')
                module_model = module.get('model_name', '').strip()
                module_serial = module.get('serial_number', '').strip()
                
                # Skip modules with empty model names (this is the key filtering!)
                if not module_model or module_model in ['', '""', '""""', '""""""']:
                    continue
                
                # Skip modules with empty serials
                if not module_serial or module_serial in ['', '""', '""""', '""""""']:
                    continue
                
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
            
            # Add transceivers (keep as transceivers)
            for transceiver in components.get('transceivers', []):
                physical_inventory['transceivers'].append({
                    'serial': transceiver.get('serial_number', ''),
                    'model': transceiver.get('model_name', ''),
                    'name': transceiver.get('name', ''),
                    'description': transceiver.get('description', '')
                })
            
            # Create device entry in JSON format
            device_entry = {
                'hostname': hostname,
                'ip': str(ip),
                'physical_inventory': physical_inventory
            }
            
            # Detect VDC devices
            vdc_match = re.match(r'^(.*?-7\d{3}-\d{2})-(ADMIN|CORE|EDGE|PCI)(?:\..*)?$', hostname)
            if vdc_match:
                device_entry['vdc_info'] = {
                    'is_vdc': True,
                    'vdc_names': [vdc_match.group(2)]
                }
            
            json_format_devices.append(device_entry)
        
        logging.info(f"Restructured {len(json_format_devices)} devices to JSON format")
        return json_format_devices
    
    def extract_fex_model(self, description, current_model):
        """Extract FEX model from description (from complete_inventory_enhancement.py)"""
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
        """Identify SFP model and vendor (from complete_inventory_enhancement.py)"""
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
    
    def apply_548_row_processing(self, json_devices):
        """Apply the exact 548-row processing logic from generate_ultimate_final_csv.py"""
        logging.info("Step 3: Apply 548-Row Processing Logic")
        
        # Track seen serials globally like original
        seen_serials = set()
        csv_data = []
        
        for device in json_devices:
            hostname = device['hostname']
            ip = device['ip']
            physical_inv = device['physical_inventory']
            
            # Get VDC notes if applicable (from generate_ultimate_final_csv.py)
            notes = ""
            if device.get('vdc_info', {}).get('is_vdc'):
                vdc_list = device['vdc_info']['vdc_names']
                vdc_types = set()
                for vdc in vdc_list:
                    if 'ADMIN' in vdc:
                        vdc_types.add('ADMIN')
                    elif 'CORE' in vdc:
                        vdc_types.add('CORE')
                    elif 'EDGE' in vdc:
                        vdc_types.add('EDGE')
                    elif 'PCI' in vdc:
                        vdc_types.add('PCI')
                notes = f"VDCs: {', '.join(sorted(vdc_types))}"
            
            chassis_list = physical_inv.get('chassis', [])
            if not chassis_list:
                continue
            
            # Handle chassis (EXACT LOGIC from generate_ultimate_final_csv.py)
            if len(chassis_list) > 1 and ('N5K' in chassis_list[0].get('model', '') or 
                                          'N56' in chassis_list[0].get('model', '')):
                # N5K with FEX
                main_chassis = chassis_list[0]
                
                # Check for duplicate
                if main_chassis['serial'] in seen_serials:
                    continue
                seen_serials.add(main_chassis['serial'])
                
                csv_data.append({
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
                for i in range(1, len(chassis_list)):
                    fex = chassis_list[i]
                    
                    if fex['serial'] in seen_serials:
                        continue
                    seen_serials.add(fex['serial'])
                    
                    fex_id = re.search(r'Fex-(\d+)', fex['name'])
                    fex_num = fex_id.group(1) if fex_id else str(100 + i)
                    
                    # Enhance FEX model
                    original = fex['model']
                    enhanced = self.extract_fex_model(fex['description'], original)
                    
                    csv_data.append({
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
                
                if main_chassis['serial'] in seen_serials:
                    continue
                seen_serials.add(main_chassis['serial'])
                
                position = 'Master' if len(chassis_list) > 1 else 'Standalone'
                csv_data.append({
                    'hostname': hostname,
                    'ip_address': ip,
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
                    
                    if chassis['serial'] in seen_serials:
                        continue
                    seen_serials.add(chassis['serial'])
                    
                    csv_data.append({
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
                if module['serial'] in seen_serials:
                    continue
                seen_serials.add(module['serial'])
                
                # Check for FEX module
                model = module['model']
                if 'Fabric Extender' in module.get('description', ''):
                    enhanced = self.extract_fex_model(module['description'], model)
                    if enhanced != model:
                        model = enhanced
                
                csv_data.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': model,
                    'serial_number': module['serial'],
                    'port_location': module['name'],
                    'vendor': '',
                    'notes': ''
                })
            
            # SFPs (CRITICAL: Apply 10-per-device limit like original)
            sfp_count = 0
            for sfp in physical_inv.get('transceivers', []):
                if sfp_count >= 10:  # EXACT SAME LIMIT AS ORIGINAL
                    break
                
                if sfp['serial'] in seen_serials:
                    continue
                seen_serials.add(sfp['serial'])
                
                # Enhance SFP
                original = sfp.get('model', 'Unknown')
                enhanced, vendor = self.identify_sfp(
                    sfp.get('description', ''),
                    original,
                    sfp.get('serial', '')
                )
                
                csv_data.append({
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
        
        logging.info(f"Generated {len(csv_data)} rows with 548-row processing")
        return csv_data
    
    def run_complete_processing(self):
        """Run the complete database → 548 rows processing"""
        start_time = datetime.now()
        
        try:
            logging.info("="*60)
            logging.info("Starting Database → 548 Rows Processing")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("="*60)
            
            # Get raw data from database
            conn = self.connect_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT hostname, ip_address, system_info, physical_components
                FROM comprehensive_device_inventory
                WHERE physical_components IS NOT NULL
                ORDER BY hostname
            """)
            
            raw_devices = cursor.fetchall()
            cursor.close()
            conn.close()
            
            logging.info(f"Loaded {len(raw_devices)} devices from database")
            
            # Step 1: Apply device filtering (DB → JSON logic)
            filtered_devices = self.apply_device_filtering(raw_devices)
            
            # Step 2: Restructure to JSON format
            json_devices = self.restructure_to_json_format(filtered_devices)
            
            # Step 3: Apply 548-row processing
            csv_data = self.apply_548_row_processing(json_devices)
            
            # Step 4: Write output CSV
            output_file = f"/usr/local/bin/Main/database_to_548_rows_{self.timestamp}.csv"
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = [
                    'hostname', 'ip_address', 'position', 'model', 
                    'serial_number', 'port_location', 'vendor', 'notes'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logging.info("="*60)
            logging.info("Processing completed successfully!")
            logging.info(f"Output file: {output_file}")
            logging.info(f"Generated rows: {len(csv_data)}")
            logging.info(f"Execution time: {execution_time:.2f} seconds")
            logging.info("="*60)
            
            # Compare with known good file
            try:
                known_good_file = "/usr/local/bin/Main/inventory_ultimate_final.csv"
                with open(known_good_file, 'r') as f:
                    known_good_lines = len(f.readlines()) - 1  # Subtract header
                
                logging.info(f"Known good file rows: {known_good_lines}")
                logging.info(f"Generated file rows: {len(csv_data)}")
                
                if len(csv_data) == known_good_lines:
                    logging.info("✅ ROW COUNT MATCHES!")
                else:
                    logging.warning(f"⚠️ Row count difference: {len(csv_data)} vs {known_good_lines}")
                    
            except Exception as e:
                logging.warning(f"Could not compare with known good file: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Processing failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    processor = DatabaseTo548Processor()
    success = processor.run_complete_processing()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()