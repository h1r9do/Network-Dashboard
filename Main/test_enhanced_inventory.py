#!/usr/bin/env python3
"""
Test script to verify enhanced inventory data format
"""
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_connection

def test_enhanced_inventory():
    """Test the enhanced inventory data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get sample devices with enhanced data
        cursor.execute("""
            SELECT device_name, ip_address, physical_inventory, summary
            FROM comprehensive_device_inventory
            WHERE collection_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY device_name
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("No recent inventory data found")
            return
        
        print(f"Found {len(results)} devices with recent inventory\n")
        
        for device_name, ip_address, physical_inv, summary in results:
            print(f"Device: {device_name} ({ip_address})")
            print(f"Summary: {json.dumps(summary, indent=2)}")
            
            # Check for enhanced features
            chassis = physical_inv.get('chassis', [])
            modules = physical_inv.get('modules', [])
            sfps = physical_inv.get('transceivers', [])
            
            # Check for FEX models
            fex_found = False
            for item in chassis + modules:
                if 'N2K-' in item.get('model', ''):
                    fex_found = True
                    print(f"  FEX Found: {item['model']} (Serial: {item['serial']})")
            
            # Check for enhanced SFPs
            enhanced_sfps = 0
            for sfp in sfps:
                if sfp.get('model', '') not in ['Unspecified', '']:
                    enhanced_sfps += 1
                    if sfp.get('vendor'):
                        print(f"  SFP: {sfp['model']} - {sfp['vendor']} (Port: {sfp['name']})")
            
            print(f"  Chassis Count: {len(chassis)}")
            print(f"  Module Count: {len(modules)}")
            print(f"  SFP Count: {len(sfps)} (Enhanced: {enhanced_sfps})")
            print(f"  FEX Detected: {'Yes' if fex_found else 'No'}")
            print("-" * 50)
        
        # Show specific examples
        print("\n=== Looking for specific enhancements ===")
        
        # Find devices with stacks
        cursor.execute("""
            SELECT device_name, 
                   jsonb_array_length(physical_inventory->'chassis') as chassis_count
            FROM comprehensive_device_inventory
            WHERE jsonb_array_length(physical_inventory->'chassis') > 1
            LIMIT 3
        """)
        
        stacks = cursor.fetchall()
        if stacks:
            print(f"\nStacked devices found: {len(stacks)}")
            for name, count in stacks:
                print(f"  {name}: {count} chassis members")
        
        # Find devices with FEX
        cursor.execute("""
            SELECT DISTINCT device_name, 
                   physical_inventory->'chassis'->0->>'model' as parent_model
            FROM comprehensive_device_inventory
            WHERE physical_inventory::text LIKE '%N2K-%'
            LIMIT 3
        """)
        
        fex_devices = cursor.fetchall()
        if fex_devices:
            print(f"\nDevices with FEX found: {len(fex_devices)}")
            for name, model in fex_devices:
                print(f"  {name}: Parent switch {model}")
                
    except Exception as e:
        print(f"Error testing inventory: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_enhanced_inventory()