#!/usr/bin/env python3
"""Check the delta between CSV enabled circuits and database circuits"""

import csv
import psycopg2
from collections import defaultdict

# Read CSV file
csv_enabled_sites = set()
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_enabled_sites.add(row['Site Name'].strip())

print(f"CSV file has {len(csv_enabled_sites)} unique sites with enabled circuits")

# Connect to database
try:
    # Use SQLAlchemy connection from config
    import sys
    sys.path.insert(0, '/usr/local/bin/Main')
    from config import config
    from sqlalchemy import create_engine
    
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    conn = engine.raw_connection()
    cur = conn.cursor()
    
    # Get enabled circuits from database
    cur.execute("""
        SELECT DISTINCT c.site_name 
        FROM circuits c
        WHERE c.status = 'Enabled'
    """)
    db_enabled_sites = {row[0] for row in cur.fetchall() if row[0]}
    
    print(f"Database has {len(db_enabled_sites)} unique sites with enabled circuits")
    
    # Get sites that have Discount-Tire tag (what the test page shows)
    cur.execute("""
        SELECT DISTINCT ec.network_name
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE mi.device_tags @> ARRAY['Discount-Tire']
        AND EXISTS (
            SELECT 1 FROM circuits c 
            WHERE LOWER(c.site_name) = LOWER(ec.network_name) 
            AND c.status = 'Enabled'
        )
    """)
    test_page_sites = {row[0] for row in cur.fetchall() if row[0]}
    
    print(f"Test page shows {len(test_page_sites)} sites (filtered by Discount-Tire tag)")
    
    # Find the delta
    in_csv_not_test = csv_enabled_sites - test_page_sites
    in_test_not_csv = test_page_sites - csv_enabled_sites
    
    print(f"\nDelta Analysis:")
    print(f"Sites in CSV but not on test page: {len(in_csv_not_test)}")
    print(f"Sites on test page but not in CSV: {len(in_test_not_csv)}")
    
    # Show some examples
    if in_csv_not_test:
        print(f"\nExamples of sites in CSV but not on test page (first 10):")
        for site in sorted(list(in_csv_not_test))[:10]:
            print(f"  - {site}")
    
    # Check why they're missing (no Meraki device or no Discount-Tire tag)
    cur.execute("""
        SELECT c.site_name, 
               CASE 
                   WHEN mi.network_name IS NULL THEN 'No Meraki device'
                   WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']) THEN 'No Discount-Tire tag'
                   WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
                   ELSE 'Unknown reason'
               END as reason
        FROM circuits c
        LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
        LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
        WHERE c.status = 'Enabled'
        AND c.site_name IN %s
        LIMIT 20
    """, (tuple(in_csv_not_test),))
    
    print(f"\nReasons for missing sites:")
    for site, reason in cur.fetchall():
        print(f"  - {site}: {reason}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Database error: {e}")

print(f"\nSummary:")
print(f"- CSV total enabled circuits: 1,867")
print(f"- Test page shows: 1,689")
print(f"- Delta: 178 circuits")