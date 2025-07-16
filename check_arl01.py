#!/usr/bin/env python3
"""
Check ARL 01 data in all tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

print("=== Checking ARL 01 ===\n")

# Check circuits table (DSR data)
print("1. DSR Data (circuits table):")
result = session.execute(text("""
    SELECT circuit_purpose, provider_name, details_ordered_service_speed, 
           billing_monthly_cost, status
    FROM circuits 
    WHERE LOWER(site_name) = 'arl 01' AND status = 'Enabled'
    ORDER BY circuit_purpose
"""))

for row in result:
    print(f"   {row[0]}: {row[1]} / {row[2]} / ${row[3]}")

# Check enriched_circuits table
print("\n2. Enriched Circuits Data:")
result = session.execute(text("""
    SELECT wan1_provider, wan1_speed, wan1_monthly_cost, wan1_circuit_role,
           wan2_provider, wan2_speed, wan2_monthly_cost, wan2_circuit_role
    FROM enriched_circuits 
    WHERE LOWER(network_name) = 'arl 01'
"""))

row = result.fetchone()
if row:
    print(f"   WAN1: {row[0]} / {row[1]} / {row[2]} / Role: {row[3]}")
    print(f"   WAN2: {row[4]} / {row[5]} / {row[6]} / Role: {row[7]}")

# Check meraki_inventory for ARIN data
print("\n3. Meraki Inventory (ARIN) Data:")
result = session.execute(text("""
    SELECT wan1_ip, wan1_arin_provider, wan1_provider_label,
           wan2_ip, wan2_arin_provider, wan2_provider_label
    FROM meraki_inventory
    WHERE LOWER(network_name) = 'arl 01'
"""))

row = result.fetchone()
if row:
    print(f"   WAN1: IP={row[0]}, ARIN={row[1]}, Label={row[2]}")
    print(f"   WAN2: IP={row[3]}, ARIN={row[4]}, Label={row[5]}")

session.close()