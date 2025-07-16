#!/usr/bin/env python3
"""
Generate final CSV with ALL enhancements applied:
- Deduplicated serials
- FEX model extraction (N2K-C2232PP-10GE instead of generic)
- SFP identification (GLC-SX-MMD instead of Unspecified)
"""
import json
import csv
import re

class CompleteEnhancer:
    def __init__(self):
        # FEX patterns for model extraction
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE.*N2K-C2148T': 'N2K-C2148T-1GE',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',
        }
        
        # SFP description to model mapping
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
            'SFP+ 10GBASE-SR': 'SFP-10G-SR',
            'SFP+ 10GBASE-LR': 'SFP-10G-LR',
        }
        
        # SFP vendor patterns
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'OPM': 'OptoSpan',
            'AVD': 'Avago',
            'ECL': 'Eoptolink',
            'MTC': 'MikroTik',
        }
    
    def extract_fex_model(self, description, current_model):
        """Extract actual FEX model from description"""
        if '-N2K-' in current_model:
            match = re.search(r'(N2K-[A-Z0-9\-]+)', current_model)
            if match:
                return match.group(1)
        
        full_text = f"{description} {current_model}"
        
        for pattern, model in self.fex_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        if 'Fabric Extender' in description:
            # Try to extract from chassis name
            if 'Nexus2232' in description:
                return 'N2K-C2232PP-10GE'
            elif 'Nexus2248' in description:
                return 'N2K-C2248TP-1GE'
            elif 'Nexus2200DELL' in description:
                return 'N2K-B22DELL-P'
        
        return current_model
    
    def identify_sfp_model(self, description, model_name, serial_number):
        """Identify SFP model and vendor"""
        if model_name and model_name not in ['Unspecified', '""', '']:
            return model_name, None
        
        serial = serial_number.strip()
        
        # Identify vendor
        vendor = None
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        # Map description to model
        for desc_pattern, model in self.sfp_description_map.items():
            if desc_pattern.lower() in description.lower():
                return model, vendor
        
        return model_name, vendor

def generate_final_enhanced_csv():
    """Generate final CSV with all enhancements"""
    
    # Load deduplicated inventory
    try:
        with open('/usr/local/bin/Main/physical_inventory_deduplicated.json', 'r') as f:
            devices = json.load(f)
        print(f"Loaded deduplicated inventory with {len(devices)} devices")
    except FileNotFoundError:
        with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
            devices = json.load(f)
    
    enhancer = CompleteEnhancer()
    
    # Generate CSV
    with open('/usr/local/bin/Main/inventory_final_complete.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'position', 'model', 
            'serial_number', 'port_location', 'vendor', 'shared_with'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        stats = {
            'devices': 0,
            'components': 0,
            'fex_enhanced': 0,
            'sfp_enhanced': 0
        }
        
        for device in devices:
            hostname = device['hostname']
            ip = device['ip']
            chassis_list = device['physical_inventory']['chassis']
            
            if not chassis_list:
                continue
                
            stats['devices'] += 1
            
            # Handle chassis
            if len(chassis_list) > 1:
                main_chassis = chassis_list[0]
                if 'N5K' in main_chassis['model'] or 'N56' in main_chassis['model']:
                    # Parent switch
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Parent Switch',
                        'model': main_chassis['model'],
                        'serial_number': main_chassis['serial'],
                        'port_location': '',
                        'vendor': 'Cisco',
                        'shared_with': ''
                    })
                    stats['components'] += 1
                    
                    # FEX units with enhanced models
                    for i in range(1, len(chassis_list)):
                        fex = chassis_list[i]
                        fex_id = re.search(r'Fex-(\d+)', fex['name'])
                        fex_num = fex_id.group(1) if fex_id else str(100 + i)
                        
                        # Enhance FEX model
                        original_model = fex['model']
                        enhanced_model = enhancer.extract_fex_model(fex['description'], original_model)
                        if enhanced_model != original_model:
                            stats['fex_enhanced'] += 1
                        
                        shared = ', '.join(fex.get('shared_with', []))
                        
                        writer.writerow({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': enhanced_model,
                            'serial_number': fex['serial'],
                            'port_location': fex['name'],
                            'vendor': 'Cisco',
                            'shared_with': shared
                        })
                        stats['components'] += 1
                else:
                    # Regular stack
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Master',
                        'model': chassis_list[0]['model'],
                        'serial_number': chassis_list[0]['serial'],
                        'port_location': '',
                        'vendor': '',
                        'shared_with': ''
                    })
                    stats['components'] += 1
                    
                    for i in range(1, len(chassis_list)):
                        writer.writerow({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Slave',
                            'model': chassis_list[i]['model'],
                            'serial_number': chassis_list[i]['serial'],
                            'port_location': '',
                            'vendor': '',
                            'shared_with': ''
                        })
                        stats['components'] += 1
            else:
                # Single device
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Standalone',
                    'model': chassis_list[0]['model'],
                    'serial_number': chassis_list[0]['serial'],
                    'port_location': '',
                    'vendor': '',
                    'shared_with': ''
                })
                stats['components'] += 1
            
            # List modules
            for module in device['physical_inventory']['modules']:
                # Check if it's a FEX module
                original_model = module['model']
                enhanced_model = original_model
                if 'Fabric Extender' in module.get('description', ''):
                    enhanced_model = enhancer.extract_fex_model(module['description'], original_model)
                    if enhanced_model != original_model:
                        stats['fex_enhanced'] += 1
                
                shared = ', '.join(module.get('shared_with', []))
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': enhanced_model,
                    'serial_number': module['serial'],
                    'port_location': module['name'],
                    'vendor': '',
                    'shared_with': shared
                })
                stats['components'] += 1
            
            # List SFPs with enhancement
            for sfp in device['physical_inventory']['transceivers']:
                # Enhance SFP model
                original_model = sfp.get('model', 'Unknown')
                enhanced_model, vendor = enhancer.identify_sfp_model(
                    sfp.get('description', ''),
                    original_model,
                    sfp.get('serial', '')
                )
                if enhanced_model != original_model:
                    stats['sfp_enhanced'] += 1
                
                shared = ', '.join(sfp.get('shared_with', []))
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': enhanced_model,
                    'serial_number': sfp['serial'],
                    'port_location': sfp['name'],
                    'vendor': vendor or sfp.get('vendor', ''),
                    'shared_with': shared
                })
                stats['components'] += 1
    
    print(f"\nFinal enhanced inventory CSV generated:")
    print(f"  File: /usr/local/bin/Main/inventory_final_complete.csv")
    print(f"  Devices: {stats['devices']}")
    print(f"  Total components: {stats['components']}")
    print(f"  FEX models enhanced: {stats['fex_enhanced']}")
    print(f"  SFP models enhanced: {stats['sfp_enhanced']}")
    
    # Show samples
    print("\n=== Sample Enhanced Entries ===")
    
    print("\nFEX entries (first 5):")
    with open('/usr/local/bin/Main/inventory_final_complete.csv', 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if 'FEX' in row['position'] and count < 5:
                print(f"  {row['position']}: {row['model']} (was generic description)")
                count += 1
    
    print("\nEnhanced SFPs (first 5):")
    with open('/usr/local/bin/Main/inventory_final_complete.csv', 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if row['position'] == 'SFP' and row['model'] not in ['Unspecified', 'Unknown'] and count < 5:
                print(f"  {row['model']} - {row['vendor']} at {row['port_location']}")
                count += 1

if __name__ == "__main__":
    generate_final_enhanced_csv()