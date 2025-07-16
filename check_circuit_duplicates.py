#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re

# Get database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Checking for duplicate circuits in database")
print("=" * 80)

# List from user (unique Site IDs expected)
expected_circuits = [
    ("INI 06", "INI 06 -B", "Secondary"),
    ("LAS 03", "LAS 03", "Primary"),
    ("MIL 28", "MIL 28", "Primary"),
    ("MSG 01", "MSG 01- B", "Secondary"),
    ("NMA 05", "NMA 05-B- B", "Secondary"),
    ("NMA 06", "NMA 06- B", "Secondary"),
    ("TXD 60", "TXD 60- B", "Secondary"),
    ("TXD 76", "TXD 76- B", "Secondary"),
    ("TXH 97", "TXH 97 -B", "Secondary"),
    ("TXS 24", "TXS 24- B", "Secondary")
]

# Check what's actually in the database
cursor.execute("""
    SELECT site_name, site_id, circuit_purpose, fingerprint, COUNT(*) as count
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
    GROUP BY site_name, site_id, circuit_purpose, fingerprint
    ORDER BY site_name, site_id
""")

print("\nDatabase contents (Ready for Enablement circuits):")
print("-" * 80)
print(f"{'Site Name':15} | {'Site ID':15} | {'Purpose':10} | {'Count':5} | {'Fingerprint':40}")
print("-" * 80)

db_circuits = cursor.fetchall()
for row in db_circuits:
    fingerprint = row[3] if row[3] else "N/A"
    print(f"{row[0]:15} | {row[1]:15} | {row[2]:10} | {row[4]:5} | {fingerprint[:40]}")

# Check for duplicates by fingerprint
cursor.execute("""
    SELECT fingerprint, COUNT(*) as count
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
    GROUP BY fingerprint
    HAVING COUNT(*) > 1
""")

duplicates = cursor.fetchall()
if duplicates:
    print("\n\nDUPLICATE FINGERPRINTS FOUND:")
    print("-" * 50)
    for dup in duplicates:
        print(f"Fingerprint: {dup[0]} - Count: {dup[1]}")
        
        # Show details of duplicates
        cursor.execute("""
            SELECT id, site_name, site_id, circuit_purpose, created_at, updated_at
            FROM circuits 
            WHERE fingerprint = %s AND LOWER(status) = 'ready for enablement'
            ORDER BY created_at
        """, (dup[0],))
        
        for detail in cursor.fetchall():
            print(f"  ID: {detail[0]}, Created: {detail[4]}, Updated: {detail[5]}")

# Compare with expected list
print("\n\nCOMPARISON WITH EXPECTED LIST:")
print("-" * 80)

# Get unique site IDs from database
cursor.execute("""
    SELECT DISTINCT site_id
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
    ORDER BY site_id
""")
db_site_ids = [row[0] for row in cursor.fetchall()]

expected_site_ids = [circuit[1] for circuit in expected_circuits]

print(f"Expected circuits: {len(expected_site_ids)}")
print(f"Database circuits: {len(db_site_ids)}")

# Find missing and extra
missing = set(expected_site_ids) - set(db_site_ids)
extra = set(db_site_ids) - set(expected_site_ids)

if missing:
    print(f"\nMissing from database: {missing}")
    
if extra:
    print(f"\nExtra in database: {extra}")

# Check if ARL 08 is in the database
print("\n\nChecking for ARL 08 (should be from July 2):")
cursor.execute("""
    SELECT site_name, site_id, status, updated_at
    FROM circuits 
    WHERE site_id LIKE 'ARL 08%'
""")
arl_results = cursor.fetchall()
if arl_results:
    for row in arl_results:
        print(f"  {row[0]} | {row[1]} | {row[2]} | Updated: {row[3]}")
else:
    print("  ARL 08 not found in database")

cursor.close()
conn.close()