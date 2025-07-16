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
    
    def extract_fex_model(self, model_string, description=''):
        """Extract FEX model from model string or description"""
        # If already in correct format
        if model_string.startswith('N2K-'):
            return model_string
            
        # First try: model_name might have format: "Fabric Extender Module: 32x10GE, 8x10GE-N2K-C2232PP-10GE"
        if 'Fabric Extender' in model_string and '-N' in model_string:
            parts = model_string.split('-')
            for i, part in enumerate(parts):
                if part.startswith('N2K'):
                    return '-'.join(parts[i:])
        
        # Second try: Check description for Nexus model 
        import re
        if description:
            # Look for patterns like "Nexus2232PP-10GE" or "Nexus2248TP-1GE" or "Nexus2248"
            nexus_match = re.search(r'Nexus(\d+[A-Z0-9\-]*)', description)
            if nexus_match:
                nexus_model = nexus_match.group(1)
                # Handle cases like "Nexus2248" without suffix
                if nexus_model == '2248':
                    return 'N2K-C2248TP-1GE'
                elif nexus_model == '2232':
                    return 'N2K-C2232PP-10GE'
                # Nexus model maps directly to N2K-C prefix
                return f'N2K-C{nexus_model}'
        
        # Third try: Identify by port configuration
        if 'Fabric Extender' in model_string:
            if '48x1GE, 4x10GE' in model_string:
                return 'N2K-C2248TP-1GE'
            elif '32x10GE, 8x10GE' in model_string:
                return 'N2K-C2232PP-10GE'
            elif '16x10GE, 8x10GE' in model_string:
                return 'N2K-B22DELL-P'
        
        # If no N2K model found, return original
        return model_string
    
    def assign_site_from_ip(self, ip_address, hostname=''):
        """Assign site based on IP address ranges"""
        if not ip_address:
            # Fallback to hostname patterns if no IP
            hostname_lower = hostname.lower() if hostname else ''
            if any(x in hostname_lower for x in ['seattle', 'sea-']):
                return 'Equinix-Seattle'
            elif any(x in hostname_lower for x in ['alameda', 'ala-']):
                return 'AZ-Alameda-DC'
            elif any(x in hostname_lower for x in ['atl', 'atlanta']):
                return 'Focal-Point-ATL'
            elif any(x in hostname_lower for x in ['dal', 'dallas']):
                return 'Focal-Point-DAL'
            else:
                return 'AZ-Scottsdale-HQ-Corp'
        
        # IP-based assignment (correct schema)
        if ip_address.startswith('10.0.') or ip_address.startswith('172.16.'):
            return 'AZ-Scottsdale-HQ-Corp'
        elif ip_address.startswith('10.101.'):
            return 'AZ-Alameda-DC'
        elif ip_address.startswith('10.41.'):
            return 'AZ-Desert-Ridge'
        elif ip_address.startswith('10.42.'):
            return 'Focal-Point-DAL'
        elif ip_address.startswith('10.43.'):
            return 'Focal-Point-ATL'
        elif ip_address.startswith('10.44.'):
            return 'Equinix-Seattle'
        elif ip_address.startswith('192.168.'):
            # 192.168 appears in both Alameda and Scottsdale - use hostname as tiebreaker
            hostname_lower = hostname.lower() if hostname else ''
            if 'ala' in hostname_lower or 'alameda' in hostname_lower:
                return 'AZ-Alameda-DC'
            else:
                return 'AZ-Scottsdale-HQ-Corp'
        else:
            # Default fallback
            return 'AZ-Scottsdale-HQ-Corp'
    
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
                if hostname and ('-ADMIN' in hostname or '-CORE' in hostname or '-EDGE' in hostname or '-PCI' in hostname):
                    # Remove domain suffix if present
                    hostname_base = hostname.split('.')[0]
                    # Extract base name including unit number (e.g., AL-7000-01, HQ-7000-02)
                    parts = hostname_base.split('-')
                    if len(parts) >= 3:
                        base_name = '-'.join(parts[:3])  # e.g., AL-7000-01, HQ-7000-02
                    else:
                        base_name = hostname_base
                    
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
            
            # Second pass: process devices grouped by site
            # First, organize all devices by site
            devices_by_site = {}
            for base_name, vdc_list in vdc_groups.items():
                # Get primary VDC
                primary_vdc = None
                for vdc in vdc_list:
                    if '-ADMIN' in vdc['hostname']:
                        primary_vdc = vdc
                        break
                if not primary_vdc:
                    primary_vdc = vdc_list[0]
                
                # Determine site
                site = self.assign_site_from_ip(str(primary_vdc['ip_address']), primary_vdc['hostname'])
                
                if site not in devices_by_site:
                    devices_by_site[site] = []
                devices_by_site[site].append((base_name, vdc_list))
            
            # Process devices by site
            for site in sorted(devices_by_site.keys()):
                for base_name, vdc_list in sorted(devices_by_site[site]):
                    # For VDCs, use ADMIN context as primary
                    primary_vdc = None
                    for vdc in vdc_list:
                        if '-ADMIN' in vdc['hostname']:
                            primary_vdc = vdc
                            break
                    if not primary_vdc:
                        primary_vdc = vdc_list[0]
                    
                    # Site is already determined above
                    
                    try:
                        components = json.loads(primary_vdc['components']) if isinstance(primary_vdc['components'], str) else primary_vdc['components']
                    except:
                        logging.error(f"Failed to parse JSON for {primary_vdc['hostname']}")
                        continue
                    
                    if not components:
                        components = {}
                    
                    chassis_list = components.get('chassis', [])
                    if not chassis_list:
                        # For devices without chassis data (like ASR routers), create a basic entry
                        device_entries = []
                        device_entries.append({
                            'site': site,
                            'hostname': primary_vdc['hostname'],
                            'ip_address': str(primary_vdc['ip_address']),
                            'position': 'Standalone',
                            'model': '',
                            'serial_number': '',
                            'port_location': '',
                            'vendor': '',
                            'notes': '',
                            'end_of_sale': '',
                            'end_of_support': ''
                        })
                        all_entries.extend(device_entries)
                        continue
                    
                    device_entries = []
                    
                    # Process chassis
                    chassis = chassis_list[0]
                    chassis_serial = self.clean_value(chassis.get('serial_number', ''))
                    chassis_model = self.clean_value(chassis.get('model_name', ''))
                    
                    # Check for duplicate serials
                    if chassis_serial and chassis_serial in self.seen_serials:
                        continue
                    
                    if chassis_serial:
                        self.seen_serials.add(chassis_serial)
                    
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
                    all_chassis = []
                    all_fex_units = []
                    
                    for vdc in vdc_list:
                        try:
                            vdc_components = json.loads(vdc['components']) if isinstance(vdc['components'], str) else vdc['components']
                            all_modules.extend(vdc_components.get('modules', []))
                            all_sfps.extend(vdc_components.get('transceivers', []))
                            # Also get chassis entries for FEX
                            all_chassis.extend(vdc_components.get('chassis', []))
                            # Get FEX units which have the correct serials
                            all_fex_units.extend(vdc_components.get('fex_units', []))
                        except:
                            continue
                    
                    # Process FEX units (these have the correct SSI serials)
                    for fex_unit in all_fex_units:
                        # FEX units ARE the chassis entries with SSI serials
                        fex_name = fex_unit.get('name', '')
                        fex_desc = fex_unit.get('description', '')
                        fex_model = self.clean_value(fex_unit.get('model_name', ''))
                        fex_serial = self.clean_value(fex_unit.get('serial_number', ''))
                        
                        # Skip empty models
                        if not fex_model:
                            continue
                            
                        # Skip duplicate serials
                        if fex_serial and fex_serial in self.seen_serials:
                            continue
                            
                        if fex_serial:
                            self.seen_serials.add(fex_serial)
                        
                        # Extract FEX number from name like "Fex-105 Nexus2248 Chassis"
                        fex_match = re.search(r'Fex-(\d+)', fex_name)
                        if fex_match:
                            position = f'FEX-{fex_match.group(1)}'
                        else:
                            position = 'FEX'
                        
                        # Extract proper model from description
                        if 'Nexus' in fex_desc:
                            fex_model = self.extract_fex_model(fex_model, fex_desc)
                        
                        device_entries.append({
                            'site': site,
                            'hostname': '',
                            'ip_address': '',
                            'position': position,
                            'model': fex_model,
                            'serial_number': fex_serial,
                            'port_location': fex_name,
                            'vendor': 'Cisco',
                            'notes': '',
                            'end_of_sale': '',
                            'end_of_support': ''
                        })
                    
                    # Process FEX chassis entries (class 3 with Fex in name) - OLD METHOD, SKIP IF FEX UNITS EXIST
                    if not all_fex_units:  # Only use old method if no fex_units found
                        for chassis in all_chassis[1:]:  # Skip first chassis (main device)
                            chassis_name = chassis.get('name', '')
                            chassis_desc = chassis.get('description', '')
                            
                            if 'Fex-' in chassis_name and 'Nexus' in chassis_desc:
                                chassis_model = self.clean_value(chassis.get('model_name', ''))
                                chassis_serial = self.clean_value(chassis.get('serial_number', ''))
                                
                                # Skip empty models
                                if not chassis_model:
                                    continue
                                    
                                # Skip duplicate serials
                                if chassis_serial and chassis_serial in self.seen_serials:
                                    continue
                                    
                                if chassis_serial:
                                    self.seen_serials.add(chassis_serial)
                                
                                # Extract FEX number
                                fex_match = re.search(r'Fex-(\d+)', chassis_name)
                                if fex_match:
                                    position = f'FEX-{fex_match.group(1)}'
                                else:
                                    position = re.sub(r'^\s*Fex-', 'FEX-', chassis_name).strip()
                                
                                # Extract model from description if needed
                                if 'Fabric Extender' in chassis_model and 'Nexus' in chassis_desc:
                                    chassis_model = self.extract_fex_model(chassis_model, chassis_desc)
                                
                                device_entries.append({
                                    'site': site,
                                    'hostname': '',
                                    'ip_address': '',
                                    'position': position,
                                    'model': chassis_model,
                                    'serial_number': chassis_serial,
                                    'port_location': chassis_name,
                                    'vendor': 'Cisco',
                                    'notes': '',
                                    'end_of_sale': '',
                                    'end_of_support': ''
                                })
                    
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
                        
                        # Skip FEX modules if we have fex_units (to avoid duplicates)
                        if 'Fex-' in module_name and 'Fabric Extender' in module_desc and all_fex_units:
                            continue
                        
                        # Handle FEX
                        if 'Fex-' in module_name and 'Fabric Extender' in module_desc:
                            fex_match = re.search(r'Fex-(\d+)', module_name)
                            if fex_match:
                                position = f'FEX-{fex_match.group(1)}'
                            else:
                                position = re.sub(r'^\s*Fex-', 'FEX-', module_name).strip()
                            
                            if 'Fabric Extender' in module_model:
                                module_model = self.extract_fex_model(module_model, module_desc)
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