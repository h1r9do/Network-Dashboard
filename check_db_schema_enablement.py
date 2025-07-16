#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re

match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Checking enablement table schemas:")
print("=" * 80)

# Check table columns
tables = ['daily_enablements', 'ready_queue_daily', 'enablement_summary']
for table in tables:
    cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    if columns:
        print(f"\n{table}:")
        for col in columns:
            print(f"  - {col[0]:25} {col[1]}")
    else:
        print(f"\n{table}: TABLE NOT FOUND")

# Now check the actual data
print("\n\nData in daily_enablements:")
print("-" * 60)
cursor.execute("SELECT * FROM daily_enablements ORDER BY track_date DESC LIMIT 15")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 80)
for row in cursor.fetchall():
    print(" | ".join(str(val) for val in row))

cursor.close()
conn.close()