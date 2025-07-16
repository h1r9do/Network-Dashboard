#!/usr/bin/env python3
"""
Test Nexus 5K FEX collection
"""

import sys
sys.path.append('/usr/local/bin/test')
from direct_inventory_collection import collect_device_inventory, save_to_database

# Test Nexus 5K devices
devices = [
    {'hostname': 'AL-5000-01', 'ip': '10.101.145.125'},
    {'hostname': 'AL-5000-02', 'ip': '10.101.145.126'},
    {'hostname': 'HQ-5000-01', 'ip': '10.0.145.94'},
    {'hostname': 'HQ-5000-02', 'ip': '10.0.145.95'}
]

all_inventory = []

for device in devices:
    print(f"\nCollecting from {device['hostname']}...")
    inventory = collect_device_inventory(device['hostname'], device['ip'])
    
    if inventory['status'] == 'success':
        print(f"✅ Success!")
        print(f"   Chassis: {len(inventory['chassis'])}")
        print(f"   Modules: {len(inventory['modules'])}")
        print(f"   SFPs: {len(inventory['sfps'])}")
        print(f"   FEX: {len(inventory['fex'])}")
        
        if inventory['fex']:
            print("\nFEX Modules found:")
            for fex in inventory['fex']:
                print(f"   - FEX {fex['fex_id']}: {fex['description']} ({fex['model']}) - {fex['state']}")
                if fex.get('serial'):
                    print(f"     Serial: {fex['serial']}")
    else:
        print(f"❌ Failed: {inventory.get('error')}")
    
    all_inventory.append(inventory)

# Save to database
try:
    collection_id = save_to_database(all_inventory)
    print(f"\n✅ Saved to database - Collection ID: {collection_id}")
except Exception as e:
    print(f"\n❌ Database save failed: {e}")