#!/usr/bin/env python3
"""
Direct Database to CSV Test Script
=================================

This script directly processes the database inventory data and applies the same
filtering logic as the original scripts to produce the 548-row output.

Instead of converting to JSON format, it works directly with the database structure.
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

class DirectDatabaseProcessor:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX patterns from original scripts
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
    
    def extract_fex_model(self, description, current_model):
        """Extract FEX model from description"""
        # First check if model already contains the FEX model
        if '-N2K-' in current_model:
            match = re.search(r'(N2K-[A-Z0-9\-]+)', current_model)
            if match:
                return match.group(1)
        
        # Check description for FEX patterns
        full_text = f"{description} {current_model}"
        
        for pattern, model in self.fex_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        # Specific checks for Nexus models
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
    
    def process_database_inventory(self):
        """Process inventory directly from database with original filtering logic"""
        logging.info("Processing inventory directly from database")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # Get device count
            cursor.execute("SELECT COUNT(*) FROM comprehensive_device_inventory WHERE physical_components IS NOT NULL")
            count = cursor.fetchone()[0]
            logging.info(f"Found {count} devices with physical components")
            
            # Export data
            query = """
            SELECT hostname, ip_address, system_info, physical_components
            FROM comprehensive_device_inventory
            WHERE physical_components IS NOT NULL
            ORDER BY hostname
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Track seen serials globally like original
            seen_serials = set()
            csv_data = []
            
            for hostname, ip_address, system_info_json, physical_components_json in rows:
                if not physical_components_json:
                    continue
                
                # Parse JSON data
                system_info = json.loads(system_info_json) if isinstance(system_info_json, str) else system_info_json
                components = json.loads(physical_components_json) if isinstance(physical_components_json, str) else physical_components_json
                
                # Detect VDC devices and consolidate
                vdc_match = re.match(r'^(.*?-7\d{3}-\d{2})-(ADMIN|CORE|EDGE|PCI)(?:\..*)?$', hostname)
                if vdc_match:
                    base_name = vdc_match.group(1)
                    vdc_type = vdc_match.group(2)
                    # For VDC devices, use base name and add VDC notes
                    display_hostname = base_name
                    notes = f"VDCs: {vdc_type}"  # Simplified for this test
                else:
                    display_hostname = hostname
                    notes = ""
                
                # Get device model and serial
                device_model = system_info.get('model', '')
                device_serial = system_info.get('serial_number', '')
                
                # Skip devices without proper serial numbers
                if not device_serial or device_serial in ['', '""', '""""']:
                    continue
                
                # Skip if already seen this device serial
                if device_serial in seen_serials:
                    continue
                seen_serials.add(device_serial)
                
                # Determine position based on device type
                position = 'Standalone'
                if any(x in str(system_info) + hostname for x in ['N5K', 'N56', 'n5000', 'n6000', '56128P', '5000']):
                    position = 'Parent Switch'
                elif 'stack' in hostname.lower():
                    position = 'Master'
                
                # Add parent device entry
                csv_data.append({
                    'hostname': display_hostname,
                    'ip_address': ip_address,
                    'position': position,
                    'model': device_model,
                    'serial_number': device_serial,
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': notes
                })
                
                # Process FEX devices
                for fex_key in ['fex', 'fex_units']:
                    for fex in components.get(fex_key, []):
                        fex_serial = fex.get('serial_number', '').strip()
                        if not fex_serial or fex_serial in seen_serials:
                            continue
                        seen_serials.add(fex_serial)
                        
                        description = fex.get('description', '')
                        
                        # Extract FEX number from description
                        fex_id = re.search(r'Fex-(\d+)', description)
                        fex_num = fex_id.group(1) if fex_id else '100'
                        
                        # Enhance FEX model
                        original_model = fex.get('model', '')
                        enhanced_model = self.extract_fex_model(description, original_model)
                        
                        csv_data.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': enhanced_model,
                            'serial_number': fex_serial,
                            'port_location': description,
                            'vendor': 'Cisco',
                            'notes': ''
                        })
                
                # Process modules (with filtering for empty serials)
                for module in components.get('modules', []):
                    module_serial = module.get('serial_number', '').strip()
                    module_model = module.get('model', '').strip()
                    module_desc = module.get('description', '')
                    
                    # Skip modules without valid serials (like FwdEngine modules)
                    if not module_serial or module_serial in ['', '""', '""""']:
                        continue
                    
                    # Skip if already seen
                    if module_serial in seen_serials:
                        continue
                    seen_serials.add(module_serial)
                    
                    # Skip empty models
                    if not module_model:
                        continue
                    
                    # Check for FEX module enhancement
                    if 'Fabric Extender' in module_desc:
                        enhanced_model = self.extract_fex_model(module_desc, module_model)
                        module_model = enhanced_model
                    
                    csv_data.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'Module',
                        'model': module_model,
                        'serial_number': module_serial,
                        'port_location': module_desc,
                        'vendor': '',
                        'notes': ''
                    })
                
                # Process SFPs/Transceivers (CRITICAL: Apply 10-per-device limit)
                sfp_count = 0
                for sfp in components.get('transceivers', []):
                    if sfp_count >= 10:  # EXACT SAME LIMIT AS ORIGINAL
                        break
                    
                    sfp_serial = sfp.get('serial_number', '').strip()
                    if not sfp_serial or sfp_serial in seen_serials:
                        continue
                    seen_serials.add(sfp_serial)
                    
                    # Enhance SFP model
                    original_model = sfp.get('model', 'SFP')
                    description = sfp.get('description', '')
                    enhanced_model, vendor = self.identify_sfp(description, original_model, sfp_serial)
                    
                    csv_data.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'SFP',
                        'model': enhanced_model,
                        'serial_number': sfp_serial,
                        'port_location': sfp.get('port', ''),
                        'vendor': vendor or '',
                        'notes': ''
                    })
                    sfp_count += 1
            
            cursor.close()
            conn.close()
            
            logging.info(f"Generated {len(csv_data)} rows with direct processing")
            return csv_data
            
        except Exception as e:
            logging.error(f"Database processing failed: {e}")
            raise
    
    def run_direct_process(self):
        """Run the direct database processing"""
        start_time = datetime.now()
        
        try:
            logging.info("="*60)
            logging.info("Starting Direct Database Processing")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("="*60)
            
            # Process inventory directly from database
            csv_data = self.process_database_inventory()
            
            # Write output CSV
            output_file = f"/usr/local/bin/Main/test_direct_processed_{self.timestamp}.csv"
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
            logging.info("Direct processing completed successfully!")
            logging.info(f"Output file: {output_file}")
            logging.info(f"Generated rows: {len(csv_data)}")
            logging.info(f"Execution time: {execution_time:.2f} seconds")
            logging.info("="*60)
            
            # Compare with known good file
            try:
                known_good_file = "/usr/local/bin/Main/inventory_ultimate_final_manual.csv"
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
            logging.error(f"Direct processing failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    processor = DirectDatabaseProcessor()
    success = processor.run_direct_process()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()