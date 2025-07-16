#!/usr/bin/env python3
"""
Check how Non-DSR circuits were added to the database
"""

import psycopg2

def check_non_dsr_source():
    """Check the source of Non-DSR circuits"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Checking Non-DSR circuit details...")
    print("="*80)
    
    # Check when Non-DSR circuits were added
    cur.execute("""
        SELECT MIN(created_at), MAX(created_at), COUNT(*)
        FROM circuits 
        WHERE data_source = 'Non-DSR'
    """)
    
    min_date, max_date, count = cur.fetchone()
    print(f"Non-DSR circuits: {count} total")
    print(f"First added: {min_date}")
    print(f"Last added: {max_date}")
    
    # Check if any Non-DSR circuits have record_numbers
    cur.execute("""
        SELECT COUNT(*), COUNT(record_number)
        FROM circuits 
        WHERE data_source = 'Non-DSR'
    """)
    
    total, with_record = cur.fetchone()
    print(f"\nRecord numbers: {with_record} out of {total} have record_numbers")
    
    # Check a sample of Non-DSR circuits
    print("\nSample Non-DSR circuits:")
    print("-"*80)
    
    cur.execute("""
        SELECT site_name, provider_name, billing_monthly_cost, created_at, record_number
        FROM circuits 
        WHERE data_source = 'Non-DSR'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    for row in cur.fetchall():
        site, provider, cost, created, record = row
        print(f"{site} | {provider} | ${cost or 0} | Created: {created} | Record: {record}")
    
    # Check if these are in the latest CSV
    print("\nChecking if CAL 24 exists in DSR tracking CSV...")
    import subprocess
    
    # Count CAL 24 entries in CSV with "Enabled" status
    cmd = "grep -i 'CAL 24' /var/www/html/circuitinfo/tracking_data_2025-07-12.csv | grep -i ',enabled,' | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        count = result.stdout.strip()
        print(f"CAL 24 enabled circuits in latest CSV: {count}")
    
    # Show what's in the CSV for CAL 24
    cmd2 = "grep -i 'CAL 24' /var/www/html/circuitinfo/tracking_data_2025-07-12.csv | cut -d',' -f1,2,15,16,17,67,68,71 | head -5"
    result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
    
    if result2.returncode == 0:
        print("\nCAL 24 entries in CSV (first 5):")
        print("Record#, Status, Site fields...")
        print(result2.stdout)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_non_dsr_source()