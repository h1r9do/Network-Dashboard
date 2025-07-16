#!/usr/bin/env python3
"""
Sync all fixes from production circuits and enriched_circuits tables to dev tables
This includes:
1. Non-DSR circuits we just created
2. Fixed speeds in enriched_circuits
"""

import psycopg2
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def sync_fixes_to_dev():
    """Copy all recent fixes to dev tables"""
    
    print("=== SYNCING FIXES TO DEV TABLES ===\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.autocommit = False
        
        # 1. First, clear the dev tables
        print("Step 1: Clearing dev tables...")
        cursor.execute("TRUNCATE TABLE circuits_dev CASCADE")
        cursor.execute("TRUNCATE TABLE enriched_circuits_dev CASCADE")
        print("✓ Dev tables cleared\n")
        
        # 2. Copy ALL data from circuits to circuits_dev
        print("Step 2: Copying all circuits data to circuits_dev...")
        cursor.execute("""
            INSERT INTO circuits_dev
            SELECT * FROM circuits
        """)
        circuits_count = cursor.rowcount
        print(f"✓ Copied {circuits_count} circuits to circuits_dev\n")
        
        # 3. Copy ALL data from enriched_circuits to enriched_circuits_dev
        print("Step 3: Copying all enriched_circuits data to enriched_circuits_dev...")
        cursor.execute("""
            INSERT INTO enriched_circuits_dev
            SELECT * FROM enriched_circuits
        """)
        enriched_count = cursor.rowcount
        print(f"✓ Copied {enriched_count} enriched circuits to enriched_circuits_dev\n")
        
        # 4. Verify the Non-DSR circuits are included
        print("Step 4: Verifying Non-DSR circuits...")
        cursor.execute("""
            SELECT COUNT(*) FROM circuits_dev
            WHERE data_source = 'Non-DSR'
        """)
        non_dsr_count = cursor.fetchone()[0]
        print(f"✓ Found {non_dsr_count} Non-DSR circuits in circuits_dev\n")
        
        # 5. Verify fixed speeds
        print("Step 5: Verifying fixed speeds...")
        cursor.execute("""
            SELECT 
                network_name,
                wan1_speed,
                wan2_speed
            FROM enriched_circuits_dev
            WHERE network_name IN ('CAN_00', 'CAN 16', 'CAS_00')
            ORDER BY network_name
        """)
        
        print("Sample of fixed speeds in enriched_circuits_dev:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: WAN1={row[1]}, WAN2={row[2]}")
        
        # 6. Check specific example - CAN 35
        print("\nStep 6: Checking CAN 35 data...")
        cursor.execute("""
            SELECT 
                'circuits_dev' as source,
                provider_name,
                billing_monthly_cost,
                circuit_purpose,
                data_source
            FROM circuits_dev
            WHERE site_name = 'CAN 35'
            AND status = 'Enabled'
            
            UNION ALL
            
            SELECT 
                'enriched_dev' as source,
                wan1_provider,
                NULL,
                wan1_circuit_role,
                NULL
            FROM enriched_circuits_dev
            WHERE network_name = 'CAN 35'
        """)
        
        print("\nCAN 35 data in dev tables:")
        for row in cursor.fetchall():
            if row[0] == 'circuits_dev':
                print(f"  Circuits: {row[1]} - ${row[2] or 0:.2f} (Purpose: {row[3]}, Source: {row[4]})")
            else:
                print(f"  Enriched: WAN1 Provider={row[1]}, Role={row[3]}")
        
        # Commit transaction
        conn.commit()
        print("\n✅ All data synced to dev tables successfully!")
        
        # Summary
        print("\n=== SUMMARY ===")
        print(f"Total circuits copied: {circuits_count}")
        print(f"Total enriched circuits copied: {enriched_count}")
        print(f"Non-DSR circuits included: {non_dsr_count}")
        print("\nDev tables now have:")
        print("  - All production data")
        print("  - All Non-DSR circuits we created")
        print("  - All speed fixes applied")
        print("\nReady for testing new matching logic!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sync_fixes_to_dev()