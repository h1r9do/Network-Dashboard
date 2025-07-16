#!/usr/bin/env python3
"""
Comprehensive inventory processing script that:
1. Exports fresh data from the database
2. Applies VPC deduplication (assigns shared resources to -01 devices only)
3. Applies model enhancement (extracts FEX models from descriptions)
4. Imports the clean data back to the database
"""
import psycopg2
import json
import csv
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InventoryProcessor:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        self.duplicates = {}
        self.data = {}
        
    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
        
    def export_from_database(self):
        """Export current inventory data from database"""
        logging.info("Exporting inventory data from database...")
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Get all device data from comprehensive_device_inventory
        query = """
        SELECT hostname, ip_address, system_info, physical_components
        FROM comprehensive_device_inventory
        WHERE physical_components IS NOT NULL
        ORDER BY hostname
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Build the inventory structure
        inventory = {}
        for hostname, ip_address, system_info, physical_components in rows:
            if physical_components:
                components = json.loads(physical_components) if isinstance(physical_components, str) else physical_components
                inventory[hostname] = {
                    'ip_address': ip_address,
                    'system_info': json.loads(system_info) if isinstance(system_info, str) else system_info,
                    'components': components
                }
        
        cursor.close()
        conn.close()
        
        logging.info(f"Exported {len(inventory)} devices from database")
        return inventory
        
    def identify_vpc_duplicates(self, inventory):
        """Identify shared components between VPC pairs"""
        logging.info("Identifying VPC duplicates...")
        serial_to_devices = {}
        
        # First identify N5K devices in VPC pairs
        n5k_vpc_pairs = set()
        for device_name, device_data in inventory.items():
            system_info = device_data.get('system_info', {})
            model = system_info.get('model', '')
            # Check if this is an N5K device in a VPC pair
            if ('N5K' in model or 'N56' in model) and (device_name.endswith('-01') or device_name.endswith('-02')):
                n5k_vpc_pairs.add(device_name)
        
        logging.info(f"Found N5K VPC pairs: {sorted(n5k_vpc_pairs)}")
        
        # Build mapping of serial numbers to devices (only for N5K VPC pairs)
        for device_name in n5k_vpc_pairs:
            device_data = inventory.get(device_name, {})
            components = device_data.get('components', {})
            
            # Check FEX devices
            for comp_type in ['fex']:  # Only check FEX, not modules
                if comp_type in components:
                    for component in components[comp_type]:
                        serial = component.get('serial_number', '').strip()
                        if serial and serial != 'N/A' and serial != '':
                            if serial not in serial_to_devices:
                                serial_to_devices[serial] = []
                            serial_to_devices[serial].append({
                                'device': device_name,
                                'component': component,
                                'type': comp_type
                            })
        
        # Identify duplicates (components shared between -01 and -02 devices)
        duplicates = {}
        for serial, devices in serial_to_devices.items():
            if len(devices) > 1:
                device_names = [d['device'] for d in devices]
                # Check if this is a VPC pair (one ends with -01, other with -02)
                dev_01 = [d for d in device_names if d.endswith('-01')]
                dev_02 = [d for d in device_names if d.endswith('-02')]
                
                if dev_01 and dev_02:
                    # Verify they are matching pairs (same prefix)
                    prefix_01 = dev_01[0][:-3]  # Remove '-01'
                    prefix_02 = dev_02[0][:-3]  # Remove '-02'
                    if prefix_01 == prefix_02:
                        duplicates[serial] = devices
                        logging.info(f"Found VPC duplicate FEX: {serial} shared between {dev_01[0]} and {dev_02[0]}")
        
        return duplicates
        
    def apply_vpc_deduplication(self, inventory, duplicates):
        """Remove duplicates, keeping resources only on -01 devices"""
        logging.info("Applying VPC deduplication...")
        deduped_inventory = {}
        
        for device_name, device_data in inventory.items():
            deduped_data = {
                'ip_address': device_data['ip_address'],
                'system_info': device_data['system_info'],
                'components': {}
            }
            
            # Process each component type
            for comp_type, components in device_data.get('components', {}).items():
                deduped_components = []
                
                for component in components:
                    serial = component.get('serial_number', '').strip()
                    
                    # Check if this is a duplicate
                    if serial in duplicates:
                        # Find which devices share this component
                        sharing_devices = [d['device'] for d in duplicates[serial]]
                        
                        # Keep component only on -01 device
                        if device_name.endswith('-01'):
                            # Add shared_with information
                            component['shared_with'] = [d for d in sharing_devices if d != device_name]
                            deduped_components.append(component)
                            logging.info(f"Keeping {serial} on {device_name}, shared with {component['shared_with']}")
                        elif device_name.endswith('-02'):
                            # Skip this component on -02 device
                            logging.info(f"Removing {serial} from {device_name} (kept on -01)")
                            continue
                    else:
                        # Not a duplicate, keep it
                        deduped_components.append(component)
                
                if deduped_components:
                    deduped_data['components'][comp_type] = deduped_components
            
            deduped_inventory[device_name] = deduped_data
        
        return deduped_inventory
        
    def enhance_model_info(self, inventory):
        """Extract clean model numbers from descriptions"""
        logging.info("Enhancing model information...")
        
        # FEX model patterns
        fex_patterns = {
            r'Nexus2232PP.*10GE': 'N2K-C2232PP-10GE',
            r'Nexus2248TP.*1GE': 'N2K-C2248TP-1GE',
            r'Nexus2232TM.*10GE': 'N2K-C2232TM-10GE',
            r'B22.*DELL': 'N2K-B22DELL-P',
            r'Fabric Extender Module.*32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'Fabric Extender Module.*48x1GE.*4x10GE': 'N2K-C2248TP-1GE'
        }
        
        enhanced_inventory = {}
        
        for device_name, device_data in inventory.items():
            enhanced_data = device_data.copy()
            
            # Process components
            for comp_type, components in device_data.get('components', {}).items():
                for component in components:
                    description = component.get('description', '')
                    model = component.get('model', '')
                    
                    # Try to extract FEX model from description
                    if 'Nexus2' in description or 'Fabric Extender' in description:
                        for pattern, clean_model in fex_patterns.items():
                            if re.search(pattern, description, re.IGNORECASE):
                                component['model'] = clean_model
                                logging.info(f"Enhanced FEX model: {description} -> {clean_model}")
                                break
                    
                    # Extract SFP model if present
                    elif 'SFP' in description and not model.startswith('SFP'):
                        component['model'] = 'SFP'
            
            enhanced_inventory[device_name] = enhanced_data
        
        return enhanced_inventory
        
    def generate_csv_format(self, inventory):
        """Convert to CSV format matching inventory_web_format table"""
        logging.info("Generating CSV format data...")
        csv_data = []
        
        for device_name, device_data in inventory.items():
            ip_address = device_data['ip_address']
            system_info = device_data['system_info']
            
            # Add parent device
            csv_data.append({
                'hostname': device_name,
                'parent_hostname': '',
                'ip_address': ip_address,
                'position': 'Parent Switch',
                'model': system_info.get('model', ''),
                'serial_number': system_info.get('serial_number', ''),
                'port_location': '',
                'vendor': system_info.get('manufacturer', 'Cisco'),
                'notes': ''
            })
            
            # Add components
            components = device_data.get('components', {})
            
            # Process FEX devices
            for fex in components.get('fex', []):
                notes = fex.get('description', '')
                # Add shared_with info to notes
                if 'shared_with' in fex:
                    notes += f" | Shared with: {', '.join(fex['shared_with'])}"
                    
                csv_data.append({
                    'hostname': '',
                    'parent_hostname': device_name,
                    'ip_address': '',
                    'position': fex.get('position', ''),
                    'model': fex.get('model', ''),
                    'serial_number': fex.get('serial_number', ''),
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': notes.strip()
                })
            
            # Process modules
            for module in components.get('modules', []):
                csv_data.append({
                    'hostname': '',
                    'parent_hostname': device_name,
                    'ip_address': '',
                    'position': module.get('position', 'Module'),
                    'model': module.get('model', ''),
                    'serial_number': module.get('serial_number', ''),
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': module.get('description', '')
                })
            
        return csv_data
        
    def import_to_database(self, csv_data):
        """Import the processed data to inventory_web_format table"""
        logging.info("Importing to database...")
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # Clear existing data
            cursor.execute("DELETE FROM inventory_web_format")
            logging.info("Cleared existing inventory_web_format data")
            
            # Insert new data
            insert_query = """
            INSERT INTO inventory_web_format 
            (hostname, parent_hostname, ip_address, position, model, serial_number, port_location, vendor, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for row in csv_data:
                cursor.execute(insert_query, (
                    row['hostname'],
                    row['parent_hostname'],
                    row['ip_address'],
                    row['position'],
                    row['model'],
                    row['serial_number'],
                    row['port_location'],
                    row['vendor'],
                    row['notes']
                ))
            
            conn.commit()
            logging.info(f"Imported {len(csv_data)} rows to inventory_web_format")
            
            # Get counts
            cursor.execute("SELECT COUNT(DISTINCT serial_number) FROM inventory_web_format WHERE position LIKE 'FEX%'")
            fex_count = cursor.fetchone()[0]
            logging.info(f"Total unique FEX devices: {fex_count}")
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Database import failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
            
    def save_csv_file(self, csv_data, filename):
        """Save the data to a CSV file"""
        logging.info(f"Saving to {filename}...")
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['hostname', 'ip_address', 'position', 'model', 'serial_number', 'port_location', 'vendor', 'notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in csv_data:
                # Format for CSV output
                csv_row = {
                    'hostname': row['hostname'],
                    'ip_address': row['ip_address'],
                    'position': row['position'],
                    'model': row['model'],
                    'serial_number': row['serial_number'],
                    'port_location': row['port_location'],
                    'vendor': row['vendor'],
                    'notes': row['notes']
                }
                writer.writerow(csv_row)
                
        logging.info(f"Saved {len(csv_data)} rows to {filename}")
            
    def run(self):
        """Run the complete processing pipeline"""
        try:
            # Step 1: Export fresh data from database
            inventory = self.export_from_database()
            
            # Step 2: Identify VPC duplicates
            duplicates = self.identify_vpc_duplicates(inventory)
            
            # Step 3: Apply VPC deduplication
            deduped_inventory = self.apply_vpc_deduplication(inventory, duplicates)
            
            # Step 4: Enhance model information
            enhanced_inventory = self.enhance_model_info(deduped_inventory)
            
            # Step 5: Convert to CSV format
            csv_data = self.generate_csv_format(enhanced_inventory)
            
            # Step 6: Save to CSV file (for reference)
            self.save_csv_file(csv_data, '/usr/local/bin/Main/inventory_processed.csv')
            
            # Step 7: Import to database
            self.import_to_database(csv_data)
            
            logging.info("Processing complete!")
            
        except Exception as e:
            logging.error(f"Processing failed: {e}")
            raise

if __name__ == '__main__':
    processor = InventoryProcessor()
    processor.run()