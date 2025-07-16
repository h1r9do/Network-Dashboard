#!/usr/bin/env python3
"""
Complete Inventory Processing Pipeline - Test Version

This script runs the entire inventory processing pipeline:
1. Fresh SNMP collection from devices
2. Model enhancement (FEX model extraction)
3. VPC deduplication (remove duplicates between -01/-02)
4. VDC consolidation
5. Database import

Documentation: /usr/local/bin/Main/INVENTORY_PROCESSING_PIPELINE.md
Created: July 10, 2025
Purpose: Test the complete pipeline before creating production version

IMPORTANT: This is a TEST script. Run outside of production hours.
"""

import os
import sys
import json
import csv
import re
import psycopg2
import subprocess
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
log_file = f'/tmp/inventory_pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class InventoryPipeline:
    def __init__(self, test_mode=True):
        self.test_mode = test_mode
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use test directories to avoid affecting production
        if test_mode:
            self.base_dir = '/tmp/inventory_test'
            self.output_dir = f'{self.base_dir}/output_{self.timestamp}'
            os.makedirs(self.output_dir, exist_ok=True)
            logging.info(f"TEST MODE: Output directory: {self.output_dir}")
        else:
            self.base_dir = '/usr/local/bin/Main'
            self.output_dir = self.base_dir
            
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX model patterns
        self.fex_patterns = {
            r'Nexus2232PP.*10GE': 'N2K-C2232PP-10GE',
            r'Nexus2248TP.*1GE': 'N2K-C2248TP-1GE', 
            r'Nexus2232TM.*10GE': 'N2K-C2232TM-10GE',
            r'B22.*DELL': 'N2K-B22DELL-P',
            r'Fabric Extender Module.*32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'Fabric Extender Module.*48x1GE.*4x10GE': 'N2K-C2248TP-1GE'
        }
        
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
        
    def step1_snmp_collection(self):
        """Step 1: Run fresh SNMP collection"""
        logging.info("="*60)
        logging.info("STEP 1: SNMP Collection")
        logging.info("="*60)
        
        if self.test_mode:
            logging.info("TEST MODE: Skipping actual SNMP collection")
            logging.info("Using existing data from comprehensive_device_inventory table")
            return True
            
        # In production, would run the actual SNMP collection
        script_path = '/usr/local/bin/Main/nightly_snmp_inventory_collection_final.py'
        if os.path.exists(script_path):
            try:
                result = subprocess.run(
                    ['python3', script_path],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                if result.returncode == 0:
                    logging.info("SNMP collection completed successfully")
                    return True
                else:
                    logging.error(f"SNMP collection failed: {result.stderr}")
                    return False
            except Exception as e:
                logging.error(f"Error running SNMP collection: {e}")
                return False
        else:
            logging.warning(f"SNMP collection script not found: {script_path}")
            return False
            
    def step2_export_from_database(self):
        """Step 2: Export current inventory from database"""
        logging.info("="*60)
        logging.info("STEP 2: Export from Database")
        logging.info("="*60)
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # Get device count
            cursor.execute("SELECT COUNT(*) FROM comprehensive_device_inventory")
            count = cursor.fetchone()[0]
            logging.info(f"Found {count} devices in database")
            
            # Export data
            query = """
            SELECT hostname, ip_address, system_info, physical_components
            FROM comprehensive_device_inventory
            WHERE physical_components IS NOT NULL
            ORDER BY hostname
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Build inventory structure
            inventory = {}
            for hostname, ip_address, system_info, physical_components in rows:
                if physical_components:
                    components = json.loads(physical_components) if isinstance(physical_components, str) else physical_components
                    inventory[hostname] = {
                        'ip_address': ip_address,
                        'system_info': json.loads(system_info) if isinstance(system_info, str) else system_info,
                        'components': components
                    }
            
            # Save to JSON
            json_file = f"{self.output_dir}/inventory_export.json"
            with open(json_file, 'w') as f:
                json.dump(inventory, f, indent=2)
                
            logging.info(f"Exported {len(inventory)} devices to {json_file}")
            
            cursor.close()
            conn.close()
            
            return inventory
            
        except Exception as e:
            logging.error(f"Database export failed: {e}")
            return None
            
    def step3_enhance_models(self, inventory):
        """Step 3: Apply model enhancements"""
        logging.info("="*60)
        logging.info("STEP 3: Model Enhancement")
        logging.info("="*60)
        
        enhanced_count = 0
        
        for device_name, device_data in inventory.items():
            components = device_data.get('components', {})
            
            # Process FEX devices (may be under 'fex' or 'fex_units')
            fex_lists = [
                components.get('fex', []),
                components.get('fex_units', []),
                components.get('modules', [])
            ]
            for fex_list in fex_lists:
                for component in fex_list:
                    description = component.get('description', '')
                    model = component.get('model', '')
                    
                    # Try to extract FEX model
                    if 'Nexus2' in description or 'Fabric Extender' in description:
                        for pattern, clean_model in self.fex_patterns.items():
                            if re.search(pattern, description, re.IGNORECASE):
                                old_model = component.get('model', '')
                                component['model'] = clean_model
                                if old_model != clean_model:
                                    enhanced_count += 1
                                    logging.debug(f"Enhanced: {old_model} -> {clean_model}")
                                break
                    
                    # Extract SFP model
                    elif 'SFP' in description and not model.startswith('SFP'):
                        component['model'] = 'SFP'
                        enhanced_count += 1
        
        logging.info(f"Enhanced {enhanced_count} model entries")
        
        # Save enhanced data
        enhanced_file = f"{self.output_dir}/inventory_enhanced.json"
        with open(enhanced_file, 'w') as f:
            json.dump(inventory, f, indent=2)
            
        return inventory
        
    def step4_identify_vpc_duplicates(self, inventory):
        """Step 4: Identify VPC duplicates"""
        logging.info("="*60)
        logging.info("STEP 4: VPC Duplicate Identification")
        logging.info("="*60)
        
        # Find N5K devices in VPC pairs
        n5k_vpc_pairs = set()
        for device_name, device_data in inventory.items():
            system_info = device_data.get('system_info', {})
            model = system_info.get('model', '')
            description = system_info.get('system_description', '')
            
            # Check model or description for N5K/N6K indicators
            is_nexus_5k = ('N5K' in model or 'N56' in model or 
                          'n5000' in description or 'n6000' in description or
                          '56128P' in device_name)
            
            if is_nexus_5k and (device_name.endswith('-01') or device_name.endswith('-02')):
                n5k_vpc_pairs.add(device_name)
                
        logging.info(f"Found N5K VPC pairs: {sorted(n5k_vpc_pairs)}")
        
        # Build serial number mapping
        serial_to_devices = {}
        for device_name in n5k_vpc_pairs:
            device_data = inventory.get(device_name, {})
            components = device_data.get('components', {})
            
            # Check both 'fex' and 'fex_units' 
            for fex_key in ['fex', 'fex_units']:
                for fex in components.get(fex_key, []):
                    serial = fex.get('serial_number', '').strip()
                    if serial and serial != 'N/A':
                        if serial not in serial_to_devices:
                            serial_to_devices[serial] = []
                        serial_to_devices[serial].append(device_name)
        
        # Find duplicates
        duplicates = {}
        for serial, devices in serial_to_devices.items():
            if len(devices) > 1:
                dev_01 = [d for d in devices if d.endswith('-01')]
                dev_02 = [d for d in devices if d.endswith('-02')]
                
                if dev_01 and dev_02:
                    prefix_01 = dev_01[0][:-3]
                    prefix_02 = dev_02[0][:-3]
                    if prefix_01 == prefix_02:
                        duplicates[serial] = devices
                        logging.info(f"Found duplicate FEX: {serial} on {dev_01[0]} and {dev_02[0]}")
        
        return duplicates
        
    def step5_apply_deduplication(self, inventory, duplicates):
        """Step 5: Remove duplicates"""
        logging.info("="*60)
        logging.info("STEP 5: Apply Deduplication")
        logging.info("="*60)
        
        removed_count = 0
        
        for serial, devices in duplicates.items():
            # Keep on -01, remove from -02
            dev_01 = [d for d in devices if d.endswith('-01')][0]
            dev_02 = [d for d in devices if d.endswith('-02')][0]
            
            # Find and remove from -02 (check both 'fex' and 'fex_units')
            components = inventory[dev_02].get('components', {})
            for fex_key in ['fex', 'fex_units']:
                if fex_key in components:
                    original_count = len(components[fex_key])
                    components[fex_key] = [f for f in components[fex_key] if f.get('serial_number') != serial]
                    removed = original_count - len(components[fex_key])
                    removed_count += removed
                    
                    if removed > 0:
                        logging.info(f"Removed {serial} from {dev_02}")
                        
                        # Add shared_with note to -01
                        dev_01_components = inventory[dev_01]['components']
                        for fex_key_01 in ['fex', 'fex_units']:
                            for fex in dev_01_components.get(fex_key_01, []):
                                if fex.get('serial_number') == serial:
                                    fex['shared_with'] = [dev_02]
                                    break
        
        logging.info(f"Removed {removed_count} duplicate FEX entries")
        
        # Save deduplicated data
        dedup_file = f"{self.output_dir}/inventory_deduplicated.json"
        with open(dedup_file, 'w') as f:
            json.dump(inventory, f, indent=2)
            
        return inventory
        
    def step6_generate_csv(self, inventory):
        """Step 6: Generate CSV format"""
        logging.info("="*60)
        logging.info("STEP 6: Generate CSV")
        logging.info("="*60)
        
        csv_data = []
        
        for device_name, device_data in inventory.items():
            ip_address = device_data['ip_address']
            system_info = device_data['system_info']
            
            # Add parent device
            csv_data.append({
                'hostname': device_name,
                'ip_address': ip_address,
                'position': 'Parent Switch' if 'N5K' in system_info.get('model', '') else 'Standalone',
                'model': system_info.get('model', ''),
                'serial_number': system_info.get('serial_number', ''),
                'port_location': '',
                'vendor': system_info.get('manufacturer', 'Cisco'),
                'notes': ''
            })
            
            # Add components
            components = device_data.get('components', {})
            
            # FEX devices (check both 'fex' and 'fex_units')
            for fex_key in ['fex', 'fex_units']:
                for fex in components.get(fex_key, []):
                    notes = fex.get('description', '')
                    if 'shared_with' in fex:
                        notes += f" | Shared with: {', '.join(fex['shared_with'])}"
                    
                    # Determine position - FEX units should have FEX-xxx position
                    position = fex.get('position', '')
                    if not position and fex_key == 'fex_units':
                        # Try to extract from description
                        if 'Fex-' in notes:
                            import re
                            match = re.search(r'Fex-(\d+)', notes)
                            if match:
                                position = f'FEX-{match.group(1)}'
                        
                    csv_data.append({
                        'hostname': '',
                        'ip_address': '',
                        'position': position,
                        'model': fex.get('model', ''),
                        'serial_number': fex.get('serial_number', ''),
                        'port_location': '',
                        'vendor': 'Cisco',
                        'notes': notes.strip()
                    })
            
            # Modules
            for module in components.get('modules', []):
                csv_data.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': module.get('position', 'Module'),
                    'model': module.get('model', ''),
                    'serial_number': module.get('serial_number', ''),
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': module.get('description', '')
                })
        
        # Write CSV
        csv_file = f"{self.output_dir}/inventory_final.csv"
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['hostname', 'ip_address', 'position', 'model', 'serial_number', 
                         'port_location', 'vendor', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        logging.info(f"Generated CSV with {len(csv_data)} rows: {csv_file}")
        
        return csv_file, csv_data
        
    def step7_import_to_database(self, csv_file, csv_data):
        """Step 7: Import to database (TEST MODE: simulated)"""
        logging.info("="*60)
        logging.info("STEP 7: Database Import (TEST MODE)")
        logging.info("="*60)
        
        if self.test_mode:
            logging.info("TEST MODE: Simulating database import")
            
            # Analyze the data
            parents = [r for r in csv_data if r['hostname']]
            fex_devices = [r for r in csv_data if r['position'].startswith('FEX')]
            modules = [r for r in csv_data if 'Module' in r['position']]
            
            logging.info(f"Would import:")
            logging.info(f"  - Parent devices: {len(parents)}")
            logging.info(f"  - FEX devices: {len(fex_devices)}")
            logging.info(f"  - Modules: {len(modules)}")
            logging.info(f"  - Total rows: {len(csv_data)}")
            
            # Check for duplicate FEX
            fex_serials = [f['serial_number'] for f in fex_devices if f['serial_number']]
            unique_serials = set(fex_serials)
            if len(fex_serials) == len(unique_serials):
                logging.info("✓ No duplicate FEX serial numbers")
            else:
                logging.warning(f"! Found {len(fex_serials) - len(unique_serials)} duplicate FEX serials")
            
            return True
        else:
            # Production import would go here
            logging.info("Production import would update inventory_web_format table")
            return False
            
    def generate_report(self):
        """Generate final report"""
        logging.info("="*60)
        logging.info("PIPELINE COMPLETE - SUMMARY REPORT")
        logging.info("="*60)
        
        report = f"""
Inventory Processing Pipeline Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {'TEST' if self.test_mode else 'PRODUCTION'}
Output Directory: {self.output_dir}
Log File: {log_file}

Files Generated:
- inventory_export.json - Raw export from database
- inventory_enhanced.json - After model enhancement
- inventory_deduplicated.json - After removing VPC duplicates
- inventory_final.csv - Final CSV ready for import

Next Steps:
1. Review the generated files in {self.output_dir}
2. Compare with current production data
3. If satisfactory, create production version of this script
4. Schedule in cron to run nightly

To run in production mode:
python3 {__file__} --production
"""
        
        report_file = f"{self.output_dir}/pipeline_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(report)
        logging.info(f"Report saved to: {report_file}")
        
    def run(self):
        """Run the complete pipeline"""
        try:
            logging.info("Starting Inventory Processing Pipeline")
            
            # Step 1: SNMP Collection (skipped in test mode)
            if not self.step1_snmp_collection():
                logging.warning("SNMP collection skipped/failed, using existing data")
            
            # Step 2: Export from database
            inventory = self.step2_export_from_database()
            if not inventory:
                logging.error("Failed to export from database")
                return False
                
            # Step 3: Enhance models
            inventory = self.step3_enhance_models(inventory)
            
            # Step 4: Identify duplicates
            duplicates = self.step4_identify_vpc_duplicates(inventory)
            
            # Step 5: Apply deduplication
            if duplicates:
                inventory = self.step5_apply_deduplication(inventory, duplicates)
            else:
                logging.info("No VPC duplicates found")
            
            # Step 6: Generate CSV
            csv_file, csv_data = self.step6_generate_csv(inventory)
            
            # Step 7: Import to database
            self.step7_import_to_database(csv_file, csv_data)
            
            # Generate report
            self.generate_report()
            
            return True
            
        except Exception as e:
            logging.error(f"Pipeline failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    # Check for production flag
    production_mode = '--production' in sys.argv
    
    if production_mode:
        response = input("WARNING: Running in PRODUCTION mode. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
            
    # Run pipeline
    pipeline = InventoryPipeline(test_mode=not production_mode)
    success = pipeline.run()
    
    if success:
        logging.info("Pipeline completed successfully")
    else:
        logging.error("Pipeline failed")
        sys.exit(1)

if __name__ == '__main__':
    main()