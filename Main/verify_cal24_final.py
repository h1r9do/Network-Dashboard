#!/usr/bin/env python3
"""
Final verification of CAL 24 circuits
"""

import psycopg2

def verify_cal24():
    """Verify CAL 24 circuits after fix"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Final verification of CAL 24 circuits...")
    print("="*80)
    
    # Check all enabled circuits for CAL 24
    cur.execute("""
        SELECT site_id, circuit_purpose, provider_name, billing_monthly_cost, status, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' AND status = 'Enabled'
        ORDER BY provider_name
    """)
    
    circuits = cur.fetchall()
    print(f"CAL 24 has {len(circuits)} enabled circuits (will show in dsrallcircuits):\n")
    
    for circuit in circuits:
        site_id, purpose, provider, cost, status, source = circuit
        print(f"Provider: {provider}")
        print(f"  Purpose: {purpose}")
        print(f"  Cost: ${cost or 0}")
        print(f"  Status: {status}")
        print(f"  Source: {source}")
        print()
    
    # Verify total enabled count
    cur.execute("""
        SELECT COUNT(*) FROM circuits WHERE status = 'Enabled'
    """)
    total = cur.fetchone()[0]
    print(f"Total enabled circuits in system: {total}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_cal24()