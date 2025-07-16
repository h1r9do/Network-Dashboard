#!/usr/bin/env python3
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

conn = get_db_connection()
cursor = conn.cursor()

# Check for N/A in wan1_provider
cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan1_provider = 'N/A'")
wan1_na = cursor.fetchone()[0]

# Check for N/A in wan2_provider  
cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan2_provider = 'N/A'")
wan2_na = cursor.fetchone()[0]

# Check for empty/null providers
cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan1_provider IS NULL OR wan1_provider = ''")
wan1_empty = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan2_provider IS NULL OR wan2_provider = ''")
wan2_empty = cursor.fetchone()[0]

# Get samples of N/A providers
cursor.execute("""
    SELECT network_name, wan1_provider, wan2_provider 
    FROM enriched_circuits 
    WHERE wan1_provider = 'N/A' OR wan2_provider = 'N/A'
    LIMIT 10
""")
na_samples = cursor.fetchall()

# Get samples of empty providers
cursor.execute("""
    SELECT network_name, wan1_provider, wan2_provider 
    FROM enriched_circuits 
    WHERE wan1_provider = '' OR wan2_provider = '' OR wan1_provider IS NULL OR wan2_provider IS NULL
    LIMIT 10
""")
empty_samples = cursor.fetchall()

print(f"WAN1 with 'N/A': {wan1_na}")
print(f"WAN2 with 'N/A': {wan2_na}")
print(f"WAN1 empty/null: {wan1_empty}")
print(f"WAN2 empty/null: {wan2_empty}")

print("\nSamples with N/A:")
for sample in na_samples:
    print(f"  {sample[0]}: WAN1='{sample[1]}', WAN2='{sample[2]}'")

print("\nSamples with empty/null:")
for sample in empty_samples:
    print(f"  {sample[0]}: WAN1='{sample[1]}', WAN2='{sample[2]}'")

# Check what the dsrcircuits page is actually querying
cursor.execute("""
    SELECT COUNT(*) 
    FROM enriched_circuits 
    WHERE (wan1_provider = '' OR wan1_provider IS NULL) 
       OR (wan2_provider = '' OR wan2_provider IS NULL)
""")
empty_count = cursor.fetchone()[0]

print(f"\nTotal circuits with empty providers: {empty_count}")

cursor.close()
conn.close()