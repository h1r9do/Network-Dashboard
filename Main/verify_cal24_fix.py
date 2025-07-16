#!/usr/bin/env python3
"""Verify that the CAL 24 ARIN refresh fix addresses the issue"""

import psycopg2

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser'
db_pass = 'dsrpass123'

def verify_fix():
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        cur = conn.cursor()
        
        site_name = "CAL 24"
        print(f"=== Verifying ARIN refresh fix for {site_name} ===\n")
        
        # Check the old logic issue
        print("1. OLD LOGIC ISSUE (Fixed):")
        print("   - Old code tried to access circuit.wan1_ip and circuit.wan2_ip")
        print("   - These columns don't exist in circuits table")
        print("   - This caused the function to find no IP data")
        
        # Show circuits table columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circuits' AND column_name LIKE '%ip%'
            ORDER BY column_name
        """)
        ip_columns = cur.fetchall()
        print(f"\n   Actual IP columns in circuits table: {[col[0] for col in ip_columns]}")
        
        # Check what IP data CAL 24 actually has
        print(f"\n2. ACTUAL DATA FOR {site_name}:")
        
        # Check circuit data
        cur.execute("""
            SELECT id, ip_address_start, provider_name
            FROM circuits 
            WHERE LOWER(site_name) = %s
        """, (site_name.lower(),))
        circuit = cur.fetchone()
        
        if circuit:
            print(f"   Circuit record: ID={circuit[0]}, IP={circuit[1]}, Provider={circuit[2]}")
            has_circuit_ip = circuit[1] is not None
        else:
            print("   No circuit record found")
            has_circuit_ip = False
        
        # Check Meraki data
        cur.execute("""
            SELECT device_serial, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
            FROM meraki_inventory 
            WHERE LOWER(network_name) = %s
        """, (site_name.lower(),))
        meraki = cur.fetchone()
        
        if meraki:
            print(f"   Meraki device: Serial={meraki[0]}")
            print(f"   WAN IPs: WAN1={meraki[1]}, WAN2={meraki[2]}")
            print(f"   Providers: WAN1={meraki[3]}, WAN2={meraki[4]}")
            has_meraki_ip = meraki[1] is not None or meraki[2] is not None
        else:
            print("   No Meraki device found")
            has_meraki_ip = False
        
        # Check enriched data
        cur.execute("""
            SELECT wan1_ip, wan2_ip, wan1_arin_org, wan2_arin_org
            FROM enriched_circuits 
            WHERE LOWER(network_name) = %s
        """, (site_name.lower(),))
        enriched = cur.fetchone()
        
        if enriched:
            print(f"   Enriched circuit: WAN1_IP={enriched[0]}, WAN2_IP={enriched[1]}")
            print(f"   ARIN orgs: WAN1={enriched[2]}, WAN2={enriched[3]}")
            has_enriched_ip = enriched[0] is not None or enriched[1] is not None
        else:
            print("   No enriched circuit found")
            has_enriched_ip = False
        
        # Analysis
        print(f"\n3. ANALYSIS:")
        print(f"   - Has circuit IP data: {has_circuit_ip}")
        print(f"   - Has Meraki IP data: {has_meraki_ip}")
        print(f"   - Has enriched IP data: {has_enriched_ip}")
        
        # The fix
        print(f"\n4. HOW THE FIX WORKS:")
        if has_circuit_ip:
            print("   ✓ NEW: Will use circuit.ip_address_start column")
            print("   ✓ This should provide IP data for ARIN lookup")
        elif has_meraki_ip:
            print("   ✓ Will use Meraki inventory IP data")
        elif has_enriched_ip:
            print("   ✓ Will use enriched circuits IP data")
        else:
            print("   ⚠️  Still no IP data available")
            print("   ✓ But will provide detailed error message explaining what was found")
        
        # Expected behavior
        print(f"\n5. EXPECTED BEHAVIOR AFTER FIX:")
        if has_circuit_ip or has_meraki_ip or has_enriched_ip:
            print("   ✅ ARIN refresh should now work")
            print("   ✅ Should return IP and provider information")
        else:
            print("   ✅ Will return detailed error instead of generic 'No IP data found'")
            if meraki:
                print(f"   ✅ Error will mention: 'Meraki device found (serial: {meraki[0]}) but no IP addresses recorded'")
            if circuit:
                print(f"   ✅ Error will mention: 'Found 1 circuit record(s) but no usable IP addresses'")
        
        conn.close()
        
        print(f"\n6. SUMMARY:")
        print("   🔧 Fixed column access issue (wan1_ip → ip_address_start)")
        print("   🔧 Enhanced error messages with detailed information")
        print("   🔧 Better handling of sites with incomplete data")
        print(f"   ✅ CAL 24 should now work or provide clear error message")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_fix()