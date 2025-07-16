#!/usr/bin/env python3
"""
Test the deduplication logic on JSON inventory data
"""
import json
import re
from collections import defaultdict

class InventoryDeduplicator:
    def __init__(self):
        self.seen_serials = set()
        self.serial_to_device = {}
        
    def find_cross_device_duplicates(self, all_devices):
        """Find serials that appear across multiple devices"""
        serial_devices = {}
        
        for device in all_devices:
            device_name = device['hostname']
            physical_inv = device['physical_inventory']
            
            for component_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
                for component in physical_inv.get(component_type, []):
                    serial = component.get('serial', '').strip()
                    if serial:
                        if serial not in serial_devices:
                            serial_devices[serial] = []
                        serial_devices[serial].append(device_name)
        
        # Return only duplicates
        duplicates = {serial: list(set(devices)) for serial, devices in serial_devices.items() 
                     if len(set(devices)) > 1}
        
        return duplicates
    
    def assign_to_primary_device(self, all_devices):
        """Assign components to primary device when duplicated"""
        # First pass: identify all duplicates
        duplicates = self.find_cross_device_duplicates(all_devices)
        
        print(f"Found {len(duplicates)} duplicate serials across devices")
        
        # Build serial assignment map
        serial_assignment = {}
        assignment_stats = defaultdict(int)
        
        for serial, devices in duplicates.items():
            # Special handling for Nexus 7K VDCs
            if any('7000' in d for d in devices):
                # For 7K VDCs, assign to CORE VDC
                core_device = next((d for d in devices if 'CORE' in d), None)
                if core_device:
                    primary_device = core_device
                else:
                    # Fall back to -01 device
                    primary_device = next((d for d in devices if '-01' in d), sorted(devices)[0])
                assignment_stats['7K VDC'] += 1
            
            # Special handling for N5K FEX sharing
            elif any('-01' in d and d.replace('-01', '-02') in devices for d in devices):
                # Assign to -01 device
                primary_device = next(d for d in devices if '-01' in d)
                assignment_stats['N5K FEX'] += 1
            
            # General case: prefer -01 device
            elif any('-01' in d for d in devices):
                primary_device = next(d for d in devices if '-01' in d)
                assignment_stats['General -01'] += 1
            
            # Otherwise use first alphabetically
            else:
                primary_device = sorted(devices)[0]
                assignment_stats['Alphabetical'] += 1
                
            serial_assignment[serial] = primary_device
        
        print("\nAssignment statistics:")
        for reason, count in assignment_stats.items():
            print(f"  {reason}: {count} serials")
        
        # Second pass: remove duplicates from non-primary devices
        cleaned_devices = []
        removal_stats = defaultdict(int)
        
        for device in all_devices:
            device_name = device['hostname']
            physical_inv = device['physical_inventory']
            
            # Track removals
            removed_count = 0
            
            # Clean each component type
            for component_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
                if component_type in physical_inv:
                    kept_components = []
                    
                    for component in physical_inv[component_type]:
                        serial = component.get('serial', '').strip()
                        
                        # Keep if no serial
                        if not serial:
                            kept_components.append(component)
                            continue
                        
                        # Keep if not duplicated
                        if serial not in duplicates:
                            kept_components.append(component)
                            continue
                        
                        # Keep if this is the assigned device
                        if serial_assignment[serial] == device_name:
                            kept_components.append(component)
                            # Add note about shared component
                            if len(duplicates[serial]) > 1:
                                component['shared_with'] = [d for d in duplicates[serial] if d != device_name]
                        else:
                            removed_count += 1
                            removal_stats[component_type] += 1
                    
                    physical_inv[component_type] = kept_components
            
            if removed_count > 0:
                print(f"  Removed {removed_count} duplicate components from {device_name}")
            
            cleaned_devices.append(device)
        
        print("\nRemoval statistics by component type:")
        for comp_type, count in removal_stats.items():
            print(f"  {comp_type}: {count} removed")
        
        return cleaned_devices

def test_deduplication():
    """Test the deduplication process"""
    # Load inventory
    with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
        original_devices = json.load(f)
    
    print(f"Original inventory: {len(original_devices)} devices")
    
    # Count original components
    original_counts = defaultdict(int)
    for device in original_devices:
        for comp_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
            original_counts[comp_type] += len(device['physical_inventory'].get(comp_type, []))
    
    print("\nOriginal component counts:")
    for comp_type, count in original_counts.items():
        print(f"  {comp_type}: {count}")
    
    # Deduplicate
    deduplicator = InventoryDeduplicator()
    cleaned_devices = deduplicator.assign_to_primary_device(original_devices)
    
    # Count cleaned components
    cleaned_counts = defaultdict(int)
    for device in cleaned_devices:
        for comp_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
            cleaned_counts[comp_type] += len(device['physical_inventory'].get(comp_type, []))
    
    print("\nCleaned component counts:")
    for comp_type, count in cleaned_counts.items():
        reduction = original_counts[comp_type] - count
        print(f"  {comp_type}: {count} (removed {reduction})")
    
    # Save cleaned data
    with open('/usr/local/bin/Main/physical_inventory_deduplicated.json', 'w') as f:
        json.dump(cleaned_devices, f, indent=2)
    
    print(f"\nDeduplicated inventory saved to physical_inventory_deduplicated.json")
    
    # Show some examples of assignments
    print("\n=== Example Assignments ===")
    examples_shown = 0
    for serial, devices in deduplicator.find_cross_device_duplicates(original_devices).items():
        if examples_shown < 5:
            assigned_to = deduplicator.serial_assignment[serial] if hasattr(deduplicator, 'serial_assignment') else 'N/A'
            print(f"\nSerial: {serial}")
            print(f"  Found on: {', '.join(devices)}")
            print(f"  Assigned to: {assigned_to}")
            examples_shown += 1

if __name__ == "__main__":
    test_deduplication()