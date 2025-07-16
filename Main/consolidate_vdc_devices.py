#!/usr/bin/env python3
"""
Consolidate Nexus 7K VDC devices into single entries
All VDCs (ADMIN, CORE, EDGE, PCI) are the same physical device
"""
import json
import re
from collections import defaultdict

def consolidate_vdc_devices():
    """Consolidate VDC devices into single entries"""
    
    # Load inventory
    with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
        devices = json.load(f)
    
    print(f"Original device count: {len(devices)}")
    
    # Group devices by base name (without VDC suffix)
    device_groups = defaultdict(list)
    
    for device in devices:
        hostname = device['hostname']
        
        # Check if this is a VDC device
        vdc_match = re.match(r'^(.*?-7\d{3}-\d{2})-(ADMIN|CORE|EDGE|PCI)(?:\..*)?$', hostname)
        if vdc_match:
            base_name = vdc_match.group(1)
            vdc_type = vdc_match.group(2)
            device['vdc_type'] = vdc_type
            device_groups[base_name].append(device)
        else:
            # Not a VDC device, keep as-is
            device_groups[hostname] = [device]
    
    # Consolidate VDC devices
    consolidated_devices = []
    vdc_consolidation_count = 0
    
    for base_name, group in device_groups.items():
        if len(group) > 1:
            # This is a VDC group - consolidate
            print(f"\nConsolidating {base_name} ({len(group)} VDCs)")
            
            # Find the CORE VDC or use first one
            core_device = next((d for d in group if d.get('vdc_type') == 'CORE'), group[0])
            
            # Use CORE device as base
            consolidated = {
                'hostname': f"{base_name}-CORE",
                'ip': core_device['ip'],
                'device_type': core_device.get('device_type', ''),
                'physical_inventory': core_device['physical_inventory'],
                'summary': core_device['summary']
            }
            
            # Collect all VDC names for reference
            vdc_names = [d['hostname'] for d in group]
            consolidated['vdc_info'] = {
                'is_vdc': True,
                'vdc_count': len(group),
                'vdc_names': vdc_names,
                'consolidated_from': ', '.join(vdc_names)
            }
            
            # Update chassis to show it represents all VDCs
            if consolidated['physical_inventory']['chassis']:
                main_chassis = consolidated['physical_inventory']['chassis'][0]
                main_chassis['shared_with'] = [d['hostname'] for d in group if d['hostname'] != consolidated['hostname']]
            
            consolidated_devices.append(consolidated)
            vdc_consolidation_count += 1
            
            # Show what was consolidated
            for d in group:
                print(f"  - {d['hostname']} ({d['ip']})")
        else:
            # Single device, keep as-is
            consolidated_devices.append(group[0])
    
    print(f"\nConsolidated {vdc_consolidation_count} VDC groups")
    print(f"Final device count: {len(consolidated_devices)}")
    
    # Now remove any remaining duplicates based on serial numbers
    seen_serials = set()
    final_devices = []
    
    for device in consolidated_devices:
        # Check if we've seen the main chassis serial
        chassis_list = device['physical_inventory']['chassis']
        if chassis_list:
            main_serial = chassis_list[0]['serial']
            
            if main_serial in seen_serials:
                print(f"Skipping duplicate device {device['hostname']} (serial {main_serial} already seen)")
                continue
            
            seen_serials.add(main_serial)
        
        final_devices.append(device)
    
    print(f"\nFinal device count after duplicate removal: {len(final_devices)}")
    
    # Save consolidated inventory
    with open('/usr/local/bin/Main/physical_inventory_consolidated.json', 'w') as f:
        json.dump(final_devices, f, indent=2)
    
    # Show summary of changes
    print("\n=== Consolidation Summary ===")
    print(f"Original devices: {len(devices)}")
    print(f"After VDC consolidation: {len(consolidated_devices)}")
    print(f"After duplicate removal: {len(final_devices)}")
    print(f"Total removed: {len(devices) - len(final_devices)}")
    
    return final_devices

def generate_consolidated_csv(devices):
    """Generate CSV from consolidated devices"""
    import csv
    
    with open('/usr/local/bin/Main/inventory_consolidated_final.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'position', 'model', 
            'serial_number', 'port_location', 'vendor', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in devices:
            hostname = device['hostname']
            ip = device['ip']
            chassis_list = device['physical_inventory']['chassis']
            
            # Add VDC info to notes if applicable
            vdc_notes = ""
            if device.get('vdc_info', {}).get('is_vdc'):
                vdc_notes = f"Consolidated from: {device['vdc_info']['consolidated_from']}"
            
            # Write main chassis
            if chassis_list:
                main_chassis = chassis_list[0]
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Chassis',
                    'model': main_chassis['model'],
                    'serial_number': main_chassis['serial'],
                    'port_location': '',
                    'vendor': 'Cisco',
                    'notes': vdc_notes
                })
                
                # Additional chassis (FEX, etc)
                for i in range(1, len(chassis_list)):
                    chassis = chassis_list[i]
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': f'FEX-{i}',
                        'model': chassis['model'],
                        'serial_number': chassis['serial'],
                        'port_location': chassis['name'],
                        'vendor': 'Cisco',
                        'notes': ''
                    })
            
            # Modules - only write unique serials
            seen_module_serials = set()
            for module in device['physical_inventory']['modules']:
                if module['serial'] not in seen_module_serials:
                    seen_module_serials.add(module['serial'])
                    writer.writerow({
                        'hostname': '',
                        'ip_address': '',
                        'position': 'Module',
                        'model': module['model'],
                        'serial_number': module['serial'],
                        'port_location': module['name'],
                        'vendor': '',
                        'notes': ''
                    })
    
    print(f"\nCSV saved to: /usr/local/bin/Main/inventory_consolidated_final.csv")

if __name__ == "__main__":
    consolidated = consolidate_vdc_devices()
    generate_consolidated_csv(consolidated)