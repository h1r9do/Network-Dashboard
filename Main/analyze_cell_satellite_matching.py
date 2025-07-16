#!/usr/bin/env python3
"""
Analyze why Cell/Satellite sites aren't matching ARIN to notes
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re

# Database connection
def get_db_connection():
    """Get database connection"""
    with open('/usr/local/bin/Main/config.py', 'r') as f:
        config_content = f.read()
    
    uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"](.+?)['\"]", config_content)
    if not uri_match:
        raise ValueError("Could not find database URI in config")
    
    db_uri = uri_match.group(1)
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', db_uri)
    if not match:
        raise ValueError("Invalid database URI format")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def main():
    """Analyze Cell/Satellite provider matching issues"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Analyzing Cell/Satellite Provider Matching ===\n")
    
    # Check what providers we have for Cell sites
    query = """
        SELECT 
            CASE 
                WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN 'WAN1'
                WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN 'WAN2'
            END as wan_type,
            CASE 
                WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN wan1_speed
                WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN wan2_speed
            END as speed_type,
            CASE 
                WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN wan1_provider
                WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN wan2_provider
            END as notes_provider,
            CASE 
                WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN wan1_arin_org
                WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN wan2_arin_org
            END as arin_provider,
            COUNT(*) as site_count
        FROM enriched_circuits
        WHERE 
            LOWER(wan1_speed) IN ('cell', 'satellite') OR 
            LOWER(wan2_speed) IN ('cell', 'satellite')
        GROUP BY 1, 2, 3, 4
        ORDER BY site_count DESC
        LIMIT 30
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("=== Top Cell/Satellite Provider Combinations ===\n")
    print(f"{'WAN':<5} {'Speed':<10} {'Notes Provider':<25} {'ARIN Provider':<25} {'Sites':<6}")
    print("-" * 80)
    
    for row in results:
        notes = (row['notes_provider'] or 'None')[:24]
        arin = (row['arin_provider'] or 'None')[:24]
        print(f"{row['wan_type']:<5} {row['speed_type']:<10} {notes:<25} {arin:<25} {row['site_count']:<6}")
    
    # Check if we need fuzzy matching for cellular
    print("\n\n=== Common Cell/Satellite Provider Patterns ===\n")
    
    patterns_query = """
        WITH cell_providers AS (
            SELECT DISTINCT
                CASE 
                    WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN wan1_provider
                    WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN wan2_provider
                END as notes_provider,
                CASE 
                    WHEN LOWER(wan1_speed) IN ('cell', 'satellite') THEN wan1_arin_org
                    WHEN LOWER(wan2_speed) IN ('cell', 'satellite') THEN wan2_arin_org
                END as arin_provider
            FROM enriched_circuits
            WHERE 
                LOWER(wan1_speed) IN ('cell', 'satellite') OR 
                LOWER(wan2_speed) IN ('cell', 'satellite')
        )
        SELECT 
            notes_provider,
            arin_provider,
            CASE 
                WHEN notes_provider IS NULL OR arin_provider IS NULL THEN 'Missing data'
                WHEN LOWER(notes_provider) = LOWER(arin_provider) THEN 'Exact match'
                WHEN LOWER(notes_provider) LIKE '%' || LOWER(arin_provider) || '%' 
                  OR LOWER(arin_provider) LIKE '%' || LOWER(notes_provider) || '%' THEN 'Partial match'
                ELSE 'No match'
            END as match_type
        FROM cell_providers
        WHERE notes_provider IS NOT NULL OR arin_provider IS NOT NULL
        ORDER BY match_type, notes_provider
        LIMIT 50
    """
    
    cursor.execute(patterns_query)
    patterns = cursor.fetchall()
    
    print(f"{'Notes Provider':<30} {'ARIN Provider':<30} {'Match Type':<15}")
    print("-" * 80)
    
    exact_matches = 0
    partial_matches = 0
    no_matches = 0
    missing_data = 0
    
    for pattern in patterns:
        notes = (pattern['notes_provider'] or 'None')[:29]
        arin = (pattern['arin_provider'] or 'None')[:29]
        match_type = pattern['match_type']
        
        if match_type == 'Exact match':
            exact_matches += 1
        elif match_type == 'Partial match':
            partial_matches += 1
        elif match_type == 'No match':
            no_matches += 1
        else:
            missing_data += 1
        
        print(f"{notes:<30} {arin:<30} {match_type:<15}")
    
    print(f"\n\nSummary:")
    print(f"  Exact matches: {exact_matches}")
    print(f"  Partial matches: {partial_matches}")
    print(f"  No matches: {no_matches}")
    print(f"  Missing data: {missing_data}")
    
    # Check specific examples where we should create circuits
    print("\n\n=== Sites That Should Get Non-DSR Circuits ===\n")
    
    should_create_query = """
        SELECT 
            network_name,
            wan1_provider,
            wan1_speed,
            wan1_arin_org,
            wan2_provider,
            wan2_speed,
            wan2_arin_org,
            (SELECT COUNT(*) FROM circuits WHERE site_name = ec.network_name AND status = 'Enabled') as circuits
        FROM enriched_circuits ec
        WHERE 
            -- WAN2 Cell with providers
            (LOWER(wan2_speed) = 'cell' 
             AND wan2_provider IS NOT NULL 
             AND wan2_arin_org IS NOT NULL)
        ORDER BY network_name
        LIMIT 20
    """
    
    cursor.execute(should_create_query)
    should_create = cursor.fetchall()
    
    print(f"{'Site':<10} {'WAN2 Provider':<20} {'WAN2 ARIN':<20} {'Circuits'}")
    print("-" * 60)
    
    for site in should_create:
        print(f"{site['network_name']:<10} {(site['wan2_provider'] or '')[:19]:<20} {(site['wan2_arin_org'] or '')[:19]:<20} {site['circuits']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()