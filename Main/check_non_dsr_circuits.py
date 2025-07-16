#!/usr/bin/env python3
"""
Check for Non-DSR circuits that are incorrectly showing in dsrallcircuits
"""

import psycopg2

def check_non_dsr_circuits():
    """Check for Non-DSR circuits with Enabled status"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Checking for Non-DSR circuits with Enabled status...")
    print("="*80)
    
    # Check data_source values
    cur.execute("""
        SELECT DISTINCT data_source, COUNT(*) 
        FROM circuits 
        GROUP BY data_source
        ORDER BY COUNT(*) DESC
    """)
    
    print("\nData source distribution:")
    for source, count in cur.fetchall():
        print(f"  {source}: {count} circuits")
    
    # Find enabled Non-DSR circuits
    cur.execute("""
        SELECT site_name, site_id, circuit_purpose, provider_name, billing_monthly_cost, data_source
        FROM circuits 
        WHERE data_source = 'Non-DSR' AND status = 'Enabled'
        ORDER BY site_name
    """)
    
    non_dsr_enabled = cur.fetchall()
    print(f"\n⚠️  Found {len(non_dsr_enabled)} ENABLED Non-DSR circuits (showing in dsrallcircuits):")
    print("-"*80)
    
    for circuit in non_dsr_enabled:
        site_name, site_id, purpose, provider, cost, source = circuit
        print(f"  {site_name} | {site_id} | {purpose} | {provider} | ${cost or 0} | {source}")
    
    # Also check for other possible non-DSR indicators
    cur.execute("""
        SELECT DISTINCT site_name, COUNT(*) as circuit_count
        FROM circuits 
        WHERE data_source = 'Non-DSR' AND status = 'Enabled'
        GROUP BY site_name
        ORDER BY COUNT(*) DESC
    """)
    
    print(f"\n\nSites with enabled Non-DSR circuits:")
    print("-"*80)
    for site, count in cur.fetchall():
        print(f"  {site}: {count} Non-DSR circuits")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_non_dsr_circuits()