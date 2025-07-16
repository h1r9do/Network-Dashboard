#!/usr/bin/env python3
"""
Test for duplicate serial numbers using JSON file
"""
import json
from collections import defaultdict

def test_duplicate_serials():
    """Find duplicate serials in JSON inventory file"""
    
    # Load the inventory data
    with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
        all_devices = json.load(f)
    
    # Track serials and which devices have them
    serial_to_devices = defaultdict(list)
    component_details = {}
    
    for device in all_devices:
        device_name = device['hostname']
        physical_inv = device['physical_inventory']
        
        # Check all component types
        for comp_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
            for component in physical_inv.get(comp_type, []):
                serial = component.get('serial', '').strip()
                if serial and serial != '""':
                    serial_to_devices[serial].append({
                        'device': device_name,
                        'type': comp_type,
                        'model': component.get('model', ''),
                        'name': component.get('name', ''),
                        'description': component.get('description', '')
                    })
                    component_details[serial] = {
                        'model': component.get('model', ''),
                        'description': component.get('description', '')
                    }
    
    # Find duplicates
    duplicates = {serial: devices for serial, devices in serial_to_devices.items() 
                 if len(devices) > 1}
    
    print(f"Total devices analyzed: {len(all_devices)}")
    print(f"Total unique serial numbers: {len(serial_to_devices)}")
    print(f"Duplicate serial numbers found: {len(duplicates)}")
    
    if duplicates:
        print("\n=== Duplicate Serial Numbers ===")
        
        # Group by device pairs
        device_pairs = defaultdict(list)
        for serial, occurrences in duplicates.items():
            devices = sorted(set([occ['device'] for occ in occurrences]))
            pair_key = " <-> ".join(devices)
            device_pairs[pair_key].append({
                'serial': serial,
                'model': component_details[serial]['model'],
                'description': component_details[serial]['description'],
                'occurrences': occurrences
            })
        
        # Show top pairs
        sorted_pairs = sorted(device_pairs.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (pair, serials) in enumerate(sorted_pairs[:10]):
            print(f"\n{i+1}. {pair}: {len(serials)} shared components")
            
            # Show first few examples
            for j, item in enumerate(serials[:2]):
                print(f"   Serial: {item['serial']}")
                print(f"   Model: {item['model']}")
                for occ in item['occurrences']:
                    print(f"     - {occ['device']}: {occ['type']} ({occ['name']})")
            
            if len(serials) > 2:
                print(f"   ... and {len(serials) - 2} more shared components")
        
        if len(sorted_pairs) > 10:
            print(f"\n... and {len(sorted_pairs) - 10} more device pairs with duplicates")
        
        # Pattern analysis
        print("\n=== Pattern Analysis ===")
        
        # Check for -01/-02 pattern
        numbered_pairs = 0
        for pair_key in device_pairs.keys():
            if '-01' in pair_key and '-02' in pair_key:
                numbered_pairs += 1
        
        print(f"Device pairs following -01/-02 pattern: {numbered_pairs}")
        
        # Check component types
        type_counts = defaultdict(int)
        for serial, occurrences in duplicates.items():
            types = set(occ['type'] for occ in occurrences)
            for t in types:
                type_counts[t] += 1
        
        print("\nDuplicate components by type:")
        for comp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {comp_type}: {count} duplicates")

if __name__ == "__main__":
    test_duplicate_serials()