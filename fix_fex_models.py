#!/usr/bin/env python3
"""
Fix FEX model identification - extract actual model numbers from descriptions
"""
import json
import re
import csv

class FEXModelFixer:
    def __init__(self):
        # Map generic descriptions to expected FEX models
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE.*N2K-C2148T': 'N2K-C2148T-1GE',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',  # Default for 48x1G
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE', # Default for 32x10G
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',    # Default for 16x10G
        }
        
        # Also handle N5K line cards
        self.n5k_patterns = {
            r'N56-M24UP2Q': 'N56-M24UP2Q',
            r'N5K-C56128P': 'N5K-C56128P',
            r'N5K-C5010P-BF': 'N5K-C5010P-BF',
            r'N5K-C5020P-BF': 'N5K-C5020P-BF'
        }
    
    def extract_fex_model(self, description, current_model):
        """Extract the actual FEX model from description or model string"""
        # First check if model already contains the FEX model
        if '-N2K-' in current_model:
            # Extract just the N2K part
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
            # Try to extract port configuration
            port_match = re.search(r'(\d+x\d+G[BE].*\d+x\d+G[BE])', description)
            if port_match:
                return f"FEX-{port_match.group(1)}"
        
        return current_model
    
    def process_inventory(self, input_file):
        """Process inventory and fix FEX models"""
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        fixed_count = 0
        
        for device in data:
            # Fix chassis models if they're FEX
            for chassis in device['physical_inventory']['chassis']:
                if 'Fabric Extender' in chassis['description'] or 'Fabric Extender' in chassis['model']:
                    original = chassis['model']
                    chassis['model'] = self.extract_fex_model(chassis['description'], chassis['model'])
                    if chassis['model'] != original:
                        fixed_count += 1
            
            # Fix module models
            for module in device['physical_inventory']['modules']:
                if 'Fabric Extender' in module['description'] or 'Fabric Extender' in module['model']:
                    original = module['model']
                    module['model'] = self.extract_fex_model(module['description'], module['model'])
                    if module['model'] != original:
                        fixed_count += 1
        
        return data, fixed_count
    
    def generate_fixed_csv(self, data, output_file):
        """Generate CSV with fixed FEX models"""
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
                    # Check if this is a parent switch with FEX
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
    fixer = FEXModelFixer()
    
    # Process enhanced inventory
    print("Processing inventory to fix FEX models...")
    try:
        # Try enhanced inventory first
        fixed_data, count = fixer.process_inventory('/usr/local/bin/physical_inventory_enhanced.json')
    except (PermissionError, FileNotFoundError):
        try:
            # Try stacks output in main location
            print("Trying stacks output in main location...")
            fixed_data, count = fixer.process_inventory('/usr/local/bin/physical_inventory_stacks_output.json')
        except (PermissionError, FileNotFoundError):
            # Fall back to Main directory
            print("Using copy in Main directory...")
            fixed_data, count = fixer.process_inventory('/usr/local/bin/Main/physical_inventory_stacks_output.json')
    print(f"Fixed {count} FEX model identifications")
    
    # Save fixed data
    with open('/usr/local/bin/Main/physical_inventory_fixed.json', 'w') as f:
        json.dump(fixed_data, f, indent=2)
    
    # Generate final CSV
    fixer.generate_fixed_csv(fixed_data, '/usr/local/bin/Main/inventory_final.csv')
    print("Final CSV saved to: /usr/local/bin/Main/inventory_final.csv")
    
    # Show examples
    print("\n=== Sample FEX Fixes ===")
    for device in fixed_data:
        if any('N2K-' in c['model'] for c in device['physical_inventory']['chassis']):
            print(f"\n{device['hostname']}:")
            for chassis in device['physical_inventory']['chassis']:
                if 'N2K-' in chassis['model'] or 'FEX' in str(chassis):
                    print(f"  {chassis['name']}: {chassis['model']} (Serial: {chassis['serial']})")
            break

if __name__ == "__main__":
    main()