#!/usr/bin/env python3
"""
Check ARL 05 data in database and JSON file
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
JSON_FILE = "/var/www/html/circuitinfo/master_circuit_data_20250701_150111.json"

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

print("=== Checking ARL 05 in Database ===\n")

# Check circuits table (DSR data)
print("1. circuits table (DSR source):")
result = session.execute(text("""
    SELECT site_name, circuit_purpose, provider_name, 
           details_ordered_service_speed, billing_monthly_cost, status
    FROM circuits 
    WHERE LOWER(site_name) = 'arl 05'
    ORDER BY circuit_purpose
"""))

for row in result:
    print(f"  Site: {row[0]}")
    print(f"  Purpose: {row[1]}")
    print(f"  Provider: {row[2]}")
    print(f"  Speed: {row[3]}")
    print(f"  Cost: ${row[4] if row[4] else 0}")
    print(f"  Status: {row[5]}")
    print()

# Check enriched_circuits table
print("\n2. enriched_circuits table:")
result = session.execute(text("""
    SELECT network_name, 
           wan1_provider, wan1_speed, wan1_monthly_cost,
           wan2_provider, wan2_speed, wan2_monthly_cost
    FROM enriched_circuits 
    WHERE LOWER(network_name) = 'arl 05'
"""))

row = result.fetchone()
if row:
    print(f"  Network: {row[0]}")
    print(f"  WAN1: {row[1]} / {row[2]} / {row[3]}")
    print(f"  WAN2: {row[4]} / {row[5]} / {row[6]}")
else:
    print("  No record found")

# Check JSON file
print("\n\n=== Checking ARL 05 in Master JSON ===")
with open(JSON_FILE, 'r') as f:
    master_data = json.load(f)

for record in master_data:
    if record.get('Store', '').upper() == 'ARL 05':
        print(f"  Store: {record.get('Store')}")
        print(f"  Circuit A: {record.get('Active A Circuit Carrier')} / {record.get('Active A Speed')} / ${record.get('MRC', 0)}")
        print(f"  Circuit B: {record.get('Active B Circuit Carrier')} / {record.get('Active B Speed')} / ${record.get('MRC3', 0)}")
        break

session.close()