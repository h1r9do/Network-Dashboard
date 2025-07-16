#!/usr/bin/env python3
"""
Check CAL 24 circuits in the database to identify DSR vs Non-DSR circuits
"""

import psycopg2

def check_cal24_circuits():
    """Check all circuits for CAL 24 site"""
    # Database connection - using the connection string from config.py
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Checking CAL 24 circuits in database...")
    print("="*80)
    
    # Query all circuits for CAL 24, regardless of status
    cur.execute("""
        SELECT site_id, circuit_purpose, provider_name, details_ordered_service_speed, 
               billing_monthly_cost, status, record_number
        FROM circuits 
        WHERE site_name = 'CAL 24'
        ORDER BY status, circuit_purpose
    """)
    
    circuits = cur.fetchall()
    print(f"\nTotal circuits found for CAL 24: {len(circuits)}")
    print("-"*80)
    
    # Group by status
    status_groups = {}
    for circuit in circuits:
        site_id, purpose, provider, speed, cost, status, record_num = circuit
        status = status or 'Unknown'
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(circuit)
    
    # Display circuits grouped by status
    for status, status_circuits in status_groups.items():
        print(f"\n{status} circuits: {len(status_circuits)}")
        for circuit in status_circuits:
            site_id, purpose, provider, speed, cost, _, record_num = circuit
            print(f"  - Site ID: {site_id}")
            print(f"    Circuit Purpose: {purpose}")
            print(f"    Provider: {provider}")
            print(f"    Speed: {speed}")
            print(f"    Cost: ${cost or 0}")
            print(f"    Record Number: {record_num}")
            print()
    
    # Check for Non-DSR indicators
    print("\nChecking for Non-DSR indicators...")
    print("-"*80)
    
    non_dsr_indicators = [
        "Non-DSR",
        "non-dsr", 
        "NonDSR",
        "Store provided",
        "Store Provided",
        "Customer provided",
        "Customer Provided"
    ]
    
    found_non_dsr = False
    for circuit in circuits:
        site_id, purpose, provider, speed, cost, status, record_num = circuit
        
        # Check circuit_purpose field
        if purpose:
            for indicator in non_dsr_indicators:
                if indicator.lower() in purpose.lower():
                    found_non_dsr = True
                    print(f"\n⚠️  Possible Non-DSR circuit found:")
                    print(f"   Site ID: {site_id}")
                    print(f"   Purpose: {purpose}")
                    print(f"   Status: {status}")
                    print(f"   Provider: {provider}")
                    break
                    
        # Check if it's a store-provided circuit based on cost
        if (cost is None or cost == 0) and status == 'Enabled':
            print(f"\n⚠️  Zero-cost enabled circuit (possible store-provided):")
            print(f"   Site ID: {site_id}")
            print(f"   Purpose: {purpose}")
            print(f"   Provider: {provider}")
    
    if not found_non_dsr:
        print("No obvious Non-DSR indicators found in circuit_purpose field")
    
    # Show only enabled circuits (what would appear in dsrallcircuits)
    enabled_circuits = [c for c in circuits if c[5] == 'Enabled']
    print(f"\n\n❗ ENABLED circuits that appear in /dsrallcircuits: {len(enabled_circuits)}")
    print("-"*80)
    for circuit in enabled_circuits:
        site_id, purpose, provider, speed, cost, _, _ = circuit
        print(f"Site ID: {site_id}, Purpose: {purpose}, Provider: {provider}, Cost: ${cost or 0}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_cal24_circuits()