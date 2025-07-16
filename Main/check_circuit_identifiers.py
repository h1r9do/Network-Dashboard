#!/usr/bin/env python3
"""
Check how circuit identifiers work for DSR vs non-DSR circuits
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re
from config import Config

def get_db_connection():
    """Get database connection"""
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

def check_identifiers():
    """Check circuit identifiers"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Circuit Identifier Analysis ===\n")
    
    # First check what columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'circuits' 
        AND column_name IN ('id', 'site_id', 'record_number', 'project_id', 'unique_id', 'identifier')
    """)
    
    cols = cursor.fetchall()
    print("Available identifier columns:")
    for col in cols:
        print(f"  - {col['column_name']}")
    
    # Check CAL 24 circuits specifically
    cursor.execute("""
        SELECT id, site_name, site_id, circuit_purpose, provider_name, 
               record_number, created_at, status
        FROM circuits
        WHERE site_name = 'CAL 24'
        ORDER BY created_at
    """)
    
    circuits = cursor.fetchall()
    
    print("CAL 24 Circuits:")
    for circuit in circuits:
        print(f"\nID: {circuit['id']}")
        print(f"  Site Name: {circuit['site_name']}")
        print(f"  Site ID: {circuit['site_id']}")
        print(f"  Purpose: {circuit['circuit_purpose']}")
        print(f"  Provider: {circuit['provider_name']}")
        print(f"  Record Number: {circuit['record_number']}")
        print(f"  Status: {circuit['status']}")
        print(f"  Created: {circuit['created_at']}")
        
        # Determine if DSR or non-DSR
        if circuit['record_number']:
            print(f"  Type: DSR Circuit (record_number: {circuit['record_number']})")
        else:
            print(f"  Type: Non-DSR Circuit (no record_number)")
    
    # Check pattern of non-DSR circuits
    print("\n\n=== Non-DSR Circuit Patterns ===")
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN project_id IS NOT NULL THEN 1 END) as with_project_id,
               COUNT(CASE WHEN site_id IS NOT NULL THEN 1 END) as with_site_id,
               COUNT(CASE WHEN record_number IS NULL AND project_id IS NULL THEN 1 END) as no_identifiers
        FROM circuits
        WHERE record_number IS NULL
        AND status = 'Enabled'
    """)
    
    stats = cursor.fetchone()
    print(f"Total Non-DSR circuits: {stats['total']}")
    print(f"  With project_id: {stats['with_project_id']}")
    print(f"  With site_id: {stats['with_site_id']}")
    print(f"  No identifiers: {stats['no_identifiers']}")
    
    # Check how new non-DSR circuits might be identified
    print("\n\n=== Sample Non-DSR with Identifiers ===")
    cursor.execute("""
        SELECT site_name, circuit_purpose, record_number, project_id, site_id
        FROM circuits
        WHERE record_number IS NULL
        AND (project_id IS NOT NULL OR site_id IS NOT NULL)
        AND status = 'Enabled'
        LIMIT 10
    """)
    
    examples = cursor.fetchall()
    for ex in examples:
        print(f"{ex['site_name']}: record#{ex['record_number']} project#{ex['project_id']} site_id:{ex['site_id']}")
    
    conn.close()

if __name__ == "__main__":
    check_identifiers()