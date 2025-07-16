#!/usr/bin/env python3
"""
Delete the Frontier Fios circuit from CAL 24 since it's not in the current DSR tracking
"""

import psycopg2

def delete_cal24_fios():
    """Delete the Frontier Fios circuit from CAL 24"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Deleting Frontier Fios circuit from CAL 24...")
    print("="*80)
    
    # First show what we're about to delete
    cur.execute("""
        SELECT id, site_name, provider_name, billing_monthly_cost, status, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' 
        AND provider_name = 'Frontier Fios'
        AND status = 'Enabled'
    """)
    
    circuit = cur.fetchone()
    if circuit:
        print(f"Found circuit to delete:")
        print(f"  ID: {circuit[0]}")
        print(f"  Site: {circuit[1]}")
        print(f"  Provider: {circuit[2]}")
        print(f"  Cost: ${circuit[3]}")
        print(f"  Status: {circuit[4]}")
        print(f"  Source: {circuit[5]}")
        
        # Delete the circuit
        cur.execute("""
            DELETE FROM circuits 
            WHERE id = %s
        """, (circuit[0],))
        
        print(f"\n✅ Deleted circuit with ID {circuit[0]}")
    else:
        print("No Frontier Fios circuit found for CAL 24")
    
    # Verify CAL 24 status after deletion
    print("\nCAL 24 circuits after deletion:")
    cur.execute("""
        SELECT provider_name, billing_monthly_cost, status, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24'
        ORDER BY status, provider_name
    """)
    
    circuits = cur.fetchall()
    if circuits:
        for circuit in circuits:
            print(f"  {circuit[0]} | ${circuit[1]} | {circuit[2]} | {circuit[3]}")
    else:
        print("  No circuits found for CAL 24")
    
    # Check how many DSR circuits will show in dsrallcircuits
    cur.execute("""
        SELECT COUNT(*) 
        FROM circuits 
        WHERE status = 'Enabled' 
        AND (data_source != 'Non-DSR' OR data_source IS NULL)
    """)
    dsr_count = cur.fetchone()[0]
    print(f"\nTotal DSR circuits that will show in dsrallcircuits: {dsr_count}")
    
    # Commit the changes
    conn.commit()
    print("\n✅ Changes committed to database")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    delete_cal24_fios()