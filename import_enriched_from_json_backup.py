#!/usr/bin/env python3
"""
Import enriched circuits from JSON backup files
"""

import json
import os
import glob
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')
BACKUP_DIR = '/usr/local/bin/backups/migration_20250624_171253/www_html/meraki-data'

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    try:
        # Find latest enriched JSON
        json_files = glob.glob(os.path.join(BACKUP_DIR, 'mx_inventory_enriched_*.json'))
        if not json_files:
            print("No enriched JSON files found")
            return
            
        latest_json = sorted(json_files)[-1]
        print(f"Loading from {latest_json}")
        
        with open(latest_json, 'r') as f:
            enriched_data = json.load(f)
        
        print(f"Found {len(enriched_data)} networks in JSON")
        
        # Clear enriched_circuits
        session.execute(text("DELETE FROM enriched_circuits"))
        session.commit()
        
        # Import each network
        count = 0
        for network in enriched_data:
            # Convert device_tags list to PostgreSQL array format
            device_tags = network.get('device_tags', [])
            
            session.execute(text("""
                INSERT INTO enriched_circuits (
                    network_name, device_tags,
                    wan1_provider, wan1_speed, wan1_monthly_cost, wan1_circuit_role, wan1_confirmed,
                    wan2_provider, wan2_speed, wan2_monthly_cost, wan2_circuit_role, wan2_confirmed
                ) VALUES (
                    :network_name, :device_tags,
                    :wan1_provider, :wan1_speed, :wan1_monthly_cost, :wan1_circuit_role, :wan1_confirmed,
                    :wan2_provider, :wan2_speed, :wan2_monthly_cost, :wan2_circuit_role, :wan2_confirmed
                )
            """), {
                'network_name': network.get('network_name', ''),
                'device_tags': device_tags,  # Pass as list, SQLAlchemy will convert to array
                'wan1_provider': network.get('wan1', {}).get('provider', ''),
                'wan1_speed': network.get('wan1', {}).get('speed', 'Unknown'),
                'wan1_monthly_cost': network.get('wan1', {}).get('monthly_cost', '$0.00'),
                'wan1_circuit_role': network.get('wan1', {}).get('circuit_role', 'Primary'),
                'wan1_confirmed': network.get('wan1', {}).get('confirmed', False),
                'wan2_provider': network.get('wan2', {}).get('provider', ''),
                'wan2_speed': network.get('wan2', {}).get('speed', 'Unknown'),
                'wan2_monthly_cost': network.get('wan2', {}).get('monthly_cost', '$0.00'),
                'wan2_circuit_role': network.get('wan2', {}).get('circuit_role', 'Secondary'),
                'wan2_confirmed': network.get('wan2', {}).get('confirmed', False)
            })
            
            count += 1
            if count % 100 == 0:
                session.commit()
                print(f"Imported {count} networks")
        
        session.commit()
        print(f"Successfully imported {count} enriched circuits")
        
        # Get statistics
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT 
                    CASE 
                        WHEN 'hub' = ANY(device_tags) OR 'lab' = ANY(device_tags) OR 'voice' = ANY(device_tags) 
                        THEN network_name 
                    END
                ) as filtered,
                SUM(CASE WHEN wan1_confirmed = true THEN 1 ELSE 0 END) as wan1_confirmed,
                SUM(CASE WHEN wan2_confirmed = true THEN 1 ELSE 0 END) as wan2_confirmed,
                SUM(CASE WHEN wan1_circuit_role = 'Secondary' THEN 1 ELSE 0 END) as wan1_secondary,
                SUM(CASE WHEN wan2_circuit_role = 'Primary' THEN 1 ELSE 0 END) as wan2_primary
            FROM enriched_circuits
        """))
        
        stats = result.fetchone()
        print(f"\nStatistics:")
        print(f"  Total networks: {stats[0]}")
        print(f"  Would be filtered (hub/lab/voice): {stats[1]}")
        print(f"  Remaining after filter: {stats[0] - stats[1]}")
        print(f"  WAN1 confirmed: {stats[2]}")
        print(f"  WAN2 confirmed: {stats[3]}")
        print(f"  WAN1 with Secondary role: {stats[4]} (DSR thinks it's secondary but on WAN1)")
        print(f"  WAN2 with Primary role: {stats[5]} (DSR thinks it's primary but on WAN2)")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()