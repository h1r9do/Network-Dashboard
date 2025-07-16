#!/usr/bin/env python3
"""
PRODUCTION NIGHTLY INVENTORY PROCESSING PIPELINE
==============================================

Purpose:
    Complete inventory processing pipeline that runs nightly to:
    1. Collect SNMP data from network devices (optional - can use existing data)
    2. Export data from comprehensive_device_inventory table
    3. Apply model enhancements (extract clean FEX models)
    4. Remove VPC duplicates (keep FEX only on -01 switches)
    5. Import processed data to inventory_web_format table

Schedule:
    Run nightly at 2:30 AM (after SNMP collection at 2:00 AM)
    
Cron Entry:
    30 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_complete_pipeline.py >> /var/log/nightly-inventory-pipeline.log 2>&1

Database Tables:
    Input: comprehensive_device_inventory (raw SNMP data)
    Output: inventory_web_format (processed data for web display)

Created: July 10, 2025
Based on: July 8, 2025 inventory processing work
Documentation: /usr/local/bin/Main/INVENTORY_PROCESSING_PIPELINE.md
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InventoryPipeline:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use production directories
        self.base_dir = '/usr/local/bin/Main'
        self.temp_dir = f'/tmp/inventory_pipeline_{self.timestamp}'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'T3dC$gLp9'
        }
        
        # FEX model patterns for enhancement
        self.fex_patterns = {
            r'Nexus2232PP.*10GE': 'N2K-C2232PP-10GE',
            r'Nexus2248TP.*1GE': 'N2K-C2248TP-1GE',
            r'Nexus2248(?!TP)': 'N2K-C2248TP-1GE',  # Nexus2248 without TP
            r'Nexus2232TM.*10GE': 'N2K-C2232TM-10GE',
            r'B22.*DELL': 'N2K-B22DELL-P',
            r'Fabric Extender Module.*32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'Fabric Extender Module.*48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'Fabric Extender Module.*16x10GE.*8x10GE': 'N2K-B22DELL-P'
        }
        
        # SFP patterns
        self.sfp_patterns = {
            r'1000BaseSX': 'GLC-SX-MMD',
            r'1000BaseLX': 'GLC-LX-SMD',
            r'10/100/1000BaseTX': 'GLC-T',
            r'SFP-10Gbase-SR': 'SFP-10G-SR',
            r'SFP-10Gbase-LR': 'SFP-10G-LR'
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
        
    def assign_site_from_ip(self, ip_address, hostname):
        """Assign site based on IP address ranges and hostname patterns"""
        # If no IP, try hostname patterns
        if not ip_address:
            hostname_lower = hostname.lower()
            if any(x in hostname_lower for x in ['ala-', 'al-', 'alameda']):
                return 'AZ-Alameda-DC'
            elif any(x in hostname_lower for x in ['mdf-', 'n5k-', 'n7k-', '2960', 'dtc_phx']):
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
    
    def lookup_eol_data(self, model):
        """Lookup EoS/EoL dates from corporate_eol table"""
        if not model:
            return '', ''
            
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT end_of_sale_date, end_of_support_date 
                FROM corporate_eol 
                WHERE model = %s
            """, (model,))
            result = cursor.fetchone()
            
            if result:
                end_of_sale = str(result[0]) if result[0] else ''
                end_of_support = str(result[1]) if result[1] else ''
                return end_of_sale, end_of_support
            return '', ''
            
        except Exception as e:
            logging.warning(f"EoL lookup failed for model {model}: {e}")
            return '', ''
        finally:
            cursor.close()
            conn.close()
        
    def run_snmp_collection(self):
        """Optional: Run SNMP collection if needed"""
        logging.info("="*60)
        logging.info("STEP 1: SNMP Collection Check")
        logging.info("="*60)
        
        # Check when SNMP was last run
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT MAX(created_at) 
                FROM comprehensive_device_inventory 
                WHERE created_at IS NOT NULL
            """)
            last_collection = cursor.fetchone()[0]
            
            if last_collection:
                hours_ago = (datetime.now() - last_collection).total_seconds() / 3600
                logging.info(f"Last SNMP collection: {last_collection} ({hours_ago:.1f} hours ago)")
                
                if hours_ago > 24:
                    logging.warning("SNMP data is more than 24 hours old - consider running collection")
                else:
                    logging.info("SNMP data is recent - skipping collection")
            else:
                logging.warning("No SNMP collection timestamp found")
                
        except Exception as e:
            logging.error(f"Error checking SNMP collection status: {e}")
        finally:
            cursor.close()
            conn.close()
            
    def export_from_database(self):
        """Export current inventory from database"""
        logging.info("="*60)
        logging.info("STEP 2: Export from Database")
        logging.info("="*60)
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
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
        """Apply model enhancements"""
        logging.info("="*60)
        logging.info("STEP 3: Model Enhancement")
        logging.info("="*60)
        
        enhanced_count = 0
        fex_enhanced = 0
        sfp_enhanced = 0
        
        for device_name, device_data in inventory.items():
            components = device_data.get('components', {})
            
            # Process FEX devices (may be under 'fex' or 'fex_units')
            for fex_key in ['fex', 'fex_units', 'modules']:
                for component in components.get(fex_key, []):
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
                                    fex_enhanced += 1
                                break
                    
                    # Extract SFP model
                    elif 'SFP' in description and not model.startswith('SFP'):
                        component['model'] = 'SFP'
                        enhanced_count += 1
                        sfp_enhanced += 1
        
        logging.info(f"Enhanced {enhanced_count} model entries ({fex_enhanced} FEX, {sfp_enhanced} SFP)")
        return inventory
        
    def identify_vpc_duplicates(self, inventory):
        """Identify VPC duplicates"""
        logging.info("="*60)
        logging.info("STEP 4: VPC Duplicate Identification")
        logging.info("="*60)
        
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
        """Remove duplicates, keeping FEX only on -01 devices"""
        logging.info("="*60)
        logging.info("STEP 5: Apply Deduplication")
        logging.info("="*60)
        
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
        
    def generate_csv_format(self, inventory):
        """Convert to CSV format for database import"""
        logging.info("="*60)
        logging.info("STEP 6: Generate CSV Format")
        logging.info("="*60)
        
        csv_data = []
        
        for device_name, device_data in inventory.items():
            ip_address = device_data['ip_address']
            system_info = device_data['system_info']
            
            # Add parent device - check for empty model and try to extract from description
            device_model = system_info.get('model', '')
            if not device_model:
                # Try to extract model from system description
                sys_desc = system_info.get('system_description', '')
                if 'N5K-C56128P' in sys_desc or 'n6000' in sys_desc:
                    device_model = 'N5K-C56128P'
                elif 'N5K-C5548UP' in sys_desc or 'n5000' in sys_desc:
                    device_model = 'N5K-C5548UP'
                elif 'WS-C' in sys_desc:
                    # Extract Catalyst model
                    model_match = re.search(r'(WS-C[A-Z0-9\-]+)', sys_desc)
                    if model_match:
                        device_model = model_match.group(1)
            
            # Determine position based on device type
            position = 'Standalone'
            if any(x in str(system_info) + device_name for x in ['N5K', 'N56', 'n5000', 'n6000', '56128P', '5000']):
                position = 'Parent Switch'
            
            # Add site assignment and EoS/EoL data
            site = self.assign_site_from_ip(ip_address, device_name)
            end_of_sale, end_of_support = self.lookup_eol_data(device_model)
            
            csv_data.append({
                'site': site,
                'hostname': device_name,
                'parent_hostname': '',  # Empty for parent devices
                'ip_address': ip_address,
                'position': position,
                'model': device_model,
                'serial_number': system_info.get('serial_number', ''),
                'port_location': '',  # Empty for parent devices
                'vendor': system_info.get('manufacturer', 'Cisco'),
                'notes': '',  # Empty for parent devices
                'end_of_sale': end_of_sale,
                'end_of_support': end_of_support
            })
            
            # Add components
            components = device_data.get('components', {})
            
            # FEX devices
            for fex_key in ['fex', 'fex_units']:
                for fex in components.get(fex_key, []):
                    description = fex.get('description', '')
                    shared_notes = ''
                    if 'shared_with' in fex:
                        shared_notes = f"Shared with: {', '.join(fex['shared_with'])}"
                    
                    # Determine position
                    position = fex.get('position', '')
                    if not position and fex_key == 'fex_units':
                        # Extract from description
                        if 'Fex-' in description:
                            match = re.search(r'Fex-(\d+)', description)
                            if match:
                                position = f'FEX-{match.group(1)}'
                        
                    # Add EoS/EoL data for FEX
                    fex_model = fex.get('model', '')
                    fex_end_of_sale, fex_end_of_support = self.lookup_eol_data(fex_model)
                    
                    csv_data.append({
                        'site': site,  # Use parent device's site
                        'hostname': '',
                        'parent_hostname': device_name,
                        'ip_address': '',
                        'position': position,
                        'model': fex_model,
                        'serial_number': fex.get('serial_number', ''),
                        'port_location': description,  # FEX description goes in port_location
                        'vendor': 'Cisco',
                        'notes': shared_notes,  # Only shared notes go here
                        'end_of_sale': fex_end_of_sale,
                        'end_of_support': fex_end_of_support
                    })
            
            # Modules
            for module in components.get('modules', []):
                # Add EoS/EoL data for modules
                module_model = module.get('model', '')
                module_end_of_sale, module_end_of_support = self.lookup_eol_data(module_model)
                
                csv_data.append({
                    'site': site,  # Use parent device's site
                    'hostname': '',
                    'parent_hostname': device_name,
                    'ip_address': '',
                    'position': module.get('position', 'Module'),
                    'model': module_model,
                    'serial_number': module.get('serial_number', ''),
                    'port_location': module.get('description', ''),  # Module description in port_location
                    'vendor': 'Cisco',
                    'notes': '',  # Empty notes for modules
                    'end_of_sale': module_end_of_sale,
                    'end_of_support': module_end_of_support
                })
                
            # SFPs/Transceivers
            for sfp in components.get('transceivers', []):
                # Add EoS/EoL data for SFPs
                sfp_model = sfp.get('model', 'SFP')
                sfp_end_of_sale, sfp_end_of_support = self.lookup_eol_data(sfp_model)
                
                csv_data.append({
                    'site': site,  # Use parent device's site
                    'hostname': '',
                    'parent_hostname': device_name,
                    'ip_address': '',
                    'position': sfp.get('position', 'SFP'),
                    'model': sfp_model,
                    'serial_number': sfp.get('serial_number', ''),
                    'port_location': sfp.get('port', ''),
                    'vendor': sfp.get('vendor', 'Unknown'),
                    'notes': sfp.get('description', ''),
                    'end_of_sale': sfp_end_of_sale,
                    'end_of_support': sfp_end_of_support
                })
        
        logging.info(f"Generated {len(csv_data)} rows for database import")
        
        # Save backup CSV and generate site-grouped version
        csv_file = f"{self.temp_dir}/inventory_processed_{self.timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['site', 'hostname', 'parent_hostname', 'ip_address', 'position', 'model', 
                         'serial_number', 'port_location', 'vendor', 'notes', 'end_of_sale', 'end_of_support']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        logging.info(f"Saved backup CSV to {csv_file}")
        
        # Generate site-grouped CSV
        self.generate_site_grouped_csv(csv_data)
        
        return csv_data
        
    def generate_site_grouped_csv(self, csv_data):
        """Generate site-grouped CSV maintaining hierarchical structure"""
        logging.info("="*60)
        logging.info("STEP 6A: Generate Site-Grouped CSV")
        logging.info("="*60)
        
        # Group devices by site while preserving hierarchy
        device_groups = {}  # site -> list of device groups (master + subs)
        
        current_group = []
        current_site = None
        
        for row in csv_data:
            hostname = row.get('hostname', '')
            site = row.get('site', 'Unknown')
            
            if hostname:  # This is a master device
                # Save previous group if it exists
                if current_group and current_site:
                    if current_site not in device_groups:
                        device_groups[current_site] = []
                    device_groups[current_site].append(current_group)
                
                # Start new group
                current_site = site
                current_group = [row]
            else:  # This is a sub-device
                current_group.append(row)
        
        # Save the last group
        if current_group and current_site:
            if current_site not in device_groups:
                device_groups[current_site] = []
            device_groups[current_site].append(current_group)
        
        # Write grouped CSV
        grouped_csv_file = f"{self.base_dir}/inventory_ultimate_final.csv"
        
        with open(grouped_csv_file, 'w', newline='') as f:
            fieldnames = ['site', 'hostname', 'ip_address', 'position', 'model', 'serial_number', 
                         'port_location', 'vendor', 'notes', 'end_of_sale', 'end_of_support']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write devices grouped by site
            for site in self.site_order:
                if site in device_groups:
                    for device_group in device_groups[site]:
                        for row in device_group:
                            # Remove parent_hostname for final CSV (not needed for web display)
                            output_row = {k: v for k, v in row.items() if k != 'parent_hostname'}
                            writer.writerow(output_row)
        
        # Log site distribution
        logging.info("Site-grouped CSV generated:")
        for site in self.site_order:
            if site in device_groups:
                total_devices = sum(len(group) for group in device_groups[site])
                master_count = len(device_groups[site])
                sub_count = total_devices - master_count
                logging.info(f"  {site}: {master_count} master devices, {sub_count} sub-devices")
        
        logging.info(f"Site-grouped CSV saved to: {grouped_csv_file}")
        
    def import_to_database(self, csv_data):
        """Import processed data to inventory_web_format table"""
        logging.info("="*60)
        logging.info("STEP 7: Database Import")
        logging.info("="*60)
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            cursor.execute("BEGIN")
            
            # Clear existing data
            cursor.execute("DELETE FROM inventory_web_format")
            logging.info("Cleared existing inventory_web_format data")
            
            # Insert new data
            insert_query = """
            INSERT INTO inventory_web_format 
            (site, hostname, parent_hostname, ip_address, position, model, serial_number, port_location, vendor, notes, end_of_sale, end_of_support)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for row in csv_data:
                cursor.execute(insert_query, (
                    row['site'],
                    row['hostname'],
                    row['parent_hostname'],
                    row['ip_address'],
                    row['position'],
                    row['model'],
                    row['serial_number'],
                    row['port_location'],
                    row['vendor'],
                    row['notes'],
                    row['end_of_sale'] if row['end_of_sale'] else None,
                    row['end_of_support'] if row['end_of_support'] else None
                ))
            
            # Commit transaction
            cursor.execute("COMMIT")
            logging.info(f"Successfully imported {len(csv_data)} rows to inventory_web_format")
            
            # Verify FEX deduplication
            cursor.execute("""
                SELECT COUNT(DISTINCT serial_number) as unique_fex,
                       COUNT(*) as total_fex
                FROM inventory_web_format 
                WHERE position LIKE 'FEX%'
                AND serial_number IS NOT NULL 
                AND serial_number != ''
            """)
            
            result = cursor.fetchone()
            if result:
                unique_fex, total_fex = result
                if unique_fex == total_fex:
                    logging.info(f"✅ FEX deduplication verified: {unique_fex} unique FEX devices")
                else:
                    logging.warning(f"⚠️ FEX duplicates found: {total_fex} total, {unique_fex} unique")
            
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN parent_hostname = '' THEN 1 END) as parent_devices,
                    COUNT(CASE WHEN position LIKE 'FEX%' THEN 1 END) as fex_devices,
                    COUNT(CASE WHEN position = 'Module' OR position LIKE 'Module%' THEN 1 END) as modules,
                    COUNT(CASE WHEN position = 'SFP' OR position LIKE 'SFP%' THEN 1 END) as sfps,
                    COUNT(*) as total_rows
                FROM inventory_web_format
            """)
            
            stats = cursor.fetchone()
            if stats:
                parents, fex, modules, sfps, total = stats
                logging.info(f"Import Summary:")
                logging.info(f"  - Parent devices: {parents}")
                logging.info(f"  - FEX devices: {fex}")
                logging.info(f"  - Modules: {modules}")
                logging.info(f"  - SFPs: {sfps}")
                logging.info(f"  - Total rows: {total}")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logging.error(f"Database import failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
            
    def cleanup(self):
        """Clean up temporary files"""
        logging.info("="*60)
        logging.info("Cleanup")
        logging.info("="*60)
        
        try:
            # Keep temp files for 7 days for troubleshooting
            import shutil
            import glob
            
            # Remove temp directories older than 7 days
            old_dirs = glob.glob('/tmp/inventory_pipeline_*')
            for old_dir in old_dirs:
                try:
                    # Extract timestamp from directory name
                    dir_timestamp = old_dir.split('_')[-1]
                    dir_date = datetime.strptime(dir_timestamp, '%Y%m%d_%H%M%S')
                    
                    if (datetime.now() - dir_date).days > 7:
                        shutil.rmtree(old_dir)
                        logging.info(f"Removed old temp directory: {old_dir}")
                except Exception as e:
                    logging.warning(f"Could not remove {old_dir}: {e}")
                    
        except Exception as e:
            logging.warning(f"Cleanup error: {e}")
            
    def run(self):
        """Run the complete pipeline"""
        start_time = datetime.now()
        
        try:
            logging.info("="*60)
            logging.info("Starting Nightly Inventory Processing Pipeline")
            logging.info(f"Timestamp: {self.timestamp}")
            logging.info("="*60)
            
            # Step 1: Check SNMP collection status
            self.run_snmp_collection()
            
            # Step 2: Export from database
            inventory = self.export_from_database()
            if not inventory:
                logging.error("No inventory data to process")
                return False
                
            # Step 3: Enhance models
            inventory = self.enhance_models(inventory)
            
            # Step 4: Identify duplicates
            duplicates = self.identify_vpc_duplicates(inventory)
            
            # Step 5: Apply deduplication
            if duplicates:
                inventory = self.apply_deduplication(inventory, duplicates)
            else:
                logging.info("No VPC duplicates found")
            
            # Step 6: Generate CSV format
            csv_data = self.generate_csv_format(inventory)
            
            # Step 7: Import to database
            self.import_to_database(csv_data)
            
            # Cleanup old temp files
            self.cleanup()
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logging.info("="*60)
            logging.info("Pipeline completed successfully!")
            logging.info(f"Execution time: {execution_time:.2f} seconds")
            logging.info("="*60)
            
            return True
            
        except Exception as e:
            logging.error(f"Pipeline failed: {e}", exc_info=True)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logging.info("="*60)
            logging.info("Pipeline FAILED!")
            logging.info(f"Execution time: {execution_time:.2f} seconds")
            logging.info("="*60)
            
            return False

def main():
    """Main entry point"""
    pipeline = InventoryPipeline()
    success = pipeline.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()