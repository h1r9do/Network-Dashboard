#!/usr/bin/env python3
"""
Check AZP 08 database information
"""

import psycopg2
from datetime import datetime

def main():
    """Check AZP 08 in database"""
    print("🔍 Checking AZP 08 Database Information")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        # Check circuits table
        print("\n📊 Circuits Table for AZP 08:")
        cursor.execute("""
            SELECT 
                circuit_id,
                site_name,
                provider_name,
                circuit_purpose,
                status,
                ip_address_start,
                details_ordered_service_speed,
                manual_override,
                manual_override_date,
                notes,
                last_updated
            FROM circuits
            WHERE site_name = 'AZP 08'
            ORDER BY circuit_purpose
        """)
        
        circuits = cursor.fetchall()
        for circuit in circuits:
            print(f"\n   Circuit ID: {circuit[0]}")
            print(f"   Site: {circuit[1]}")
            print(f"   Provider: {circuit[2]}")
            print(f"   Purpose: {circuit[3]}")
            print(f"   Status: {circuit[4]}")
            print(f"   IP: {circuit[5]}")
            print(f"   Speed: {circuit[6]}")
            print(f"   Manual Override: {circuit[7]}")
            print(f"   Override Date: {circuit[8]}")
            print(f"   Notes: {circuit[9]}")
            print(f"   Last Updated: {circuit[10]}")
        
        # Check meraki_inventory table
        print("\n\n📊 Meraki Inventory for AZP 08:")
        cursor.execute("""
            SELECT 
                network_name,
                device_serial,
                device_model,
                wan1_ip,
                wan1_status,
                wan1_arin_provider,
                wan2_ip,
                wan2_status,
                wan2_arin_provider,
                device_notes,
                last_updated
            FROM meraki_inventory
            WHERE network_name = 'AZP 08'
        """)
        
        inventory = cursor.fetchone()
        if inventory:
            print(f"   Network: {inventory[0]}")
            print(f"   Serial: {inventory[1]}")
            print(f"   Model: {inventory[2]}")
            print(f"   WAN1 IP: {inventory[3]}")
            print(f"   WAN1 Status: {inventory[4]}")
            print(f"   WAN1 ARIN: {inventory[5]}")
            print(f"   WAN2 IP: {inventory[6]}")
            print(f"   WAN2 Status: {inventory[7]}")
            print(f"   WAN2 ARIN: {inventory[8]}")
            print(f"   Device Notes: {repr(inventory[9])}")  # Show raw representation
            print(f"   Last Updated: {inventory[10]}")
        
        # Check enriched_circuits table
        print("\n\n📊 Enriched Circuits for AZP 08:")
        cursor.execute("""
            SELECT 
                site_name,
                wan1_provider,
                wan1_speed,
                wan2_provider,
                wan2_speed,
                device_notes,
                last_updated
            FROM enriched_circuits
            WHERE site_name = 'AZP 08'
        """)
        
        enriched = cursor.fetchone()
        if enriched:
            print(f"   Site: {enriched[0]}")
            print(f"   WAN1 Provider: {enriched[1]}")
            print(f"   WAN1 Speed: {enriched[2]}")
            print(f"   WAN2 Provider: {enriched[3]}")
            print(f"   WAN2 Speed: {enriched[4]}")
            print(f"   Device Notes: {repr(enriched[5])}")  # Show raw representation
            print(f"   Last Updated: {enriched[6]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    main()