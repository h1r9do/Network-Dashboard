#!/usr/bin/env python3
"""
Complete inventory enhancement - combines FEX model fixes and SFP identification
"""
import json
import re
import csv

class CompleteInventoryEnhancer:
    def __init__(self):
        # FEX patterns for model extraction
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE.*N2K-C2148T': 'N2K-C2148T-1GE',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',  # Default for 48x1G
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE', # Default for 32x10G
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',    # Default for 16x10G
        }
        
        # N5K line cards
        self.n5k_patterns = {
            r'N56-M24UP2Q': 'N56-M24UP2Q',
            r'N5K-C56128P': 'N5K-C56128P',
            r'N5K-C5010P-BF': 'N5K-C5010P-BF',
            r'N5K-C5020P-BF': 'N5K-C5020P-BF'
        }
        
        # SFP description to model mapping
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',          # 1G multimode 850nm
            '1000BaseLX SFP': 'GLC-LX-SMD',          # 1G singlemode 1310nm
            '10/100/1000BaseTX SFP': 'GLC-T',       # 1G copper
            '1000BaseT SFP': 'GLC-T',               # 1G copper
            'SFP-10Gbase-SR': 'SFP-10G-SR',         # 10G multimode 850nm
            'SFP-10Gbase-LR': 'SFP-10G-LR',         # 10G singlemode 1310nm
            'SFP+ 10GBASE-SR': 'SFP-10G-SR',        # 10G multimode 850nm
            'SFP+ 10GBASE-LR': 'SFP-10G-LR',        # 10G singlemode 1310nm
        }
        
        # SFP vendor identification by serial prefix
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago', 
            'FNS': 'Finisar',
            'OPM': 'OptoSpan',
            'ACP': 'Accedian',
            'AVD': 'Avago',
            'ECL': 'Eoptolink',
            'SPC': 'SourcePhotonics',
            'MTC': 'MikroTik',
            'JFQ': 'JDSU/Viavi',
            'AVP': 'Avago',
            'AVM': 'Avago'
        }
    
    def extract_fex_model(self, description, current_model):
        """Extract the actual FEX model from description or model string"""
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
        
        # Check for N5K patterns
        for pattern, model in self.n5k_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        # If it's a Fabric Extender but no specific model found, return cleaned version
        if 'Fabric Extender' in description:
            port_match = re.search(r'(\d+x\d+G[BE].*\d+x\d+G[BE])', description)
            if port_match:
                return f"FEX-{port_match.group(1)}"
        
        return current_model
    
    def identify_sfp_model(self, description, model_name, serial_number):
        """Identify the actual SFP model based on available information"""
        
        # If we already have a good model name, keep it
        if model_name and model_name not in ['Unspecified', '""', '']:
            return model_name, None
        
        # Clean up serial number
        serial = serial_number.strip()
        
        # Identify vendor from serial prefix
        vendor = None
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        # Map description to standard model
        base_model = None
        for desc_pattern, model in self.sfp_description_map.items():
            if desc_pattern.lower() in description.lower():
                base_model = model
                break
        
        if not base_model:
            # Try to extract info from description
            if 'sfp' in description.lower():
                if '10g' in description.lower() or '10000' in description:
                    if 'sr' in description.lower() or '850' in description:
                        base_model = 'SFP-10G-SR'
                    elif 'lr' in description.lower() or '1310' in description:
                        base_model = 'SFP-10G-LR'
                elif '1g' in description.lower() or '1000' in description:
                    if 'sx' in description.lower() or '850' in description:
                        base_model = 'GLC-SX-MMD'
                    elif 'lx' in description.lower() or '1310' in description:
                        base_model = 'GLC-LX-SMD'
                    elif 'tx' in description.lower() or 'baset' in description.lower():
                        base_model = 'GLC-T'
        
        # Add vendor suffix for third-party if needed
        if base_model and vendor and vendor != 'Cisco':
            # For common third-party vendors, keep standard naming
            if vendor in ['Avago', 'Finisar']:
                final_model = base_model
            else:
                final_model = f"{base_model}-3P"
        else:
            final_model = base_model or model_name
        
        return final_model, vendor
    
    def process_inventory(self, input_file):
        """Process inventory and enhance both FEX and SFP identification"""
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        fex_count = 0
        sfp_count = 0
        
        for device in data:
            # Fix chassis models if they're FEX
            for chassis in device['physical_inventory']['chassis']:
                if 'Fabric Extender' in chassis['description'] or 'Fabric Extender' in chassis['model']:
                    original = chassis['model']
                    chassis['model'] = self.extract_fex_model(chassis['description'], chassis['model'])
                    if chassis['model'] != original:
                        fex_count += 1
            
            # Fix module models
            for module in device['physical_inventory']['modules']:
                if 'Fabric Extender' in module['description'] or 'Fabric Extender' in module['model']:
                    original = module['model']
                    module['model'] = self.extract_fex_model(module['description'], module['model'])
                    if module['model'] != original:
                        fex_count += 1
            
            # Process transceivers/SFPs
            for sfp in device['physical_inventory']['transceivers']:
                original_model = sfp['model']
                enhanced_model, vendor = self.identify_sfp_model(
                    sfp['description'],
                    sfp['model'],
                    sfp['serial']
                )
                
                if enhanced_model != original_model:
                    sfp['original_model'] = original_model
                    sfp['model'] = enhanced_model
                    if vendor:
                        sfp['vendor'] = vendor
                    sfp_count += 1
        
        return data, fex_count, sfp_count
    
    def generate_final_csv(self, data, output_file):
        """Generate CSV with all enhancements"""
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'hostname', 'ip_address', 'position', 'model', 
                'serial_number', 'port_location', 'vendor'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for device in data:
                hostname = device['hostname']
                ip = device['ip']
                chassis_list = device['physical_inventory']['chassis']
                
                # Handle chassis - including FEX as chassis
                if len(chassis_list) > 1:
                    # For N5K/N56K, first is main chassis, rest are FEX
                    main_chassis = chassis_list[0]
                    if 'N5K' in main_chassis['model'] or 'N56' in main_chassis['model']:
                        # Main switch
                        writer.writerow({
                            'hostname': hostname,
                            'ip_address': ip,
                            'position': 'Parent Switch',
                            'model': main_chassis['model'],
                            'serial_number': main_chassis['serial'],
                            'port_location': '',
                            'vendor': 'Cisco'
                        })
                        
                        # FEX units
                        for i in range(1, len(chassis_list)):
                            fex = chassis_list[i]
                            fex_id = re.search(r'Fex-(\d+)', fex['name'])
                            fex_num = fex_id.group(1) if fex_id else str(100 + i)
                            writer.writerow({
                                'hostname': '',
                                'ip_address': '',
                                'position': f'FEX-{fex_num}',
                                'model': fex['model'],
                                'serial_number': fex['serial'],
                                'port_location': fex['name'],
                                'vendor': 'Cisco'
                            })
                    else:
                        # Regular stack
                        writer.writerow({
                            'hostname': hostname,
                            'ip_address': ip,
                            'position': 'Master',
                            'model': chassis_list[0]['model'],
                            'serial_number': chassis_list[0]['serial'],
                            'port_location': '',
                            'vendor': ''
                        })
                        
                        for i in range(1, len(chassis_list)):
                            writer.writerow({
                                'hostname': '',
                                'ip_address': '',
                                'position': 'Slave',
                                'model': chassis_list[i]['model'],
                                'serial_number': chassis_list[i]['serial'],
                                'port_location': '',
                                'vendor': ''
                            })
                else:
                    if chassis_list:
                        writer.writerow({
                            'hostname': hostname,
                            'ip_address': ip,
                            'position': 'Standalone',
                            'model': chassis_list[0]['model'],
                            'serial_number': chassis_list[0]['serial'],
                            'port_location': '',
                            'vendor': ''
                        })
                
                # List modules
                for module in device['physical_inventory']['modules']:
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'Module',
                        'model': module['model'],
                        'serial_number': module['serial'],
                        'port_location': module['name'],
                        'vendor': ''
                    })
                
                # List SFPs
                for sfp in device['physical_inventory']['transceivers']:
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'SFP',
                        'model': sfp.get('model', 'Unknown'),
                        'serial_number': sfp['serial'],
                        'port_location': sfp['name'],
                        'vendor': sfp.get('vendor', '')
                    })

def main():
    enhancer = CompleteInventoryEnhancer()
    
    # Process inventory
    print("Processing inventory with complete enhancements...")
    enhanced_data, fex_count, sfp_count = enhancer.process_inventory(
        '/usr/local/bin/Main/physical_inventory_stacks_output.json'
    )
    
    print(f"Enhanced {fex_count} FEX model identifications")
    print(f"Enhanced {sfp_count} SFP model identifications")
    
    # Save enhanced data
    with open('/usr/local/bin/Main/physical_inventory_complete.json', 'w') as f:
        json.dump(enhanced_data, f, indent=2)
    
    # Generate final CSV
    enhancer.generate_final_csv(enhanced_data, '/usr/local/bin/Main/inventory_complete.csv')
    print("Complete CSV saved to: /usr/local/bin/Main/inventory_complete.csv")
    
    # Show examples
    print("\n=== Sample Enhancements ===")
    
    # Show FEX examples
    print("\nFEX Models:")
    fex_shown = 0
    for device in enhanced_data:
        for chassis in device['physical_inventory']['chassis']:
            if 'N2K-' in chassis['model'] and fex_shown < 3:
                print(f"  {device['hostname']} - {chassis['name']}: {chassis['model']}")
                fex_shown += 1
    
    # Show SFP examples
    print("\nEnhanced SFPs:")
    sfp_shown = 0
    for device in enhanced_data:
        for sfp in device['physical_inventory']['transceivers']:
            if 'original_model' in sfp and sfp_shown < 5:
                print(f"  {device['hostname']} - {sfp['name']}:")
                print(f"    Original: {sfp['original_model']}")
                print(f"    Enhanced: {sfp['model']}")
                if 'vendor' in sfp:
                    print(f"    Vendor: {sfp['vendor']}")
                sfp_shown += 1

if __name__ == "__main__":
    main()