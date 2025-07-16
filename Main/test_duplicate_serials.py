#!/usr/bin/env python3
"""
Test script to find and report duplicate serial numbers in inventory
"""
import json
import sys
import os
import psycopg2
from collections import defaultdict

def test_duplicate_serials():
    """Find and report duplicate serial numbers"""
    # Direct database connection
    conn = psycopg2.connect(
        host="localhost",
        database="network_inventory",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    
    try:
        # Get all devices with inventory
        cursor.execute("""
            SELECT device_name, physical_inventory
            FROM comprehensive_device_inventory
            WHERE physical_inventory IS NOT NULL
            ORDER BY device_name
        """)
        
        # Track serials and which devices have them
        serial_to_devices = defaultdict(list)
        component_details = {}  # serial -> component details
        
        for device_name, physical_inv in cursor.fetchall():
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
        
        print(f"Total unique serial numbers: {len(serial_to_devices)}")
        print(f"Duplicate serial numbers found: {len(duplicates)}")
        
        if duplicates:
            print("\n=== Duplicate Serial Numbers ===")
            
            # Group by device pairs to see patterns
            device_pairs = defaultdict(list)
            for serial, occurrences in duplicates.items():
                devices = sorted([occ['device'] for occ in occurrences])
                pair_key = " <-> ".join(devices)
                device_pairs[pair_key].append({
                    'serial': serial,
                    'model': component_details[serial]['model'],
                    'description': component_details[serial]['description'],
                    'occurrences': occurrences
                })
            
            # Show patterns
            for pair, serials in sorted(device_pairs.items()):
                print(f"\n{pair}: {len(serials)} shared components")
                
                # Show first few examples
                for i, item in enumerate(serials[:3]):
                    print(f"  Serial: {item['serial']}")
                    print(f"  Model: {item['model']}")
                    print(f"  Description: {item['description']}")
                    for occ in item['occurrences']:
                        print(f"    - {occ['device']}: {occ['type']} - {occ['name']}")
                
                if len(serials) > 3:
                    print(f"  ... and {len(serials) - 3} more shared components")
        
        # Look for specific patterns
        print("\n=== Pattern Analysis ===")
        
        # Find Nexus pairs
        nexus_pairs = defaultdict(int)
        for serial, occurrences in duplicates.items():
            devices = [occ['device'] for occ in occurrences]
            if any('56128P' in d or 'N5K' in d or 'nexus' in d.lower() for d in devices):
                pair = tuple(sorted(devices))
                nexus_pairs[pair] += 1
        
        if nexus_pairs:
            print("\nNexus device pairs with shared components:")
            for pair, count in sorted(nexus_pairs.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pair[0]} <-> {pair[1]}: {count} shared components")
        
        # Check for -01/-02 pattern
        numbered_pairs = defaultdict(int)
        for serial, occurrences in duplicates.items():
            devices = [occ['device'] for occ in occurrences]
            # Check if devices follow -01, -02 pattern
            if len(devices) == 2:
                if devices[0].replace('-01', '') == devices[1].replace('-02', ''):
                    numbered_pairs[devices[0].rsplit('-', 1)[0]] += 1
        
        if numbered_pairs:
            print("\nDevice pairs following -01/-02 pattern:")
            for base_name, count in sorted(numbered_pairs.items()):
                print(f"  {base_name}-01 & {base_name}-02: {count} shared components")
                
    except Exception as e:
        print(f"Error analyzing duplicates: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_duplicate_serials()