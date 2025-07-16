#!/usr/bin/env python3
"""Check EOL data in the database"""

import psycopg2
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
import re

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

print("=== Enhanced EOL Table ===")
cursor.execute("""
    SELECT model, announcement_date, end_of_sale, end_of_support, source, pdf_name
    FROM meraki_eol_enhanced
    WHERE model LIKE 'MS220%'
    ORDER BY model
""")

for row in cursor.fetchall():
    print(f"{row[0]}: Ann={row[1]}, EOS={row[2]}, EOL={row[3]} (Source: {row[4]}, PDF: {row[5]})")

print("\n=== Inventory Summary Table ===")
cursor.execute("""
    SELECT model, announcement_date, end_of_sale, end_of_support, highlight
    FROM inventory_summary
    WHERE model LIKE 'MS220%'
    ORDER BY model
""")

for row in cursor.fetchall():
    print(f"{row[0]}: Ann={row[1]}, EOS={row[2]}, EOL={row[3]} (Highlight: {row[4]})")

print("\n=== Check if we should use the PDF data ===")
# The PDF shows:
# MS220-8/8P: EOS=Sept 21, 2018, EOL=Sept 21, 2025
# MS220-24/48 series: EOS=July 29, 2017, EOL=July 29, 2024

cursor.close()
conn.close()