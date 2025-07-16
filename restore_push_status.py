#!/usr/bin/env python3
"""
Restore push status from pushed_sites_log.json
"""

import json
import psycopg2
from datetime import datetime
import re

# Database connection
def get_db_connection():
    import re
    from config import Config
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

# Load pushed sites log
with open('/var/www/html/meraki-data/pushed_sites_log.json', 'r') as f:
    pushed_sites = json.load(f)

print(f"Found {len(pushed_sites)} sites in pushed log")

# Update database
conn = get_db_connection()
cursor = conn.cursor()

updated_count = 0
for site in pushed_sites:
    cursor.execute("""
        UPDATE enriched_circuits 
        SET pushed_to_meraki = TRUE,
            pushed_date = %s
        WHERE network_name = %s
    """, (datetime(2025, 6, 26, 12, 0, 0), site))  # Set to yesterday noon
    
    if cursor.rowcount > 0:
        updated_count += 1
        print(f"✓ Updated {site}")
    else:
        print(f"✗ No match for {site}")

conn.commit()
cursor.close()
conn.close()

print(f"\nUpdated {updated_count} sites as pushed to Meraki")