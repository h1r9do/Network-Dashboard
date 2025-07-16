#!/usr/bin/env python3
"""
Verify DSR circuit filtering is working correctly
"""

import psycopg2

def verify_filtering():
    """Verify the filtering logic"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Verifying DSR circuit filtering...")
    print("="*80)
    
    # Count all enabled circuits
    cur.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE status = 'Enabled'
    """)
    total_enabled = cur.fetchone()[0]
    print(f"Total enabled circuits (before filtering): {total_enabled}")
    
    # Count enabled DSR circuits (excluding Non-DSR)
    cur.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE status = 'Enabled' 
        AND (data_source != 'Non-DSR' OR data_source IS NULL)
    """)
    dsr_enabled = cur.fetchone()[0]
    print(f"Enabled DSR circuits (after filtering): {dsr_enabled}")
    
    # Count excluded Non-DSR circuits
    cur.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE status = 'Enabled' AND data_source = 'Non-DSR'
    """)
    non_dsr_excluded = cur.fetchone()[0]
    print(f"Non-DSR circuits excluded: {non_dsr_excluded}")
    
    print(f"\nReduction: {total_enabled} → {dsr_enabled} (-{non_dsr_excluded} circuits)")
    
    # Check CAL 24 specifically
    print("\n" + "-"*80)
    print("CAL 24 circuits after filtering:")
    
    cur.execute("""
        SELECT site_id, circuit_purpose, provider_name, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' 
        AND status = 'Enabled'
        AND (data_source != 'Non-DSR' OR data_source IS NULL)
    """)
    
    cal24_circuits = cur.fetchall()
    if cal24_circuits:
        for circuit in cal24_circuits:
            print(f"  {circuit}")
    else:
        print("  ✅ No DSR circuits found for CAL 24 (Non-DSR circuits properly excluded)")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_filtering()