#!/usr/bin/env python3
"""Direct update test"""

import psycopg2
from config import Config
import re
from datetime import datetime, timezone

# Get database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(
    host=host,
    port=int(port),
    database=database,
    user=user,
    password=password
)

cursor = conn.cursor()

# Direct update of NYB 01
cursor.execute("""
    UPDATE meraki_inventory
    SET wan1_ip = '208.105.133.178',
        wan2_ip = '107.127.197.80',
        wan1_arin_provider = 'AT&T',
        wan2_arin_provider = 'Charter Communications',
        last_updated = %s
    WHERE device_serial = 'Q2KY-4RP7-4FN8'
""", (datetime.now(timezone.utc),))

print(f"Updated {cursor.rowcount} rows")

# Verify
cursor.execute("""
    SELECT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
    FROM meraki_inventory
    WHERE device_serial = 'Q2KY-4RP7-4FN8'
""")

result = cursor.fetchone()
if result:
    print(f"Network: {result[0]}")
    print(f"WAN1 IP: {result[1]}")
    print(f"WAN2 IP: {result[2]}")
    print(f"WAN1 ARIN: {result[3]}")
    print(f"WAN2 ARIN: {result[4]}")

conn.commit()
cursor.close()
conn.close()

print("\nTesting confirm_site now...")
from confirm_meraki_notes_db_fixed import confirm_site
import json
result = confirm_site('NYB 01')
print(f"WAN1 IP from confirm_site: {result.get('wan1_ip')}")
print(f"WAN2 IP from confirm_site: {result.get('wan2_ip')}")