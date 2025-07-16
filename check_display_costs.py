#!/usr/bin/env python3
"""
Check what costs are being displayed vs what's in the database
"""

import os
import sys
import json
from sqlalchemy import create_engine, text, func, or_
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
from models import Circuit, EnrichedCircuit

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
JSON_FILE = "/var/www/html/circuitinfo/master_circuit_data_20250701_150111.json"

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

# Check a few specific sites
test_sites = ['ARL 05', 'ALB 03', 'AZC 01']

for site in test_sites:
    print(f"\n=== {site} ===")
    
    # Check enriched_circuits (what the page queries)
    enriched = session.query(EnrichedCircuit).filter(
        func.lower(EnrichedCircuit.network_name) == func.lower(site)
    ).first()
    
    if enriched:
        print(f"Enriched Circuits Table:")
        print(f"  WAN1: {enriched.wan1_provider} / {enriched.wan1_monthly_cost}")
        print(f"  WAN2: {enriched.wan2_provider} / {enriched.wan2_monthly_cost}")
    
    # Check circuits table (DSR data)
    circuits = session.query(Circuit).filter(
        func.lower(Circuit.site_name) == func.lower(site),
        Circuit.status == 'Enabled'
    ).all()
    
    print(f"\nCircuits Table (DSR):")
    for c in circuits:
        print(f"  {c.circuit_purpose}: {c.provider_name} / ${c.billing_monthly_cost}")

# Count how many enriched circuits have $0.00 costs
result = session.execute(text("""
    SELECT COUNT(*) 
    FROM enriched_circuits 
    WHERE (wan1_monthly_cost = '$0.00' OR wan2_monthly_cost = '$0.00')
    AND (wan1_speed NOT LIKE '%Cell%' AND wan1_speed NOT LIKE '%Satellite%'
         AND wan2_speed NOT LIKE '%Cell%' AND wan2_speed NOT LIKE '%Satellite%')
"""))

count = result.scalar()
print(f"\n\nTotal enriched circuits with $0.00 non-cell costs: {count}")

# Now check which sites have costs in JSON but not in circuits table
print("\n\nChecking for missing costs that are in master JSON...")

# Load JSON
with open(JSON_FILE, 'r') as f:
    master_data = json.load(f)

master_lookup = {record.get('Store', '').upper(): record for record in master_data}

# Get all sites with $0 costs in enriched table
result = session.execute(text("""
    SELECT DISTINCT network_name
    FROM enriched_circuits
    WHERE (wan1_monthly_cost = '$0.00' OR wan2_monthly_cost = '$0.00')
    ORDER BY network_name
    LIMIT 20
"""))

print("\nFirst 20 sites with $0.00 costs:")
for (site_name,) in result:
    if site_name.upper() in master_lookup:
        master = master_lookup[site_name.upper()]
        mrc1 = master.get('MRC', 0)
        mrc2 = master.get('MRC3', 0)
        if mrc1 or mrc2:
            print(f"  {site_name}: Master has Circuit A=${mrc1}, Circuit B=${mrc2}")

session.close()