#!/usr/bin/env python3
"""
Verify that Non-DSR circuits are properly excluded from dsrallcircuits
"""

import psycopg2

def verify_exclusion():
    """Verify Non-DSR circuits are excluded"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Verifying Non-DSR circuit exclusion...")
    print("="*80)
    
    # Check total enabled circuits
    cur.execute("SELECT COUNT(*) FROM circuits WHERE status = 'Enabled'")
    total = cur.fetchone()[0]
    print(f"Total enabled circuits in database: {total}")
    
    # Check Non-DSR enabled circuits
    cur.execute("SELECT COUNT(*) FROM circuits WHERE status = 'Enabled' AND data_source = 'Non-DSR'")
    non_dsr = cur.fetchone()[0]
    print(f"Non-DSR enabled circuits: {non_dsr}")
    
    # Check what dsrallcircuits will show (mimicking the query)
    cur.execute("""
        SELECT COUNT(*) 
        FROM circuits 
        WHERE status = 'Enabled' 
        AND (data_source != 'Non-DSR' OR data_source IS NULL)
    """)
    shown = cur.fetchone()[0]
    print(f"Circuits that will show in dsrallcircuits: {shown}")
    print(f"Circuits excluded: {total - shown}")
    
    # Verify CAL 24 specifically
    print("\nCAL 24 verification:")
    cur.execute("""
        SELECT provider_name, status, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' AND status = 'Enabled'
    """)
    cal24 = cur.fetchall()
    if cal24:
        for circuit in cal24:
            print(f"  {circuit[0]} | {circuit[1]} | {circuit[2]}")
            if circuit[2] == 'Non-DSR':
                print("  ❌ This circuit will NOT show in dsrallcircuits")
            else:
                print("  ✅ This circuit WILL show in dsrallcircuits")
    else:
        print("  No enabled circuits for CAL 24")
    
    # Sample some other Non-DSR circuits to verify
    print("\nSample Non-DSR circuits (will NOT show in dsrallcircuits):")
    cur.execute("""
        SELECT site_name, provider_name, billing_monthly_cost
        FROM circuits 
        WHERE status = 'Enabled' AND data_source = 'Non-DSR'
        ORDER BY site_name
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | ${row[2] or 0}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_exclusion()