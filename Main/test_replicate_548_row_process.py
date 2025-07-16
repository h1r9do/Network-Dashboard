#!/usr/bin/env python3
"""
Test Script to Replicate 548-Row Process
=========================================

This script replicates the entire multi-step process that creates the known good
548-row inventory_ultimate_final.csv by:

1. Reading raw SNMP data from database
2. Applying exact same filtering as generate_ultimate_final_csv.py
3. Using same enhancement logic as complete_inventory_enhancement.py
4. Using same deduplication as deduplicate_inventory_serials.py
5. Using same VDC consolidation as consolidate_vdc_devices.py
6. Producing CSV that exactly matches the known good output

Goal: Generate test output that matches inventory_ultimate_final_manual.csv exactly
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

class ReplicateOriginalProcess:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX patterns from complete_inventory_enhancement.py
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
        """Extract FEX model from description (from complete_inventory_enhancement.py)"""
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
    
    def export_from_database(self):
        """Export raw inventory from database (like nightly_inventory_complete_pipeline.py)"""
        logging.info("Step 1: Export from Database")
        
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
            
            logging.info(f"Exported {len(inventory)} devices from database")
            
            cursor.close()
            conn.close()
            
            return inventory
            
        except Exception as e:
            logging.error(f"Database export failed: {e}")
            raise
    
    def enhance_models(self, inventory):
        """Apply model enhancements (from complete_inventory_enhancement.py)"""
        logging.info("Step 2: Model Enhancement")
        
        enhanced_count = 0
        fex_enhanced = 0
        sfp_enhanced = 0
        
        for device_name, device_data in inventory.items():
            components = device_data.get('components', {})
            
            # Process FEX devices
            for fex_key in ['fex', 'fex_units', 'modules']:
                for component in components.get(fex_key, []):
                    description = component.get('description', '')
                    model = component.get('model', '')
                    
                    # Try to extract FEX model
                    if 'Nexus2' in description or 'Fabric Extender' in description:
                        old_model = component.get('model', '')
                        enhanced_model = self.extract_fex_model(description, model)
                        if enhanced_model != old_model:
                            component['model'] = enhanced_model
                            enhanced_count += 1
                            fex_enhanced += 1
                    
                    # Extract SFP model
                    elif 'SFP' in description and not model.startswith('SFP'):
                        component['model'] = 'SFP'
                        enhanced_count += 1
                        sfp_enhanced += 1
        
        logging.info(f"Enhanced {enhanced_count} model entries ({fex_enhanced} FEX, {sfp_enhanced} SFP)")
        return inventory
    
    def identify_vpc_duplicates(self, inventory):
        """Identify VPC duplicates (from deduplicate_inventory_serials.py)"""
        logging.info("Step 3: VPC Duplicate Identification")
        
        # Find N5K/N6K devices in VPC pairs
        n5k_vpc_pairs = set()
        for device_name, device_data in inventory.items():
            system_info = device_data.get('system_info', {})
            model = system_info.get('model', '')
            description = system_info.get('system_description', '')
            
            # Check for N5K/N6K indicators
            is_nexus_5k = ('N5K' in model or 'N56' in model or 
                          'n5000' in description or 'n6000' in description or
                          '56128P' in device_name or '5000' in device_name)
            
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
                    if serial and serial != 'N/A' and serial != '':
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
                    # Verify they are matching pairs
                    prefix_01 = dev_01[0][:-3]
                    prefix_02 = dev_02[0][:-3]
                    if prefix_01 == prefix_02:
                        duplicates[serial] = devices
                        logging.info(f"Found duplicate FEX: {serial} on {dev_01[0]} and {dev_02[0]}")
        
        return duplicates
    
    def apply_deduplication(self, inventory, duplicates):
        """Remove duplicates, keeping FEX only on -01 devices (from deduplicate_inventory_serials.py)"""
        logging.info("Step 4: Apply Deduplication")
        
        removed_count = 0
        
        for serial, devices in duplicates.items():
            # Keep on -01, remove from -02
            dev_01 = [d for d in devices if d.endswith('-01')][0]
            dev_02 = [d for d in devices if d.endswith('-02')][0]
            
            # Remove from -02
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
        return inventory
    
    def detect_vdc_devices(self, inventory):
        """Detect VDC devices (from consolidate_vdc_devices.py)"""
        logging.info("Step 5: VDC Detection")
        
        vdc_groups = {}
        regular_devices = {}
        
        for device_name, device_data in inventory.items():
            # Check for VDC pattern: base_name-(ADMIN|CORE|EDGE|PCI)
            vdc_match = re.match(r'^(.*?-7\d{3}-\d{2})-(ADMIN|CORE|EDGE|PCI)(?:\..*)?$', device_name)
            
            if vdc_match:
                base_name = vdc_match.group(1)
                vdc_type = vdc_match.group(2)
                
                if base_name not in vdc_groups:
                    vdc_groups[base_name] = {}
                vdc_groups[base_name][vdc_type] = device_data
            else:
                regular_devices[device_name] = device_data
        
        logging.info(f"Found {len(vdc_groups)} VDC groups and {len(regular_devices)} regular devices")
        return vdc_groups, regular_devices
    
    def consolidate_vdc_groups(self, vdc_groups):
        """Consolidate VDC groups into single devices (from consolidate_vdc_devices.py)"""
        logging.info("Step 6: VDC Consolidation")
        
        consolidated = {}
        
        for base_name, vdc_devices in vdc_groups.items():
            # Use CORE VDC as primary, fall back to first available
            primary_vdc = vdc_devices.get('CORE') or list(vdc_devices.values())[0]
            
            # Create consolidated device
            consolidated_device = {
                'ip_address': primary_vdc['ip_address'],
                'system_info': primary_vdc['system_info'],
                'components': primary_vdc['components'],
                'vdc_info': {
                    'is_vdc': True,
                    'vdc_names': list(vdc_devices.keys())
                }
            }
            
            # Merge components from all VDCs
            for vdc_type, vdc_data in vdc_devices.items():
                for component_type, components in vdc_data['components'].items():
                    if component_type not in consolidated_device['components']:
                        consolidated_device['components'][component_type] = []
                    
                    # Add components if not duplicate
                    for component in components:
                        serial = component.get('serial_number', '')
                        existing_serials = [c.get('serial_number', '') for c in consolidated_device['components'][component_type]]
                        if serial not in existing_serials:
                            consolidated_device['components'][component_type].append(component)
            
            consolidated[base_name] = consolidated_device
        
        logging.info(f"Consolidated {len(vdc_groups)} VDC groups into {len(consolidated)} devices")
        return consolidated
    
    def generate_final_csv_like_original(self, inventory):
        """Generate CSV using exact logic from generate_ultimate_final_csv.py"""
        logging.info("Step 7: Generate Final CSV (Original Logic)")
        
        # Convert inventory to device list format like original
        devices = []
        for hostname, device_data in inventory.items():
            # Build physical inventory structure
            physical_inv = {
                'chassis': [],
                'modules': [],
                'transceivers': []
            }
            
            # Add main chassis
            system_info = device_data['system_info']
            main_chassis = {
                'serial': system_info.get('serial_number', ''),
                'model': system_info.get('model', ''),
                'name': hostname,
                'description': system_info.get('system_description', '')
            }
            
            # Only add chassis if it has a valid serial number
            if main_chassis['serial'] and main_chassis['serial'] not in ['', '""', '""""']:
                physical_inv['chassis'].append(main_chassis)
            
            # Add FEX as additional chassis
            components = device_data.get('components', {})
            for fex_key in ['fex', 'fex_units']:
                for fex in components.get(fex_key, []):
                    fex_chassis = {
                        'serial': fex.get('serial_number', ''),
                        'model': fex.get('model', ''),
                        'name': fex.get('description', ''),
                        'description': fex.get('description', '')
                    }
                    physical_inv['chassis'].append(fex_chassis)
            
            # Add modules
            for module in components.get('modules', []):
                physical_inv['modules'].append({
                    'serial': module.get('serial_number', ''),
                    'model': module.get('model', ''),
                    'name': module.get('description', ''),
                    'description': module.get('description', '')
                })
            
            # Add transceivers/SFPs
            for sfp in components.get('transceivers', []):
                physical_inv['transceivers'].append({
                    'serial': sfp.get('serial_number', ''),
                    'model': sfp.get('model', ''),
                    'name': sfp.get('port', ''),
                    'description': sfp.get('description', '')
                })
            
            device_entry = {
                'hostname': hostname,
                'ip': device_data['ip_address'],
                'physical_inventory': physical_inv
            }
            
            # Add VDC info if present
            if 'vdc_info' in device_data:
                device_entry['vdc_info'] = device_data['vdc_info']
            
            devices.append(device_entry)
        
        # Apply EXACT original filtering logic
        seen_serials = set()
        csv_data = []
        
        for device in devices:
            hostname = device['hostname']
            ip = device['ip']
            physical_inv = device['physical_inventory']
            
            # Get VDC notes if applicable
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
            
            # Handle chassis (same logic as original)
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
        
        logging.info(f"Generated {len(csv_data)} rows with original filtering logic")
        return csv_data
    
    def run_complete_process(self):
        """Run the complete process to replicate 548-row output"""
        start_time = datetime.now()
        
        try:
            logging.info("="*60)
            logging.info("Starting Complete Process Replication")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("="*60)
            
            # Step 1: Export from database
            inventory = self.export_from_database()
            if not inventory:
                logging.error("No inventory data to process")
                return False
            
            # Step 2: Enhance models
            inventory = self.enhance_models(inventory)
            
            # Step 3: Identify and apply VPC deduplication
            duplicates = self.identify_vpc_duplicates(inventory)
            if duplicates:
                inventory = self.apply_deduplication(inventory, duplicates)
            else:
                logging.info("No VPC duplicates found")
            
            # Step 4: VDC consolidation
            vdc_groups, regular_devices = self.detect_vdc_devices(inventory)
            if vdc_groups:
                consolidated_vdc = self.consolidate_vdc_groups(vdc_groups)
                # Merge consolidated VDC devices with regular devices
                final_inventory = {**regular_devices, **consolidated_vdc}
            else:
                final_inventory = regular_devices
            
            # Step 5: Generate final CSV with original filtering
            csv_data = self.generate_final_csv_like_original(final_inventory)
            
            # Step 6: Write output CSV
            output_file = f"/usr/local/bin/Main/test_replicated_548_rows_{self.timestamp}.csv"
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
            logging.info("Process completed successfully!")
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
            logging.error(f"Process failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    replicator = ReplicateOriginalProcess()
    success = replicator.run_complete_process()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()