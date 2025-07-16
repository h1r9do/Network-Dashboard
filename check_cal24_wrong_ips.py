#!/usr/bin/env python3
"""Check where the wrong IPs are coming from for CAL 24"""

import psycopg2

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser'
db_pass = 'dsrpass123'

conn = psycopg2.connect(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_pass
)
cur = conn.cursor()

print("=== Checking all CAL 24 related data ===\n")

# 1. Check enriched_circuits
print("1. Enriched Circuits table:")
cur.execute("""
    SELECT 
        id,
        network_name,
        wan1_ip,
        wan2_ip,
        wan1_provider,
        wan2_provider,
        wan1_arin_org,
        wan2_arin_org,
        last_updated
    FROM enriched_circuits 
    WHERE LOWER(network_name) = 'cal 24'
""")
enriched = cur.fetchall()
for row in enriched:
    print(f"  ID: {row[0]}")
    print(f"  Network: {row[1]}")
    print(f"  WAN1 IP: {row[2]} (Provider: {row[4]}, ARIN: {row[6]})")
    print(f"  WAN2 IP: {row[3]} (Provider: {row[5]}, ARIN: {row[7]})")
    print(f"  Last Updated: {row[8]}\n")

# 2. Check meraki_inventory
print("2. Meraki Inventory table:")
cur.execute("""
    SELECT 
        device_serial,
        network_name,
        wan1_ip,
        wan2_ip,
        wan1_public_ip,
        wan2_public_ip,
        wan1_arin_provider,
        wan2_arin_provider,
        last_updated
    FROM meraki_inventory 
    WHERE LOWER(network_name) = 'cal 24'
""")
meraki = cur.fetchall()
for row in meraki:
    print(f"  Serial: {row[0]}")
    print(f"  Network: {row[1]}")
    print(f"  WAN1 IP: {row[2]}, Public IP: {row[4]}, ARIN: {row[6]}")
    print(f"  WAN2 IP: {row[3]}, Public IP: {row[5]}, ARIN: {row[7]}")
    print(f"  Last Updated: {row[8]}\n")

# 3. Check if these wrong IPs exist elsewhere
print("3. Searching for the wrong IPs (45.19.143.81 and 96.81.191.61):")

# Search in enriched_circuits
cur.execute("""
    SELECT network_name, wan1_ip, wan2_ip 
    FROM enriched_circuits 
    WHERE wan1_ip = '45.19.143.81' OR wan2_ip = '45.19.143.81' 
       OR wan1_ip = '96.81.191.61' OR wan2_ip = '96.81.191.61'
""")
wrong_ips_enriched = cur.fetchall()
print(f"  Found in enriched_circuits: {len(wrong_ips_enriched)} records")
for row in wrong_ips_enriched:
    print(f"    Network: {row[0]}, WAN1: {row[1]}, WAN2: {row[2]}")

# Search in meraki_inventory
cur.execute("""
    SELECT network_name, wan1_ip, wan2_ip, wan1_public_ip, wan2_public_ip
    FROM meraki_inventory 
    WHERE wan1_ip = '45.19.143.81' OR wan2_ip = '45.19.143.81' 
       OR wan1_ip = '96.81.191.61' OR wan2_ip = '96.81.191.61'
       OR wan1_public_ip = '45.19.143.81' OR wan2_public_ip = '45.19.143.81'
       OR wan1_public_ip = '96.81.191.61' OR wan2_public_ip = '96.81.191.61'
""")
wrong_ips_meraki = cur.fetchall()
print(f"\n  Found in meraki_inventory: {len(wrong_ips_meraki)} records")
for row in wrong_ips_meraki:
    print(f"    Network: {row[0]}, WAN1: {row[1]}, WAN2: {row[2]}, Public1: {row[3]}, Public2: {row[4]}")

# 4. Check what the ARIN refresh is looking at
print("\n4. What data source is being used:")
print("  Expected IPs from Meraki:")
print("    WAN1: 47.176.12.58 (Frontier)")
print("    WAN2: 166.211.206.131 (Verizon)")
print("\n  Wrong IPs shown in modal:")
print("    WAN1: 45.19.143.81 (Tonya Woody)")
print("    WAN2: 96.81.191.61 (Comcast)")

conn.close()