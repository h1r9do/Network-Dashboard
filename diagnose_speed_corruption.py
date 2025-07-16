#!/usr/bin/env python3
"""
Diagnose where speed corruption is happening in the enrichment process
"""

import os
import sys
import psycopg2
from datetime import datetime

sys.path.append('/usr/local/bin/Main/nightly')

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def diagnose_corruption():
    """Step through the enrichment process to find where corruption happens"""
    
    # Import the actual nightly script
    from nightly_enriched_db import (
        get_dsr_circuits, parse_raw_notes, reformat_speed,
        match_dsr_circuit_by_ip, determine_final_provider
    )
    
    conn = get_db_connection()
    
    print("=== DIAGNOSING SPEED CORRUPTION ===\n")
    
    # Step 1: Check DSR data
    print("1. Getting DSR circuits data...")
    dsr_circuits_by_site = get_dsr_circuits(conn)
    
    # Check CAN00 data
    can00_circuits = dsr_circuits_by_site.get('CAN00', [])
    print(f"   Found {len(can00_circuits)} circuits for CAN00")
    for circuit in can00_circuits:
        print(f"   - {circuit['purpose']}: speed='{circuit['speed']}' provider='{circuit['provider']}'")
    
    # Step 2: Get Meraki data
    print("\n2. Getting Meraki data for CAN_00...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT device_notes, wan1_ip, wan2_ip
        FROM meraki_inventory
        WHERE network_name = 'CAN_00'
    """)
    row = cursor.fetchone()
    if row:
        device_notes, wan1_ip, wan2_ip = row
        print(f"   WAN1 IP: {wan1_ip}")
        print(f"   WAN2 IP: {wan2_ip}")
        
        # Step 3: Parse notes
        print("\n3. Parsing device notes...")
        wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(device_notes)
        print(f"   WAN1: provider='{wan1_notes}' speed='{wan1_speed}'")
        print(f"   WAN2: provider='{wan2_notes}' speed='{wan2_speed}'")
        
        # Step 4: Match DSR circuits
        print("\n4. Matching DSR circuits...")
        wan1_dsr = match_dsr_circuit_by_ip(can00_circuits, wan1_ip)
        wan2_dsr = match_dsr_circuit_by_ip(can00_circuits, wan2_ip)
        print(f"   WAN1 match: {wan1_dsr}")
        print(f"   WAN2 match: {wan2_dsr}")
        
        # Step 5: Check speed selection
        print("\n5. Speed selection logic...")
        wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
        wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr and wan2_dsr.get('speed') else wan2_speed
        print(f"   WAN1 speed to use: '{wan1_speed_to_use}'")
        print(f"   WAN2 speed to use: '{wan2_speed_to_use}'")
        
        # Step 6: Test reformat_speed
        print("\n6. Testing reformat_speed function...")
        wan1_provider_final = wan1_dsr['provider'] if wan1_dsr else wan1_notes
        wan2_provider_final = wan2_dsr['provider'] if wan2_dsr else wan2_notes
        
        wan1_speed_final = reformat_speed(wan1_speed_to_use, wan1_provider_final)
        wan2_speed_final = reformat_speed(wan2_speed_to_use, wan2_provider_final)
        print(f"   WAN1 final speed: '{wan1_speed_final}'")
        print(f"   WAN2 final speed: '{wan2_speed_final}'")
        
        # Step 7: Check what's actually in enriched_circuits
        print("\n7. Current enriched_circuits data...")
        cursor.execute("""
            SELECT wan1_speed, wan2_speed
            FROM enriched_circuits
            WHERE network_name = 'CAN_00'
        """)
        enriched = cursor.fetchone()
        if enriched:
            print(f"   WAN1 in DB: '{enriched[0]}'")
            print(f"   WAN2 in DB: '{enriched[1]}'")
        
        # Analysis
        print("\n=== ANALYSIS ===")
        if wan1_speed_final != enriched[0] or wan2_speed_final != enriched[1]:
            print("❌ MISMATCH DETECTED!")
            print(f"   Expected WAN1: '{wan1_speed_final}' but got '{enriched[0]}'")
            print(f"   Expected WAN2: '{wan2_speed_final}' but got '{enriched[1]}'")
            print("\nThe corruption is happening AFTER reformat_speed!")
            print("Check the INSERT statement or any post-processing.")
        else:
            print("✓ No corruption detected in the logic flow")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    diagnose_corruption()