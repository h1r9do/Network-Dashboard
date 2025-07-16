#!/usr/bin/env python3
"""
Sync all fixes from production tables to dev tables
Handles column differences between tables
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

def get_common_columns(cursor, table1, table2):
    """Get columns that exist in both tables"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        AND column_name IN (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s
        )
        ORDER BY ordinal_position
    """, (table1, table2))
    return [row[0] for row in cursor.fetchall()]

def sync_fixes_to_dev():
    """Copy all recent fixes to dev tables"""
    
    print("=== SYNCING FIXES TO DEV TABLES ===\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.autocommit = False
        
        # 1. Clear the dev tables
        print("Step 1: Clearing dev tables...")
        cursor.execute("TRUNCATE TABLE circuits_dev CASCADE")
        cursor.execute("TRUNCATE TABLE enriched_circuits_dev CASCADE")
        print("✓ Dev tables cleared\n")
        
        # 2. Get common columns for circuits
        print("Step 2: Checking table structures...")
        circuits_cols = get_common_columns(cursor, 'circuits', 'circuits_dev')
        enriched_cols = get_common_columns(cursor, 'enriched_circuits', 'enriched_circuits_dev')
        
        print(f"  Common columns in circuits tables: {len(circuits_cols)}")
        print(f"  Common columns in enriched tables: {len(enriched_cols)}\n")
        
        # 3. Copy circuits data
        print("Step 3: Copying circuits data...")
        circuits_cols_str = ', '.join(circuits_cols)
        cursor.execute(f"""
            INSERT INTO circuits_dev ({circuits_cols_str})
            SELECT {circuits_cols_str} FROM circuits
        """)
        circuits_count = cursor.rowcount
        print(f"✓ Copied {circuits_count} circuits to circuits_dev\n")
        
        # 4. Copy enriched_circuits data
        print("Step 4: Copying enriched_circuits data...")
        enriched_cols_str = ', '.join(enriched_cols)
        cursor.execute(f"""
            INSERT INTO enriched_circuits_dev ({enriched_cols_str})
            SELECT {enriched_cols_str} FROM enriched_circuits
        """)
        enriched_count = cursor.rowcount
        print(f"✓ Copied {enriched_count} enriched circuits to enriched_circuits_dev\n")
        
        # 5. Verify Non-DSR circuits
        print("Step 5: Verifying Non-DSR circuits...")
        cursor.execute("""
            SELECT COUNT(*) FROM circuits_dev
            WHERE data_source = 'Non-DSR'
        """)
        non_dsr_count = cursor.fetchone()[0]
        print(f"✓ Found {non_dsr_count} Non-DSR circuits in circuits_dev\n")
        
        # 6. Check CAN 35 example
        print("Step 6: Checking CAN 35 example...")
        cursor.execute("""
            SELECT 
                c.provider_name,
                c.billing_monthly_cost,
                c.circuit_purpose,
                c.data_source,
                ec.wan1_provider,
                ec.wan1_circuit_role
            FROM circuits_dev c
            LEFT JOIN enriched_circuits_dev ec ON ec.network_name = c.site_name
            WHERE c.site_name = 'CAN 35'
            AND c.status = 'Enabled'
            AND c.provider_name LIKE '%AT&T%'
        """)
        
        result = cursor.fetchone()
        if result:
            print("CAN 35 AT&T circuit in dev:")
            print(f"  Provider: {result[0]}")
            print(f"  Cost: ${result[1] or 0:.2f}")
            print(f"  Purpose: {result[2]}")
            print(f"  Source: {result[3]}")
            print(f"  Enriched WAN1: {result[4]} (Role: {result[5]})")
        
        # Commit
        conn.commit()
        print("\n✅ All data synced successfully!")
        
        print("\n=== SUMMARY ===")
        print(f"Circuits copied: {circuits_count}")
        print(f"Enriched circuits copied: {enriched_count}")
        print(f"Non-DSR circuits: {non_dsr_count}")
        print("\nDev tables ready for testing!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sync_fixes_to_dev()