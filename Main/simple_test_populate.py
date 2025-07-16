#!/usr/bin/env python3
"""
Simple test to populate provider matching test data
"""

import os
import sys
import psycopg2
import psycopg2.extras

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def get_db_connection():
    """Get database connection using config"""
    import re
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

def simple_test():
    """Simple test without complex logic"""
    
    print("Simple provider matching test...")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Just get a few circuits and add them to test table
    cursor.execute("""
        SELECT 
            site_id, site_name, circuit_purpose, provider_name
        FROM circuits
        WHERE status = 'Enabled'
        LIMIT 10
    """)
    
    circuits = cursor.fetchall()
    print(f"Found {len(circuits)} circuits")
    
    for circuit in circuits:
        # Simple mapping logic
        dsr_provider = circuit['provider_name']
        
        # Simple provider mappings
        if 'Spectrum' in dsr_provider:
            arin_provider = 'Charter Communications'
            match_status = 'matched'
            confidence = 95
            reason = 'Spectrum → Charter'
        elif 'AT&T' in dsr_provider:
            arin_provider = 'AT&T'
            match_status = 'matched'
            confidence = 100
            reason = 'Direct match'
        elif 'Brightspeed' in dsr_provider:
            arin_provider = 'CenturyLink'
            match_status = 'matched'
            confidence = 90
            reason = 'Brightspeed → CenturyLink'
        else:
            arin_provider = 'Unknown'
            match_status = 'no_match'
            confidence = 0
            reason = 'No mapping'
        
        # Insert into test table
        try:
            cursor.execute("""
                INSERT INTO provider_match_test (
                    site_id, site_name, circuit_purpose, dsr_provider, arin_provider,
                    provider_match_status, provider_match_confidence, 
                    provider_canonical, match_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (site_id, circuit_purpose) DO UPDATE SET
                    dsr_provider = EXCLUDED.dsr_provider,
                    arin_provider = EXCLUDED.arin_provider,
                    provider_match_status = EXCLUDED.provider_match_status,
                    provider_match_confidence = EXCLUDED.provider_match_confidence,
                    provider_canonical = EXCLUDED.provider_canonical,
                    match_reason = EXCLUDED.match_reason
            """, (
                circuit['site_id'], circuit['site_name'], circuit['circuit_purpose'],
                dsr_provider, arin_provider, match_status, confidence,
                arin_provider, reason
            ))
            print(f"Added {circuit['site_name']}: {dsr_provider} → {arin_provider}")
        except Exception as e:
            print(f"Error adding {circuit['site_name']}: {e}")
    
    conn.commit()
    
    # Show results
    cursor.execute("SELECT * FROM provider_test_statistics")
    stats = cursor.fetchone()
    
    print(f"\n=== Results ===")
    print(f"Total: {stats['total_circuits']}")
    print(f"Matched: {stats['matched_circuits']}")
    print(f"Match rate: {stats['match_rate']}%")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    simple_test()