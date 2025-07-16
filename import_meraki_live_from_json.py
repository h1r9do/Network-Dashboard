#!/usr/bin/env python3
"""
Import Meraki live data from existing JSON file into database
This is a one-time import to quickly get all 1,296 networks into the database
"""

import json
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)

DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')
JSON_FILE = '/usr/local/bin/backups/migration_20250624_171253/www_html/meraki-data.bak/mx_inventory_live.json'

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    # Create table if not exists
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS meraki_live_data (
            id SERIAL PRIMARY KEY,
            network_name VARCHAR(255) NOT NULL,
            network_id VARCHAR(100),
            device_serial VARCHAR(100),
            device_model VARCHAR(50),
            device_name VARCHAR(255),
            device_tags TEXT,
            wan1_provider_label VARCHAR(255),
            wan1_speed VARCHAR(100),
            wan1_ip VARCHAR(45),
            wan1_provider VARCHAR(255),
            wan1_provider_comparison VARCHAR(50),
            wan2_provider_label VARCHAR(255),
            wan2_speed VARCHAR(100),
            wan2_ip VARCHAR(45),
            wan2_provider VARCHAR(255),
            wan2_provider_comparison VARCHAR(50),
            raw_notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(network_name)
        )
    """))
    session.commit()
    
    # Load JSON data
    logging.info(f"Loading JSON from {JSON_FILE}")
    with open(JSON_FILE, 'r') as f:
        meraki_data = json.load(f)
    
    logging.info(f"Found {len(meraki_data)} networks in JSON")
    
    # Clear existing data
    session.execute(text("DELETE FROM meraki_live_data"))
    session.commit()
    
    # Import each network
    count = 0
    for item in meraki_data:
        session.execute(text("""
            INSERT INTO meraki_live_data (
                network_name, network_id, device_serial, device_model, device_name,
                device_tags, wan1_provider_label, wan1_speed, wan1_ip, wan1_provider,
                wan1_provider_comparison, wan2_provider_label, wan2_speed, wan2_ip,
                wan2_provider, wan2_provider_comparison, raw_notes
            ) VALUES (
                :network_name, :network_id, :device_serial, :device_model, :device_name,
                :device_tags, :wan1_provider_label, :wan1_speed, :wan1_ip, :wan1_provider,
                :wan1_provider_comparison, :wan2_provider_label, :wan2_speed, :wan2_ip,
                :wan2_provider, :wan2_provider_comparison, :raw_notes
            )
            ON CONFLICT (network_name) DO UPDATE SET
                network_id = EXCLUDED.network_id,
                device_serial = EXCLUDED.device_serial,
                device_model = EXCLUDED.device_model,
                device_name = EXCLUDED.device_name,
                device_tags = EXCLUDED.device_tags,
                wan1_provider_label = EXCLUDED.wan1_provider_label,
                wan1_speed = EXCLUDED.wan1_speed,
                wan1_ip = EXCLUDED.wan1_ip,
                wan1_provider = EXCLUDED.wan1_provider,
                wan1_provider_comparison = EXCLUDED.wan1_provider_comparison,
                wan2_provider_label = EXCLUDED.wan2_provider_label,
                wan2_speed = EXCLUDED.wan2_speed,
                wan2_ip = EXCLUDED.wan2_ip,
                wan2_provider = EXCLUDED.wan2_provider,
                wan2_provider_comparison = EXCLUDED.wan2_provider_comparison,
                raw_notes = EXCLUDED.raw_notes,
                last_updated = CURRENT_TIMESTAMP
        """), {
            'network_name': item.get('network_name', ''),
            'network_id': item.get('network_id', ''),
            'device_serial': item.get('device_serial', ''),
            'device_model': item.get('device_model', ''),
            'device_name': item.get('device_name', ''),
            'device_tags': json.dumps(item.get('device_tags', [])),
            'wan1_provider_label': item.get('wan1', {}).get('provider_label', ''),
            'wan1_speed': item.get('wan1', {}).get('speed', ''),
            'wan1_ip': item.get('wan1', {}).get('ip', ''),
            'wan1_provider': item.get('wan1', {}).get('provider', ''),
            'wan1_provider_comparison': item.get('wan1', {}).get('provider_comparison', ''),
            'wan2_provider_label': item.get('wan2', {}).get('provider_label', ''),
            'wan2_speed': item.get('wan2', {}).get('speed', ''),
            'wan2_ip': item.get('wan2', {}).get('ip', ''),
            'wan2_provider': item.get('wan2', {}).get('provider', ''),
            'wan2_provider_comparison': item.get('wan2', {}).get('provider_comparison', ''),
            'raw_notes': item.get('raw_notes', '')
        })
        
        count += 1
        if count % 100 == 0:
            session.commit()
            logging.info(f"Imported {count} networks")
    
    session.commit()
    logging.info(f"Successfully imported {count} networks into meraki_live_data table")
    
    session.close()

if __name__ == "__main__":
    main()