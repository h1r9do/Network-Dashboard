#!/usr/bin/env python3
"""
Add missing columns to enriched_circuits table
"""
import psycopg2
import re

# Read config to get database connection
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()
else:
    print("Could not find database URI in config")
    exit(1)

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    print("Adding new columns to enriched_circuits table...")
    
    # Add the columns if they don't exist
    cursor.execute("""
        ALTER TABLE enriched_circuits 
        ADD COLUMN IF NOT EXISTS wan1_ip VARCHAR(50),
        ADD COLUMN IF NOT EXISTS wan2_ip VARCHAR(50),
        ADD COLUMN IF NOT EXISTS wan1_arin_org VARCHAR(255),
        ADD COLUMN IF NOT EXISTS wan2_arin_org VARCHAR(255);
    """)
    
    conn.commit()
    print("Columns added successfully (or already existed)")
    
    # Verify the columns exist
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'enriched_circuits'
        AND column_name IN ('wan1_ip', 'wan2_ip', 'wan1_arin_org', 'wan2_arin_org')
        ORDER BY column_name
    """)
    
    columns = cursor.fetchall()
    print("\nVerification - New columns in enriched_circuits:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}({col[2]})")
    
    # Check if we need to populate these columns from meraki_inventory
    cursor.execute("""
        SELECT COUNT(*) 
        FROM enriched_circuits 
        WHERE wan1_ip IS NULL AND wan2_ip IS NULL
    """)
    
    null_count = cursor.fetchone()[0]
    if null_count > 0:
        print(f"\nFound {null_count} records with NULL IP addresses")
        print("These will be populated during the next nightly run")
    else:
        print("\nAll records already have IP addresses populated")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()