#!/usr/bin/env python3
"""Check existing carrier detection data"""

import sys
import psycopg2
import json

sys.path.append('/usr/local/bin/test')
from config import Config

conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
cursor = conn.cursor()

# Check if we have any data
cursor.execute("""
    SELECT 
        network_name, 
        wan_interface, 
        private_ip, 
        public_ip,
        detected_carrier,
        confidence_score,
        traceroute_hops
    FROM cellular_carrier_detection
    WHERE network_name = 'ALB 03'
""")

results = cursor.fetchall()

if results:
    print("Existing carrier detection data for ALB 03:")
    for row in results:
        print(f"\nNetwork: {row[0]}")
        print(f"Interface: {row[1]}")
        print(f"Private IP: {row[2]}")
        print(f"Public IP: {row[3]}")
        print(f"Detected Carrier: {row[4]}")
        print(f"Confidence: {row[5]}%")
        if row[6]:
            hops = json.loads(row[6])
            if hops:
                print("Traceroute hops:")
                for hop in hops:
                    print(f"  Hop {hop.get('hop')}: {hop.get('ip')} -> {hop.get('hostname', 'N/A')}")
else:
    print("No existing carrier detection data for ALB 03")

# Check how many total records we have
cursor.execute("SELECT COUNT(*) FROM cellular_carrier_detection")
count = cursor.fetchone()[0]
print(f"\nTotal carrier detection records: {count}")

cursor.close()
conn.close()