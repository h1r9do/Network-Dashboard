#!/usr/bin/env python3
import sys
import psycopg2
sys.path.append('/usr/local/bin/test')
from config import Config

conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM meraki_inventory WHERE device_model LIKE 'MS%'")
count = cursor.fetchone()[0]
print(f"Number of Meraki switches: {count}")

if count > 0:
    cursor.execute("""
        SELECT device_serial, network_name, device_model 
        FROM meraki_inventory 
        WHERE device_model LIKE 'MS%' 
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"\nExample switch: {result[1]} - {result[2]} ({result[0]})")

cursor.close()
conn.close()