#!/usr/bin/env python3
"""
Fix enriched_circuits where speed is 'Cell' but provider is blank
Sets provider to 'Cell' when speed is 'Cell'
"""
import psycopg2
import re
from datetime import datetime
from config import Config

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

print("Fixing enriched_circuits where speed is 'Cell' but provider is blank...")

# Fix WAN1
cursor.execute("""
    UPDATE enriched_circuits
    SET wan1_provider = 'Cell',
        last_updated = CURRENT_TIMESTAMP
    WHERE wan1_speed = 'Cell' 
    AND (wan1_provider = '' OR wan1_provider IS NULL)
""")
wan1_fixed = cursor.rowcount
print(f"Fixed {wan1_fixed} WAN1 entries")

# Fix WAN2
cursor.execute("""
    UPDATE enriched_circuits
    SET wan2_provider = 'Cell',
        last_updated = CURRENT_TIMESTAMP
    WHERE wan2_speed = 'Cell' 
    AND (wan2_provider = '' OR wan2_provider IS NULL)
""")
wan2_fixed = cursor.rowcount
print(f"Fixed {wan2_fixed} WAN2 entries")

# Commit changes
conn.commit()

print(f"\nTotal fixed: {wan1_fixed + wan2_fixed} entries")

# Verify the fix
cursor.execute("""
    SELECT 
        COUNT(CASE WHEN wan1_speed = 'Cell' AND (wan1_provider = '' OR wan1_provider IS NULL) THEN 1 END) as wan1_remaining,
        COUNT(CASE WHEN wan2_speed = 'Cell' AND (wan2_provider = '' OR wan2_provider IS NULL) THEN 1 END) as wan2_remaining
    FROM enriched_circuits
""")
remaining = cursor.fetchone()
print(f"\nVerification - Remaining unfixed:")
print(f"  WAN1: {remaining[0]}")
print(f"  WAN2: {remaining[1]}")

# Show some examples of fixed entries
cursor.execute("""
    SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
    FROM enriched_circuits
    WHERE (wan1_provider = 'Cell' AND wan1_speed = 'Cell')
       OR (wan2_provider = 'Cell' AND wan2_speed = 'Cell')
    ORDER BY network_name
    LIMIT 10
""")

print("\nSample of fixed entries:")
for row in cursor.fetchall():
    if row[1] == 'Cell' and row[2] == 'Cell':
        print(f"  {row[0]}: WAN1 = Cell/Cell")
    if row[3] == 'Cell' and row[4] == 'Cell':
        print(f"  {row[0]}: WAN2 = Cell/Cell")

cursor.close()
conn.close()

print("\n✓ Fix complete!")