#!/usr/bin/env python3
"""
Enhanced SFP identification - maps Unspecified SFPs to proper model names
based on description and serial number patterns
"""
import json
import re

class SFPIdentifier:
    def __init__(self):
        # Map descriptions to likely model types
        self.description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',          # 1G multimode 850nm
            '1000BaseLX SFP': 'GLC-LX-SMD',          # 1G singlemode 1310nm
            '10/100/1000BaseTX SFP': 'GLC-T',       # 1G copper
            '1000BaseT SFP': 'GLC-T',               # 1G copper
            'SFP-10Gbase-SR': 'SFP-10G-SR',         # 10G multimode 850nm
            'SFP-10Gbase-LR': 'SFP-10G-LR',         # 10G singlemode 1310nm
            'SFP+ 10GBASE-SR': 'SFP-10G-SR',        # 10G multimode 850nm
            'SFP+ 10GBASE-LR': 'SFP-10G-LR',        # 10G singlemode 1310nm
        }
        
        # Serial number patterns to vendor mapping
        self.vendor_patterns = {
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
    
    def identify_sfp_model(self, description, model_name, serial_number):
        """Identify the actual SFP model based on available information"""
        
        # If we already have a good model name, keep it
        if model_name and model_name not in ['Unspecified', '""', '']:
            return model_name, None
        
        # Clean up serial number
        serial = serial_number.strip()
        
        # Identify vendor from serial prefix
        vendor = None
        for prefix, vendor_name in self.vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        # Map description to standard model
        base_model = None
        for desc_pattern, model in self.description_map.items():
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
                        base_model = 'GLC-SX-MM'
                    elif 'lx' in description.lower() or '1310' in description:
                        base_model = 'GLC-LX-SM'
                    elif 'tx' in description.lower() or 'baset' in description.lower():
                        base_model = 'GLC-T'
        
        # If we identified the type, add vendor suffix if third-party
        if base_model and vendor and vendor != 'Cisco':
            # Add -3P suffix for third-party
            final_model = f"{base_model}-3P"
        else:
            final_model = base_model or model_name
        
        return final_model, vendor
    
    def process_inventory_data(self, inventory_file):
        """Process inventory data and enhance SFP identification"""
        with open(inventory_file, 'r') as f:
            data = json.load(f)
        
        enhanced_count = 0
        
        for device in data:
            # Process transceivers
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
                    enhanced_count += 1
        
        return data, enhanced_count
    
    def generate_enhanced_csv(self, enhanced_data, output_file):
        """Generate CSV with enhanced SFP identification"""
        import csv
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'hostname', 'ip_address', 'position', 'model', 
                'serial_number', 'port_location', 'vendor'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for device in enhanced_data:
                hostname = device['hostname']
                ip = device['ip']
                chassis_list = device['physical_inventory']['chassis']
                
                # Handle chassis
                if len(chassis_list) > 1:
                    # First is Master
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Master',
                        'model': chassis_list[0]['model'],
                        'serial_number': chassis_list[0]['serial'],
                        'port_location': '',
                        'vendor': ''
                    })
                    
                    # Rest are Slaves
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
                
                # List SFPs with enhanced info
                for sfp in device['physical_inventory']['transceivers']:
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'SFP',
                        'model': sfp['model'],
                        'serial_number': sfp['serial'],
                        'port_location': sfp['name'],
                        'vendor': sfp.get('vendor', '')
                    })

def main():
    identifier = SFPIdentifier()
    
    # Process the inventory data
    print("Processing inventory data with enhanced SFP identification...")
    enhanced_data, count = identifier.process_inventory_data('/usr/local/bin/physical_inventory_stacks_output.json')
    
    print(f"Enhanced {count} SFP identifications")
    
    # Save enhanced data
    with open('/usr/local/bin/physical_inventory_enhanced.json', 'w') as f:
        json.dump(enhanced_data, f, indent=2)
    
    # Generate enhanced CSV
    identifier.generate_enhanced_csv(enhanced_data, '/usr/local/bin/inventory_enhanced.csv')
    print("Enhanced CSV saved to: /usr/local/bin/inventory_enhanced.csv")
    
    # Show some examples
    print("\n=== Sample Enhanced SFPs ===")
    sample_count = 0
    for device in enhanced_data:
        for sfp in device['physical_inventory']['transceivers']:
            if 'original_model' in sfp and sample_count < 10:
                print(f"{device['hostname']} - {sfp['name']}:")
                print(f"  Original: {sfp['original_model']}")
                print(f"  Enhanced: {sfp['model']}")
                if 'vendor' in sfp:
                    print(f"  Vendor: {sfp['vendor']}")
                sample_count += 1

if __name__ == "__main__":
    main()