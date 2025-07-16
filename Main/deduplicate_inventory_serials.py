#!/usr/bin/env python3
"""
Handle duplicate serial numbers in inventory data
Especially important for Nexus devices that may report components multiple times
"""
import json
import re
from typing import Dict, List, Set, Tuple

class InventoryDeduplicator:
    def __init__(self):
        self.seen_serials = set()
        self.serial_to_device = {}  # Track which device first reported each serial
        
    def deduplicate_inventory(self, device_data: Dict) -> Dict:
        """Remove duplicate serial numbers from inventory"""
        device_name = device_data['device_name']
        physical_inv = device_data['physical_inventory']
        
        # Process each component type
        for component_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
            if component_type in physical_inv:
                deduplicated = []
                
                for component in physical_inv[component_type]:
                    serial = component.get('serial', '').strip()
                    
                    # Skip if no serial or already seen
                    if not serial or serial in self.seen_serials:
                        continue
                    
                    # Add to tracking
                    self.seen_serials.add(serial)
                    self.serial_to_device[serial] = device_name
                    deduplicated.append(component)
                
                physical_inv[component_type] = deduplicated
        
        return device_data
    
    def find_cross_device_duplicates(self, all_devices: List[Dict]) -> Dict[str, List[str]]:
        """Find serials that appear across multiple devices"""
        serial_devices = {}
        
        for device in all_devices:
            device_name = device['device_name']
            physical_inv = device['physical_inventory']
            
            for component_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
                for component in physical_inv.get(component_type, []):
                    serial = component.get('serial', '').strip()
                    if serial:
                        if serial not in serial_devices:
                            serial_devices[serial] = []
                        serial_devices[serial].append(device_name)
        
        # Return only duplicates
        duplicates = {serial: devices for serial, devices in serial_devices.items() 
                     if len(devices) > 1}
        
        return duplicates
    
    def assign_to_primary_device(self, all_devices: List[Dict]) -> List[Dict]:
        """Assign components to primary device (usually -01) when duplicated"""
        # First pass: identify all duplicates
        duplicates = self.find_cross_device_duplicates(all_devices)
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate serials across devices")
            
        # Build serial assignment map (assign to -01 device if available)
        serial_assignment = {}
        for serial, devices in duplicates.items():
            # Prefer device ending in -01
            primary_device = None
            for device in devices:
                if device.endswith('-01'):
                    primary_device = device
                    break
            
            # If no -01 device, use first alphabetically
            if not primary_device:
                primary_device = sorted(devices)[0]
                
            serial_assignment[serial] = primary_device
        
        # Second pass: remove duplicates from non-primary devices
        cleaned_devices = []
        for device in all_devices:
            device_name = device['device_name']
            physical_inv = device['physical_inventory']
            
            # Clean each component type
            for component_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
                if component_type in physical_inv:
                    kept_components = []
                    
                    for component in physical_inv[component_type]:
                        serial = component.get('serial', '').strip()
                        
                        # Keep if no serial (shouldn't happen with our filtering)
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
                    
                    physical_inv[component_type] = kept_components
            
            cleaned_devices.append(device)
        
        return cleaned_devices

def deduplicate_json_inventory():
    """Process inventory in JSON to remove duplicates"""
    # Load from JSON file
    with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
        all_devices = json.load(f)
    
    try:
        # Get all devices
        cursor.execute("""
            SELECT device_name, ip_address, physical_inventory, entity_data, summary, collection_timestamp
            FROM comprehensive_device_inventory
            ORDER BY device_name
        """)
        
        all_devices = []
        for row in cursor.fetchall():
            all_devices.append({
                'device_name': row[0],
                'ip_address': row[1],
                'physical_inventory': row[2],
                'entity_data': row[3],
                'summary': row[4],
                'collection_timestamp': row[5]
            })
        
        print(f"Processing {len(all_devices)} devices for duplicate serials")
        
        # Deduplicate
        deduplicator = InventoryDeduplicator()
        cleaned_devices = deduplicator.assign_to_primary_device(all_devices)
        
        # Update database with cleaned data
        update_count = 0
        for device in cleaned_devices:
            # Recalculate summary
            physical_inv = device['physical_inventory']
            summary = device['summary']
            summary['chassis_count'] = len(physical_inv.get('chassis', []))
            summary['module_count'] = len(physical_inv.get('modules', []))
            summary['transceiver_count'] = len(physical_inv.get('transceivers', []))
            
            cursor.execute("""
                UPDATE comprehensive_device_inventory
                SET physical_inventory = %s,
                    summary = %s
                WHERE device_name = %s
            """, (
                json.dumps(physical_inv),
                json.dumps(summary),
                device['device_name']
            ))
            update_count += 1
        
        conn.commit()
        print(f"Updated {update_count} devices with deduplicated inventory")
        
        # Show statistics
        total_components = sum(
            len(d['physical_inventory'].get('chassis', [])) +
            len(d['physical_inventory'].get('modules', [])) +
            len(d['physical_inventory'].get('transceivers', []))
            for d in cleaned_devices
        )
        
        print(f"Total components after deduplication: {total_components}")
        
    except Exception as e:
        print(f"Error deduplicating inventory: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    deduplicate_database_inventory()