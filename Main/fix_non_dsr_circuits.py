#!/usr/bin/env python3
"""
Fix circuits incorrectly marked as Non-DSR
Since all circuits from DSR Global imports are DSR circuits by definition
"""

import psycopg2
from datetime import datetime

def fix_non_dsr_circuits():
    """Update circuits incorrectly marked as Non-DSR to csv_import"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Fixing circuits incorrectly marked as Non-DSR...")
    print("="*80)
    
    # First, show what we're about to fix
    cur.execute("""
        SELECT COUNT(*) 
        FROM circuits 
        WHERE data_source = 'Non-DSR'
    """)
    count = cur.fetchone()[0]
    print(f"Found {count} circuits marked as 'Non-DSR'")
    
    # Show some examples
    cur.execute("""
        SELECT site_name, provider_name, status, data_source
        FROM circuits 
        WHERE data_source = 'Non-DSR'
        LIMIT 10
    """)
    
    print("\nSample circuits to be fixed:")
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    print("\nUpdating data_source from 'Non-DSR' to 'csv_import'...")
    
    # Update all Non-DSR to csv_import since they all come from DSR Global
    cur.execute("""
        UPDATE circuits 
        SET data_source = 'csv_import',
            updated_at = NOW()
        WHERE data_source = 'Non-DSR'
    """)
    
    rows_updated = cur.rowcount
    print(f"Updated {rows_updated} circuits")
    
    # Verify the fix
    cur.execute("""
        SELECT COUNT(*) 
        FROM circuits 
        WHERE data_source = 'Non-DSR'
    """)
    remaining = cur.fetchone()[0]
    print(f"\nRemaining Non-DSR circuits: {remaining} (should be 0)")
    
    # Check CAL 24 specifically
    print("\nChecking CAL 24 after fix:")
    cur.execute("""
        SELECT site_id, circuit_purpose, provider_name, status, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' AND status = 'Enabled'
    """)
    
    for row in cur.fetchall():
        print(f"  {row}")
    
    # Commit the changes
    conn.commit()
    print("\n✅ Fix completed and committed to database")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_non_dsr_circuits()