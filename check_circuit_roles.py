#!/usr/bin/env python3
"""
Check circuit role assignments in enriched_circuits table
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

print("=== Checking Circuit Role Assignments ===\n")

# Check if any WAN1 has Secondary role or WAN2 has Primary role
result = session.execute(text("""
    SELECT network_name, wan1_provider, wan1_circuit_role, wan2_provider, wan2_circuit_role
    FROM enriched_circuits
    WHERE wan1_circuit_role != 'Primary' OR wan2_circuit_role != 'Secondary'
    LIMIT 20
"""))

non_standard = result.fetchall()
if non_standard:
    print(f"Found {len(non_standard)} circuits with non-standard roles:")
    for row in non_standard:
        print(f"  {row[0]}: WAN1={row[2]}, WAN2={row[4]}")
else:
    print("All circuits have standard roles (WAN1=Primary, WAN2=Secondary)")

# Now check how this correlates with DSR data
print("\n\n=== Checking DSR Circuit Assignments ===")
print("Sites where DSR 'Secondary' circuit is on WAN1:\n")

result = session.execute(text("""
    SELECT ec.network_name, ec.wan1_provider, c.circuit_purpose, c.provider_name
    FROM enriched_circuits ec
    JOIN circuits c ON LOWER(ec.network_name) = LOWER(c.site_name)
    WHERE c.status = 'Enabled'
    AND LOWER(c.circuit_purpose) = 'secondary'
    AND UPPER(ec.wan1_provider) LIKE '%' || UPPER(SUBSTRING(c.provider_name, 1, 5)) || '%'
    LIMIT 20
"""))

matches = result.fetchall()
if matches:
    print(f"Found {len(matches)} cases where DSR Secondary is on WAN1:")
    for row in matches:
        print(f"  {row[0]}: WAN1={row[1]}, DSR={row[2]}/{row[3]}")
else:
    print("No matches found")

# Check the reverse - DSR Primary on WAN2
print("\n\nSites where DSR 'Primary' circuit is on WAN2:\n")

result = session.execute(text("""
    SELECT ec.network_name, ec.wan2_provider, c.circuit_purpose, c.provider_name
    FROM enriched_circuits ec
    JOIN circuits c ON LOWER(ec.network_name) = LOWER(c.site_name)
    WHERE c.status = 'Enabled'
    AND LOWER(c.circuit_purpose) = 'primary'
    AND UPPER(ec.wan2_provider) LIKE '%' || UPPER(SUBSTRING(c.provider_name, 1, 5)) || '%'
    LIMIT 20
"""))

matches = result.fetchall()
if matches:
    print(f"Found {len(matches)} cases where DSR Primary is on WAN2:")
    for row in matches:
        print(f"  {row[0]}: WAN2={row[1]}, DSR={row[2]}/{row[3]}")

session.close()