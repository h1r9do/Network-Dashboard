#!/usr/bin/env python3
"""
Migrate Meraki inventory data from JSON files to database
"""

import json
import os
import sys
sys.path.append('/usr/local/bin/Main')

from models import db, InventoryDevice, InventorySummary
from dsrcircuits_integrated import create_app

def migrate_inventory_data():
    """Migrate inventory data from JSON files to database"""
    
    app = create_app()
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("✅ Created inventory database tables")
            
            # Clear existing data
            InventoryDevice.query.delete()
            InventorySummary.query.delete()
            db.session.commit()
            print("✅ Cleared existing inventory data")
            
            # Migrate summary data
            summary_file = '/var/www/html/meraki-data/meraki_inventory_summary.json'
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
                
                for item in summary_data.get('summary', []):
                    summary_record = InventorySummary(
                        model=item['model'],
                        total_count=item.get('total', 0),
                        org_counts=json.dumps(item.get('org_counts', {})),
                        announcement_date=item.get('announcement_date', ''),
                        end_of_sale=item.get('end_of_sale', ''),
                        end_of_support=item.get('end_of_support', ''),
                        highlight=item.get('highlight', '')
                    )
                    db.session.add(summary_record)
                
                db.session.commit()
                print(f"✅ Migrated {len(summary_data.get('summary', []))} summary records")
            
            # Migrate detailed device data
            details_file = '/var/www/html/meraki-data/meraki_inventory_full.json'
            if os.path.exists(details_file):
                with open(details_file, 'r') as f:
                    full_data = json.load(f)
                
                device_count = 0
                for org_name, devices in full_data.items():
                    for device in devices:
                        device_record = InventoryDevice(
                            serial=device.get('serial', ''),
                            model=device.get('model') or device.get('device_model', ''),
                            organization=org_name,
                            network_id=device.get('networkId', ''),
                            network_name=device.get('networkName', ''),
                            name=device.get('name', ''),
                            mac=device.get('mac', ''),
                            lan_ip=device.get('lanIp', ''),
                            firmware=device.get('firmware', ''),
                            product_type=device.get('productType', ''),
                            tags=json.dumps(device.get('tags', [])),
                            notes=device.get('notes', ''),
                            details=json.dumps({k: v for k, v in device.items() 
                                              if k not in ['serial', 'model', 'device_model', 'networkId', 
                                                         'networkName', 'name', 'mac', 'lanIp', 'firmware', 
                                                         'productType', 'tags', 'notes']})
                        )
                        db.session.add(device_record)
                        device_count += 1
                
                db.session.commit()
                print(f"✅ Migrated {device_count} device records")
            
            print("🎉 Inventory migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during inventory migration: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_inventory_data()