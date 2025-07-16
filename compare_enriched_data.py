#!/usr/bin/env python3
import json
import psycopg2
import re
from config import Config

# Get database connection
def get_db_connection():
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

# Load old enriched data
print("Loading pre-migration enriched data from June 24...")
with open('/usr/local/bin/backups/migration_20250624_171253/www_html/meraki-data/mx_inventory_enriched_2025-06-24.json', 'r') as f:
    old_data = json.load(f)

# Create lookup dict
old_lookup = {item['network_name']: item for item in old_data}
print(f"Loaded {len(old_data)} sites from backup")

# Get current data from database
conn = get_db_connection()
cursor = conn.cursor()

# Get current enriched data
cursor.execute("""
    SELECT network_name, wan1_provider, wan1_speed, wan1_monthly_cost,
           wan2_provider, wan2_speed, wan2_monthly_cost
    FROM enriched_circuits
    ORDER BY network_name
""")

current_data = cursor.fetchall()
print(f"Found {len(current_data)} sites in current database")

# Compare data
lost_data = []
changed_data = []
still_empty = []

for row in current_data:
    network_name = row[0]
    current_wan1_provider = row[1] or ''
    current_wan2_provider = row[4] or ''
    
    if network_name in old_lookup:
        old_item = old_lookup[network_name]
        old_wan1_provider = old_item['wan1'].get('provider', '')
        old_wan2_provider = old_item['wan2'].get('provider', '')
        
        # Check if we lost data
        if old_wan1_provider and not current_wan1_provider:
            lost_data.append({
                'site': network_name,
                'wan': 'WAN1',
                'old_provider': old_wan1_provider,
                'old_speed': old_item['wan1'].get('speed', ''),
                'old_cost': old_item['wan1'].get('monthly_cost', '')
            })
        
        if old_wan2_provider and not current_wan2_provider:
            lost_data.append({
                'site': network_name,
                'wan': 'WAN2',
                'old_provider': old_wan2_provider,
                'old_speed': old_item['wan2'].get('speed', ''),
                'old_cost': old_item['wan2'].get('monthly_cost', '')
            })
        
        # Check if data changed
        if (old_wan1_provider != current_wan1_provider and current_wan1_provider) or \
           (old_wan2_provider != current_wan2_provider and current_wan2_provider):
            changed_data.append({
                'site': network_name,
                'old_wan1': old_wan1_provider,
                'new_wan1': current_wan1_provider,
                'old_wan2': old_wan2_provider,
                'new_wan2': current_wan2_provider
            })
    
    # Check if still empty
    if not current_wan1_provider or not current_wan2_provider:
        still_empty.append({
            'site': network_name,
            'wan1': current_wan1_provider,
            'wan2': current_wan2_provider
        })

print(f"\n=== ANALYSIS RESULTS ===")
print(f"Total sites with lost data: {len(lost_data)}")
print(f"Total sites with changed data: {len(changed_data)}")
print(f"Total sites still with empty providers: {len(still_empty)}")

print("\n=== LOST DATA (had provider before, empty now) ===")
for item in lost_data[:20]:  # Show first 20
    print(f"{item['site']} {item['wan']}: '{item['old_provider']}' {item['old_speed']} {item['old_cost']} -> EMPTY")

print("\n=== SAMPLE CHANGED DATA ===")
for item in changed_data[:10]:
    print(f"{item['site']}: WAN1: '{item['old_wan1']}' -> '{item['new_wan1']}', WAN2: '{item['old_wan2']}' -> '{item['new_wan2']}'")

# Check specific problematic sites
print("\n=== SPECIFIC SITES CHECK ===")
for site in ['COD 23', 'TXS 24', 'COX 01', 'AZH 01']:
    if site in old_lookup:
        old_item = old_lookup[site]
        cursor.execute("""
            SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
            FROM enriched_circuits
            WHERE network_name = %s
        """, (site,))
        current = cursor.fetchone()
        
        print(f"\n{site}:")
        print(f"  OLD - WAN1: '{old_item['wan1'].get('provider', '')}' {old_item['wan1'].get('speed', '')}")
        print(f"        WAN2: '{old_item['wan2'].get('provider', '')}' {old_item['wan2'].get('speed', '')}")
        if current:
            print(f"  NEW - WAN1: '{current[0]}' {current[1]}")
            print(f"        WAN2: '{current[2]}' {current[3]}")

cursor.close()
conn.close()