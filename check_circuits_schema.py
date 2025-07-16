#!/usr/bin/env python3
"""
Check the actual schema of the circuits table
"""
import psycopg2

db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Get column information
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'circuits'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print("Circuits table columns:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    
    # Check sample data
    print("\nSample data:")
    cur.execute("""
        SELECT site_id, site_name, provider, circuit_type, circuit_status, 
               bandwidth_mbps, public_ip
        FROM circuits
        LIMIT 5;
    """)
    
    for row in cur.fetchall():
        print(f"  {row}")
    
    # Count circuits by type
    print("\nCircuit type distribution:")
    cur.execute("""
        SELECT circuit_type, COUNT(*) 
        FROM circuits 
        WHERE circuit_status = 'Active'
        GROUP BY circuit_type;
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")