#!/usr/bin/env python3
"""
Import data from enriched_networks table to enriched_circuits table
This copies the already-processed data from the old enrichment run
"""

import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    try:
        # Clear enriched_circuits
        session.execute(text("DELETE FROM enriched_circuits"))
        session.commit()
        
        # Copy from enriched_networks to enriched_circuits
        result = session.execute(text("""
            INSERT INTO enriched_circuits (
                network_name, device_tags, 
                wan1_provider, wan1_speed, wan1_monthly_cost, wan1_circuit_role, wan1_confirmed,
                wan2_provider, wan2_speed, wan2_monthly_cost, wan2_circuit_role, wan2_confirmed
            )
            SELECT 
                network_name,
                '{}',  -- Empty array for now, will update later
                COALESCE((wan1_data::json->>'Provider'), ''),
                COALESCE((wan1_data::json->>'Speed'), 'Unknown'),
                COALESCE((wan1_data::json->>'Monthly Cost'), '$0.00'),
                COALESCE((wan1_data::json->>'Circuit Role'), 'Primary'),
                COALESCE((wan1_data::json->>'Confirmed')::boolean, false),
                COALESCE((wan2_data::json->>'Provider'), ''),
                COALESCE((wan2_data::json->>'Speed'), 'Unknown'),
                COALESCE((wan2_data::json->>'Monthly Cost'), '$0.00'),
                COALESCE((wan2_data::json->>'Circuit Role'), 'Secondary'),
                COALESCE((wan2_data::json->>'Confirmed')::boolean, false)
            FROM enriched_networks
            WHERE wan1_data IS NOT NULL
        """))
        
        count = result.rowcount
        session.commit()
        
        print(f"Imported {count} records from enriched_networks to enriched_circuits")
        
        # Now update device tags from meraki_live_data
        session.execute(text("""
            UPDATE enriched_circuits ec
            SET device_tags = COALESCE(
                (SELECT ARRAY(SELECT json_array_elements_text(device_tags::json))
                 FROM meraki_live_data mld
                 WHERE mld.network_name = ec.network_name
                 LIMIT 1), 
                '{}'::text[]
            )
        """))
        
        session.commit()
        print("Updated device tags from meraki_live_data")
        
        # Get counts
        result = session.execute(text("SELECT COUNT(*) FROM enriched_circuits"))
        total = result.scalar()
        
        result = session.execute(text("""
            SELECT COUNT(*) FROM enriched_circuits 
            WHERE array_to_string(device_tags, ',') ILIKE '%hub%'
               OR array_to_string(device_tags, ',') ILIKE '%lab%'
               OR array_to_string(device_tags, ',') ILIKE '%voice%'
        """))
        filtered = result.scalar()
        
        print(f"\nTotal enriched circuits: {total}")
        print(f"Would be filtered by hub/lab/voice tags: {filtered}")
        print(f"Remaining after filter: {total - filtered}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()