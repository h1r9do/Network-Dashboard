#!/usr/bin/env python3
"""Check columns in circuits table"""

import psycopg2
from config import Config
import re

def get_db_connection():
    """Get database connection"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )

conn = get_db_connection()
cursor = conn.cursor()

# Get column information
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'circuits' 
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
print("Columns in circuits table:")
for col_name, col_type in columns:
    print(f"  {col_name}: {col_type}")

cursor.close()
conn.close()