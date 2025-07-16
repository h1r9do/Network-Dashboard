#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='dsrcircuits',
    user='dsruser',
    password='dsrpass123'
)
cursor = conn.cursor()

# Check data
cursor.execute('SELECT COUNT(*) FROM circuits_dev')
print(f'Records in circuits_dev: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM enriched_circuits_dev')
print(f'Records in enriched_circuits_dev: {cursor.fetchone()[0]}')

# Check CAN 35
print('\nCAN 35 data:')
cursor.execute("""
    SELECT provider_name, billing_monthly_cost, circuit_purpose
    FROM circuits_dev
    WHERE site_name = 'CAN 35'
""")
for row in cursor.fetchall():
    print(f'  circuits_dev: {row[0]} - ${row[1] or 0} - {row[2]}')

cursor.execute("""
    SELECT wan1_provider, wan1_speed
    FROM enriched_circuits_dev
    WHERE network_name = 'CAN 35'
""")
row = cursor.fetchone()
if row:
    print(f'  enriched_dev: WAN1={row[0]} - {row[1]}')

conn.close()