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

# Count circuits with N/A providers
cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan1_provider = 'N/A' OR wan2_provider = 'N/A'")
na_count = cursor.fetchone()[0]

# Count circuits with real providers
cursor.execute("SELECT COUNT(*) FROM enriched_circuits WHERE wan1_provider != 'N/A' AND wan1_provider IS NOT NULL")
real_count = cursor.fetchone()[0]

# Get sample data
cursor.execute("""
    SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed 
    FROM enriched_circuits 
    WHERE wan1_provider != 'N/A' 
    LIMIT 5
""")
samples = cursor.fetchall()

print(f"Circuits with N/A providers: {na_count}")
print(f"Circuits with real providers: {real_count}")
print("\nSample circuits with real data:")
for sample in samples:
    print(f"  {sample[0]}: WAN1={sample[1]} {sample[2]}, WAN2={sample[3]} {sample[4]}")

cursor.close()
conn.close()