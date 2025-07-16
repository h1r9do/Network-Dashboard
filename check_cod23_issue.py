#!/usr/bin/env python3
import psycopg2
import re
from config import Config

# Get database connection
def get_db_connection():
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

conn = get_db_connection()
cursor = conn.cursor()

# Check COD 23 in various tables
print("=== COD 23 Investigation ===")

# Check circuits table
cursor.execute("""
    SELECT circuit_purpose, provider_name, status, ip_address_start, 
           details_ordered_service_speed, billing_monthly_cost
    FROM circuits 
    WHERE site_name = 'COD 23'
    ORDER BY circuit_purpose
""")
circuits = cursor.fetchall()
print("\nCircuits table:")
for row in circuits:
    print(f"  {row[0]}: {row[1]} - {row[2]} - IP: {row[3]} - Speed: {row[4]} - Cost: ${row[5]}")

# Check meraki_inventory
cursor.execute("""
    SELECT network_name, device_serial, wan1_ip, wan2_ip
    FROM meraki_inventory 
    WHERE network_name = 'COD 23'
""")
meraki = cursor.fetchall()
print("\nMeraki inventory:")
for row in meraki:
    print(f"  {row[0]}: Serial={row[1]}, WAN1_IP={row[2]}, WAN2_IP={row[3]}")

# Check enriched_circuits
cursor.execute("""
    SELECT network_name, wan1_provider, wan1_speed, wan1_confirmed,
           wan2_provider, wan2_speed, wan2_confirmed
    FROM enriched_circuits 
    WHERE network_name = 'COD 23'
""")
enriched = cursor.fetchall()
print("\nEnriched circuits:")
for row in enriched:
    print(f"  {row[0]}: WAN1='{row[1]}' {row[2]} (confirmed={row[3]}), WAN2='{row[4]}' {row[5]} (confirmed={row[6]})")

# Check raw Meraki notes
print("\n=== Checking another problematic site: TXS 24 ===")
cursor.execute("""
    SELECT circuit_purpose, provider_name, status, ip_address_start
    FROM circuits 
    WHERE site_name = 'TXS 24'
    ORDER BY circuit_purpose
""")
circuits = cursor.fetchall()
print("\nTXS 24 Circuits:")
for row in circuits:
    print(f"  {row[0]}: {row[1]} - {row[2]} - IP: {row[3]}")

cursor.close()
conn.close()