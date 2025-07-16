#!/usr/bin/env python3
"""Update just AZN 02 with the correct ARIN provider"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')
from sqlalchemy import create_engine, text
from config import Config
from datetime import datetime

def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Update AZN 02
        result = conn.execute(text('''
            UPDATE meraki_inventory
            SET wan1_arin_provider = 'Cable One, Inc.',
                last_updated = :updated
            WHERE network_name = 'AZN 02'
            AND device_model LIKE 'MX%'
        '''), {'updated': datetime.now()})
        
        conn.commit()
        
        print(f"Updated {result.rowcount} rows for AZN 02")
        
        # Verify the update
        result = conn.execute(text('''
            SELECT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE network_name = 'AZN 02'
            AND device_model LIKE 'MX%'
        '''))
        
        row = result.fetchone()
        if row:
            print("\nVerification:")
            print(f"  Network: {row[0]}")
            print(f"  WAN1: {row[1]} → {row[2]}")
            print(f"  WAN2: {row[3]} → {row[4]}")

if __name__ == "__main__":
    main()