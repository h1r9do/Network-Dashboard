#!/usr/bin/env python3
"""
Check database schema and investigate Frontier matching
"""

import psycopg2

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

# Connect to database
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# First check the actual columns in circuits table
print("=== Circuits table columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'circuits'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

# Check enriched_circuits columns
print("\n=== Enriched_circuits table columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'enriched_circuits'
    AND column_name LIKE '%provider%'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

cur.close()
conn.close()