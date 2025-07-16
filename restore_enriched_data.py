#!/usr/bin/env python3
"""
Restore enriched circuit data from June 24 backup, then apply only NEW enabled circuits
from the latest DSR tracking data.
"""
import json
import psycopg2
import re
from datetime import datetime
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

# Load June 24 backup data
print("Loading June 24 backup data...")
with open('/usr/local/bin/backups/migration_20250624_171253/www_html/meraki-data/mx_inventory_enriched_2025-06-24.json', 'r') as f:
    backup_data = json.load(f)

print(f"Loaded {len(backup_data)} sites from backup")

# Connect to database
conn = get_db_connection()
cursor = conn.cursor()

# First, let's backup current data just in case
print("\nBacking up current enriched_circuits table...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS enriched_circuits_backup_20250627 AS 
    SELECT * FROM enriched_circuits
""")
conn.commit()

# Clear and restore from backup
print("\nRestoring enriched data from June 24 backup...")
cursor.execute("TRUNCATE enriched_circuits")

# Prepare data for insertion
insert_data = []
for item in backup_data:
    network_name = item['network_name']
    wan1 = item.get('wan1', {})
    wan2 = item.get('wan2', {})
    
    # Extract circuit roles
    wan1_role = 'Primary' if wan1 else None
    wan2_role = 'Secondary' if wan2 else None
    
    # Get device tags, ensure it's a list
    device_tags = item.get('device_tags', [])
    if isinstance(device_tags, str):
        device_tags = [device_tags] if device_tags else []
    elif not device_tags:
        device_tags = []
    
    insert_data.append((
        network_name,
        device_tags,
        wan1.get('provider', ''),
        wan1.get('speed', ''),
        wan1.get('monthly_cost', ''),
        wan1_role,
        wan1.get('confirmed', False),
        wan2.get('provider', ''),
        wan2.get('speed', ''),
        wan2.get('monthly_cost', ''),
        wan2_role,
        wan2.get('confirmed', False),
        item.get('pushed_to_meraki', False),
        item.get('pushed_date'),
        datetime.utcnow()
    ))

# Insert all data
cursor.executemany("""
    INSERT INTO enriched_circuits (
        network_name, device_tags, wan1_provider, wan1_speed, wan1_monthly_cost,
        wan1_circuit_role, wan1_confirmed,
        wan2_provider, wan2_speed, wan2_monthly_cost,
        wan2_circuit_role, wan2_confirmed,
        pushed_to_meraki, pushed_date, last_updated
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", insert_data)

conn.commit()
print(f"Restored {len(insert_data)} records")

# Now check for NEW enabled circuits from DSR tracking
print("\nChecking for new enabled circuits from DSR tracking...")

# Get enabled status list
enabled_statuses = ['Enabled', 'Service Activated', 'Enabled Using Existing Broadband', 
                   'Enabled/Disconnected', 'Enabled/Disconnect Pending']

# Find NEW enabled circuits (that weren't in June 24 data)
cursor.execute("""
    WITH june24_enabled AS (
        -- Sites that had enabled circuits in backup
        SELECT DISTINCT network_name
        FROM enriched_circuits
        WHERE wan1_provider != '' OR wan2_provider != ''
    ),
    current_enabled AS (
        -- Sites with enabled circuits in current DSR data
        SELECT DISTINCT site_name, circuit_purpose, provider_name, 
               details_ordered_service_speed, billing_monthly_cost,
               ip_address_start
        FROM circuits
        WHERE status = ANY(%s)
    )
    SELECT ce.site_name, ce.circuit_purpose, ce.provider_name,
           ce.details_ordered_service_speed, ce.billing_monthly_cost,
           ce.ip_address_start
    FROM current_enabled ce
    LEFT JOIN june24_enabled j24 ON ce.site_name = j24.network_name
    WHERE j24.network_name IS NULL  -- Only new sites
    ORDER BY ce.site_name, ce.circuit_purpose
""", (enabled_statuses,))

new_circuits = cursor.fetchall()
print(f"\nFound {len(new_circuits)} new enabled circuits")

# Group by site
new_sites = {}
for row in new_circuits:
    site_name = row[0]
    if site_name not in new_sites:
        new_sites[site_name] = []
    new_sites[site_name].append({
        'purpose': row[1],
        'provider': row[2],
        'speed': row[3],
        'cost': row[4],
        'ip': row[5]
    })

print(f"\nNew sites with enabled circuits: {len(new_sites)}")
for site, circuits in list(new_sites.items())[:10]:  # Show first 10
    print(f"\n{site}:")
    for circuit in circuits:
        print(f"  - {circuit['purpose']}: {circuit['provider']} ({circuit['speed']}, ${circuit['cost']})")

# For new sites, we need to check if they exist in enriched_circuits
# If they do, update them with DSR data. If not, we'll need to create them.
print("\nUpdating enriched_circuits with new DSR enabled circuits...")

updates = 0
for site_name, circuits in new_sites.items():
    # Check if site exists in enriched_circuits
    cursor.execute("SELECT 1 FROM enriched_circuits WHERE network_name = %s", (site_name,))
    exists = cursor.fetchone()
    
    if exists:
        # Update existing record with new DSR data
        wan1_data = None
        wan2_data = None
        
        for circuit in circuits:
            purpose = (circuit['purpose'] or '').lower()
            if 'primary' in purpose or 'wan1' in purpose or (not wan1_data and 'backup' not in purpose):
                wan1_data = circuit
            elif 'backup' in purpose or 'wan2' in purpose or not wan2_data:
                wan2_data = circuit
        
        # Update the record
        if wan1_data:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan1_provider = %s, wan1_speed = %s, wan1_monthly_cost = %s,
                    wan1_confirmed = false, last_updated = %s
                WHERE network_name = %s AND wan1_provider = ''
            """, (wan1_data['provider'], wan1_data['speed'], wan1_data['cost'],
                  datetime.utcnow(), site_name))
            
        if wan2_data:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan2_provider = %s, wan2_speed = %s, wan2_monthly_cost = %s,
                    wan2_confirmed = false, last_updated = %s
                WHERE network_name = %s AND wan2_provider = ''
            """, (wan2_data['provider'], wan2_data['speed'], wan2_data['cost'],
                  datetime.utcnow(), site_name))
        
        updates += 1
    else:
        # This is a completely new site, add it
        wan1_data = None
        wan2_data = None
        
        for circuit in circuits:
            purpose = (circuit['purpose'] or '').lower()
            if 'primary' in purpose or 'wan1' in purpose or (not wan1_data and 'backup' not in purpose):
                wan1_data = circuit
            elif 'backup' in purpose or 'wan2' in purpose or not wan2_data:
                wan2_data = circuit
        
        cursor.execute("""
            INSERT INTO enriched_circuits (
                network_name, device_tags, wan1_provider, wan1_speed, wan1_monthly_cost,
                wan1_circuit_role, wan2_provider, wan2_speed, wan2_monthly_cost,
                wan2_circuit_role, pushed_to_meraki, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s)
        """, (
            site_name,
            [],  # device_tags as empty array
            wan1_data['provider'] if wan1_data else '',
            wan1_data['speed'] if wan1_data else '',
            wan1_data['cost'] if wan1_data else '',
            'Primary' if wan1_data else None,
            wan2_data['provider'] if wan2_data else '',
            wan2_data['speed'] if wan2_data else '',
            wan2_data['cost'] if wan2_data else '',
            'Secondary' if wan2_data else None,
            datetime.utcnow()
        ))
        updates += 1

conn.commit()
print(f"\nUpdated/added {updates} sites with new enabled circuits")

# Final verification
cursor.execute("SELECT COUNT(*) FROM enriched_circuits")
total = cursor.fetchone()[0]
print(f"\nTotal enriched circuits after restoration: {total}")

cursor.execute("""
    SELECT COUNT(*) FROM enriched_circuits 
    WHERE wan1_provider != '' OR wan2_provider != ''
""")
with_data = cursor.fetchone()[0]
print(f"Sites with circuit data: {with_data}")

cursor.execute("""
    SELECT COUNT(*) FROM enriched_circuits 
    WHERE wan1_provider = '' AND wan2_provider = ''
""")
empty = cursor.fetchone()[0]
print(f"Sites with no circuit data: {empty}")

# Check some specific sites
print("\n=== Verification of previously problematic sites ===")
for site in ['COD 23', 'TXS 24', 'COX 01', 'AZH 01']:
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    result = cursor.fetchone()
    if result:
        print(f"{site}: WAN1='{result[0]}' {result[1]}, WAN2='{result[2]}' {result[3]}")

cursor.close()
conn.close()

print("\n✓ Restoration complete!")
print("  - Restored all data from June 24 backup")
print("  - Applied only NEW enabled circuits from DSR tracking")
print("  - Preserved all existing Meraki data (cellular, satellite, etc.)")