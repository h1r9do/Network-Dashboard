#!/usr/bin/env python3
"""
Simple inventory migration to populate database from JSON with basic schema
"""

import json
import os
import sys
import psycopg2
import re
from config import Config

def get_db_connection():
    """Get database connection"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def migrate_inventory():
    """Migrate inventory data with basic SQL"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create simple tables
        print("Creating inventory tables...")
        
        cursor.execute("""
            DROP TABLE IF EXISTS inventory_summary CASCADE;
            CREATE TABLE inventory_summary (
                id SERIAL PRIMARY KEY,
                model VARCHAR(50) UNIQUE NOT NULL,
                total_count INTEGER DEFAULT 0,
                org_counts TEXT,
                announcement_date VARCHAR(20),
                end_of_sale VARCHAR(20),
                end_of_support VARCHAR(20),
                highlight VARCHAR(20)
            );
        """)
        
        cursor.execute("""
            DROP TABLE IF EXISTS inventory_devices CASCADE;
            CREATE TABLE inventory_devices (
                id SERIAL PRIMARY KEY,
                serial VARCHAR(50) UNIQUE NOT NULL,
                model VARCHAR(50) NOT NULL,
                organization VARCHAR(100) NOT NULL,
                network_id VARCHAR(50),
                network_name VARCHAR(100),
                name VARCHAR(100),
                mac VARCHAR(20),
                lan_ip VARCHAR(45),
                firmware VARCHAR(50),
                product_type VARCHAR(50),
                tags TEXT,
                notes TEXT,
                details TEXT
            );
        """)
        
        conn.commit()
        print("✅ Created inventory tables")
        
        # Migrate summary data
        summary_file = '/var/www/html/meraki-data/meraki_inventory_summary.json'
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
            
            for item in summary_data.get('summary', []):
                cursor.execute("""
                    INSERT INTO inventory_summary 
                    (model, total_count, org_counts, announcement_date, end_of_sale, end_of_support, highlight)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (model) DO UPDATE SET
                    total_count = EXCLUDED.total_count,
                    org_counts = EXCLUDED.org_counts,
                    announcement_date = EXCLUDED.announcement_date,
                    end_of_sale = EXCLUDED.end_of_sale,
                    end_of_support = EXCLUDED.end_of_support,
                    highlight = EXCLUDED.highlight
                """, (
                    item['model'],
                    item.get('total', 0),
                    json.dumps(item.get('org_counts', {})),
                    item.get('announcement_date', ''),
                    item.get('end_of_sale', ''),
                    item.get('end_of_support', ''),
                    item.get('highlight', '')
                ))
            
            conn.commit()
            print(f"✅ Migrated {len(summary_data.get('summary', []))} summary records")
        
        # Migrate device data (first 1000 devices to test)
        details_file = '/var/www/html/meraki-data/meraki_inventory_full.json'
        if os.path.exists(details_file):
            with open(details_file, 'r') as f:
                full_data = json.load(f)
            
            device_count = 0
            for org_name, devices in full_data.items():
                print(f"Migrating {len(devices)} devices for {org_name}")
                for device in devices:  # Process all devices
                    cursor.execute("""
                        INSERT INTO inventory_devices
                        (serial, model, organization, network_id, network_name, name, mac, lan_ip, firmware, product_type, tags, notes, details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (serial) DO UPDATE SET
                        model = EXCLUDED.model,
                        organization = EXCLUDED.organization,
                        network_id = EXCLUDED.network_id,
                        network_name = EXCLUDED.network_name,
                        name = EXCLUDED.name,
                        mac = EXCLUDED.mac,
                        lan_ip = EXCLUDED.lan_ip,
                        firmware = EXCLUDED.firmware,
                        product_type = EXCLUDED.product_type,
                        tags = EXCLUDED.tags,
                        notes = EXCLUDED.notes,
                        details = EXCLUDED.details
                    """, (
                        device.get('serial', ''),
                        device.get('model') or device.get('device_model', ''),
                        org_name,
                        device.get('networkId', ''),
                        device.get('networkName', ''),
                        device.get('name', ''),
                        device.get('mac', ''),
                        device.get('lanIp', ''),
                        device.get('firmware', ''),
                        device.get('productType', ''),
                        json.dumps(device.get('tags', [])),
                        device.get('notes', ''),
                        json.dumps({k: v for k, v in device.items() 
                                  if k not in ['serial', 'model', 'device_model', 'networkId', 
                                             'networkName', 'name', 'mac', 'lanIp', 'firmware', 
                                             'productType', 'tags', 'notes']})
                    ))
                    device_count += 1
            
            conn.commit()
            print(f"✅ Migrated {device_count} device records")
        
        print("🎉 Inventory migration completed!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_inventory()