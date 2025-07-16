#!/usr/bin/env python3
"""
Check parsing error for FLT 02 and GAA 01
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import Config

# Create database connection
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

print("Checking sites FLT 02 and GAA 01...\n")

query = text("""
    SELECT network_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider, 
           device_notes, last_updated 
    FROM enriched_circuits 
    WHERE network_name IN ('FLT 02', 'GAA 01')
    ORDER BY network_name
""")

with engine.connect() as conn:
    results = conn.execute(query).fetchall()
    
    if not results:
        print("No data found for FLT 02 or GAA 01")
    else:
        for row in results:
            print(f"Site: {row[0]}")
            print(f"  WAN1 Speed: '{row[1]}'")
            print(f"  WAN1 Provider: '{row[3]}'")
            print(f"  WAN2 Speed: '{row[2]}'")
            print(f"  WAN2 Provider: '{row[4]}'")
            print(f"  Last Updated: {row[6]}")
            
            # Show device notes
            if row[5]:
                print(f"\n  Device Notes (raw):")
                print(f"  {repr(row[5][:300])}")
                
                # Try to parse the notes to see what's in there
                import re
                # Look for speed patterns
                speed_patterns = re.findall(r'(\d+\.?\d*\s*[MG])', row[5], re.IGNORECASE)
                if speed_patterns:
                    print(f"\n  Speed patterns found in notes: {speed_patterns}")
                
                # Look for x patterns (e.g., "300.0M x 35.0M")
                x_patterns = re.findall(r'(\d+\.?\d*\s*[MG]\s*x\s*\d+\.?\d*\s*[MG])', row[5], re.IGNORECASE)
                if x_patterns:
                    print(f"  'x' patterns found in notes: {x_patterns}")
            
            print("\n" + "-"*60 + "\n")

# Also check what the raw Meraki inventory has
print("\nChecking Meraki inventory for these sites...\n")

inventory_query = text("""
    SELECT network_name, device_name, device_notes, model
    FROM meraki_inventory
    WHERE network_name IN ('FLT 02', 'GAA 01')
    ORDER BY network_name, device_name
""")

with engine.connect() as conn:
    results = conn.execute(inventory_query).fetchall()
    
    for row in results:
        print(f"Network: {row[0]}, Device: {row[1]}, Model: {row[3]}")
        if row[2]:
            print(f"  Notes: {repr(row[2][:200])}")
        print()