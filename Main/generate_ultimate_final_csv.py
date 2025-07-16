#!/usr/bin/env python3
"""
Generate the ultimate final CSV with:
- VDC consolidation (7K devices appear once)
- No duplicate serials
- FEX model extraction
- SFP identification
"""
import json
import csv
import re

class FinalEnhancer:
    def __init__(self):
        # FEX patterns
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',
        }
        
        # SFP mappings
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
        }
        
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'MTC': 'MikroTik',
        }
    
    def extract_fex_model(self, description, current_model):
        """Extract FEX model"""
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

def generate_ultimate_final():
    """Generate the final CSV with all enhancements"""
    
    # Load consolidated inventory (with VDCs merged)
    try:
        with open('/usr/local/bin/Main/physical_inventory_consolidated.json', 'r') as f:
            devices = json.load(f)
        print(f"Loaded consolidated inventory with {len(devices)} devices")
    except FileNotFoundError:
        print("Consolidated file not found, using deduplicated...")
        with open('/usr/local/bin/Main/physical_inventory_deduplicated.json', 'r') as f:
            devices = json.load(f)
    
    enhancer = FinalEnhancer()
    
    # Track all serials to ensure no duplicates
    seen_serials = set()
    
    with open('/usr/local/bin/Main/inventory_ultimate_final.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'position', 'model', 
            'serial_number', 'port_location', 'vendor', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        stats = {
            'devices': 0,
            'components': 0,
            'duplicates_skipped': 0,
            'fex_enhanced': 0,
            'sfp_enhanced': 0
        }
        
        for device in devices:
            hostname = device['hostname']
            ip = device['ip']
            physical_inv = device['physical_inventory']
            
            # Get VDC notes if applicable
            notes = ""
            if device.get('vdc_info', {}).get('is_vdc'):
                vdc_list = device['vdc_info']['vdc_names']
                # Clean up the list to show unique VDC types
                vdc_types = set()
                for vdc in vdc_list:
                    if '-ADMIN' in vdc:
                        vdc_types.add('ADMIN')
                    elif '-CORE' in vdc:
                        vdc_types.add('CORE')
                    elif '-EDGE' in vdc:
                        vdc_types.add('EDGE')
                    elif '-PCI' in vdc:
                        vdc_types.add('PCI')
                notes = f"VDCs: {', '.join(sorted(vdc_types))}"
            
            chassis_list = physical_inv.get('chassis', [])
            if not chassis_list:
                continue
            
            stats['devices'] += 1
            
            # Handle chassis
            if len(chassis_list) > 1 and ('N5K' in chassis_list[0].get('model', '') or 
                                          'N56' in chassis_list[0].get('model', '')):
                # N5K with FEX
                main_chassis = chassis_list[0]
                
                # Check for duplicate
                if main_chassis['serial'] in seen_serials:
                    stats['duplicates_skipped'] += 1
                    continue
                seen_serials.add(main_chassis['serial'])
                
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Parent Switch',
                    'model': main_chassis['model'],
                    'serial_number': main_chassis['serial'],
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': notes
                })
                stats['components'] += 1
                
                # FEX units
                for i in range(1, len(chassis_list)):
                    fex = chassis_list[i]
                    
                    if fex['serial'] in seen_serials:
                        stats['duplicates_skipped'] += 1
                        continue
                    seen_serials.add(fex['serial'])
                    
                    fex_id = re.search(r'Fex-(\d+)', fex['name'])
                    fex_num = fex_id.group(1) if fex_id else str(100 + i)
                    
                    # Enhance FEX model
                    original = fex['model']
                    enhanced = enhancer.extract_fex_model(fex['description'], original)
                    if enhanced != original:
                        stats['fex_enhanced'] += 1
                    
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': f'FEX-{fex_num}',
                        'model': enhanced,
                        'serial_number': fex['serial'],
                        'port_location': fex['name'],
                        'vendor': 'Cisco',
                        'notes': ''
                    })
                    stats['components'] += 1
            else:
                # Single chassis or stack
                main_chassis = chassis_list[0]
                
                if main_chassis['serial'] in seen_serials:
                    stats['duplicates_skipped'] += 1
                    continue
                seen_serials.add(main_chassis['serial'])
                
                position = 'Master' if len(chassis_list) > 1 else 'Standalone'
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': position,
                    'model': main_chassis['model'],
                    'serial_number': main_chassis['serial'],
                    'port_location': '',
                    'vendor': 'Cisco' if '7K' in main_chassis['model'] else '',
                    'notes': notes
                })
                stats['components'] += 1
                
                # Additional stack members
                for i in range(1, len(chassis_list)):
                    chassis = chassis_list[i]
                    
                    if chassis['serial'] in seen_serials:
                        stats['duplicates_skipped'] += 1
                        continue
                    seen_serials.add(chassis['serial'])
                    
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'Slave',
                        'model': chassis['model'],
                        'serial_number': chassis['serial'],
                        'port_location': '',
                        'vendor': '',
                        'notes': ''
                    })
                    stats['components'] += 1
            
            # Modules
            for module in physical_inv.get('modules', []):
                if module['serial'] in seen_serials:
                    stats['duplicates_skipped'] += 1
                    continue
                seen_serials.add(module['serial'])
                
                # Check for FEX module
                model = module['model']
                if 'Fabric Extender' in module.get('description', ''):
                    enhanced = enhancer.extract_fex_model(module['description'], model)
                    if enhanced != model:
                        stats['fex_enhanced'] += 1
                        model = enhanced
                
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': model,
                    'serial_number': module['serial'],
                    'port_location': module['name'],
                    'vendor': '',
                    'notes': ''
                })
                stats['components'] += 1
            
            # SFPs (sample - not all)
            sfp_count = 0
            for sfp in physical_inv.get('transceivers', []):
                if sfp_count >= 10:  # Limit SFPs per device for readability
                    break
                
                if sfp['serial'] in seen_serials:
                    stats['duplicates_skipped'] += 1
                    continue
                seen_serials.add(sfp['serial'])
                
                # Enhance SFP
                original = sfp.get('model', 'Unknown')
                enhanced, vendor = enhancer.identify_sfp(
                    sfp.get('description', ''),
                    original,
                    sfp.get('serial', '')
                )
                if enhanced != original:
                    stats['sfp_enhanced'] += 1
                
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': enhanced,
                    'serial_number': sfp['serial'],
                    'port_location': sfp['name'],
                    'vendor': vendor or '',
                    'notes': ''
                })
                stats['components'] += 1
                sfp_count += 1
    
    print(f"\nUltimate final CSV generated:")
    print(f"  File: /usr/local/bin/Main/inventory_ultimate_final.csv")
    print(f"  Devices: {stats['devices']}")
    print(f"  Components: {stats['components']}")
    print(f"  Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"  FEX enhanced: {stats['fex_enhanced']}")
    print(f"  SFP enhanced: {stats['sfp_enhanced']}")
    
    # Show sample
    print("\n=== Sample entries ===")
    with open('/usr/local/bin/Main/inventory_ultimate_final.csv', 'r') as f:
        for i, line in enumerate(f):
            if i < 20:
                print(f"  {line.strip()}")

if __name__ == "__main__":
    generate_ultimate_final()