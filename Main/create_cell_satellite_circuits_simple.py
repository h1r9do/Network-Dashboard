#!/usr/bin/env python3
"""
Create Non-DSR circuits for Cell and Satellite sites - Simple version
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
from datetime import datetime
import re

# Database connection
def get_db_connection():
    """Get database connection"""
    # Parse the connection string from config
    with open('/usr/local/bin/Main/config.py', 'r') as f:
        config_content = f.read()
    
    # Extract database URI
    uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"](.+?)['\"]", config_content)
    if not uri_match:
        raise ValueError("Could not find database URI in config")
    
    db_uri = uri_match.group(1)
    
    # Parse PostgreSQL URI
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
    """Find and create Non-DSR circuits for Cell/Satellite sites"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Analyzing Cell/Satellite Sites for Non-DSR Circuit Creation ===\n")
    
    # First, let's see what we have
    analysis_query = """
        WITH cell_satellite_sites AS (
            SELECT DISTINCT
                ec.network_name,
                ec.wan1_provider,
                ec.wan1_speed,
                ec.wan1_arin_org,
                ec.wan2_provider,
                ec.wan2_speed,
                ec.wan2_arin_org
            FROM enriched_circuits ec
            WHERE 
                LOWER(ec.wan1_speed) IN ('cell', 'satellite') OR 
                LOWER(ec.wan2_speed) IN ('cell', 'satellite')
        )
        SELECT 
            COUNT(DISTINCT network_name) as total_sites,
            COUNT(CASE WHEN LOWER(wan1_speed) = 'cell' THEN 1 END) as wan1_cell_count,
            COUNT(CASE WHEN LOWER(wan1_speed) = 'satellite' THEN 1 END) as wan1_satellite_count,
            COUNT(CASE WHEN LOWER(wan2_speed) = 'cell' THEN 1 END) as wan2_cell_count,
            COUNT(CASE WHEN LOWER(wan2_speed) = 'satellite' THEN 1 END) as wan2_satellite_count
        FROM cell_satellite_sites
    """
    
    cursor.execute(analysis_query)
    stats = cursor.fetchone()
    
    print(f"Total sites with Cell/Satellite: {stats['total_sites']}")
    print(f"  WAN1 Cell: {stats['wan1_cell_count']}")
    print(f"  WAN1 Satellite: {stats['wan1_satellite_count']}")
    print(f"  WAN2 Cell: {stats['wan2_cell_count']}")
    print(f"  WAN2 Satellite: {stats['wan2_satellite_count']}")
    
    # Now find candidates where ARIN matches notes
    candidates_query = """
        SELECT DISTINCT
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan1_arin_org,
            ec.wan2_provider,
            ec.wan2_speed,
            ec.wan2_arin_org,
            -- Check existing circuits
            (SELECT COUNT(*) FROM circuits c 
             WHERE c.site_name = ec.network_name 
             AND c.status = 'Enabled') as existing_circuits
        FROM enriched_circuits ec
        WHERE 
            (
                -- WAN1 Cell/Satellite with matching providers
                (LOWER(ec.wan1_speed) IN ('cell', 'satellite') 
                 AND ec.wan1_provider IS NOT NULL 
                 AND ec.wan1_arin_org IS NOT NULL
                 AND LOWER(ec.wan1_provider) = LOWER(ec.wan1_arin_org))
                OR
                -- WAN2 Cell/Satellite with matching providers  
                (LOWER(ec.wan2_speed) IN ('cell', 'satellite')
                 AND ec.wan2_provider IS NOT NULL
                 AND ec.wan2_arin_org IS NOT NULL
                 AND LOWER(ec.wan2_provider) = LOWER(ec.wan2_arin_org))
            )
        ORDER BY ec.network_name
        LIMIT 50
    """
    
    cursor.execute(candidates_query)
    candidates = cursor.fetchall()
    
    print(f"\n\n=== Sites with matching ARIN/Notes providers (first 50) ===\n")
    print(f"{'Site':<10} {'Existing':<8} {'WAN1 Provider':<20} {'WAN1 ARIN':<20} {'WAN1 Speed':<10} {'WAN2 Provider':<20} {'WAN2 ARIN':<20} {'WAN2 Speed':<10}")
    print("-" * 140)
    
    for site in candidates:
        print(f"{site['network_name']:<10} {site['existing_circuits']:<8} "
              f"{(site['wan1_provider'] or '')[:19]:<20} {(site['wan1_arin_org'] or '')[:19]:<20} {(site['wan1_speed'] or ''):<10} "
              f"{(site['wan2_provider'] or '')[:19]:<20} {(site['wan2_arin_org'] or '')[:19]:<20} {(site['wan2_speed'] or ''):<10}")
    
    # Check specific examples
    print("\n\n=== Checking specific sites for circuit needs ===\n")
    
    check_sites = ['ALB 03', 'MNG 11', 'FLO 21', 'GAA 41', 'MTB 06', 'WAP 10']
    
    for site_name in check_sites:
        cursor.execute("""
            SELECT 
                ec.*,
                (SELECT COUNT(*) FROM circuits WHERE site_name = %s AND status = 'Enabled') as circuit_count,
                (SELECT array_agg(provider_name || ' (' || circuit_purpose || ')') 
                 FROM circuits WHERE site_name = %s AND status = 'Enabled') as existing_providers
            FROM enriched_circuits ec
            WHERE ec.network_name = %s
        """, (site_name, site_name, site_name))
        
        site_data = cursor.fetchone()
        
        if site_data:
            print(f"\n{site_name}:")
            print(f"  WAN1: {site_data['wan1_provider']} / ARIN: {site_data['wan1_arin_org']} / Speed: {site_data['wan1_speed']}")
            print(f"  WAN2: {site_data['wan2_provider']} / ARIN: {site_data['wan2_arin_org']} / Speed: {site_data['wan2_speed']}")
            print(f"  Existing circuits ({site_data['circuit_count']}): {site_data['existing_providers']}")
            
            # Check if needs Non-DSR circuit
            needs_circuit = False
            
            if site_data['wan1_speed'] and site_data['wan1_speed'].lower() in ['cell', 'satellite']:
                if site_data['wan1_provider'] and site_data['wan1_arin_org']:
                    if site_data['wan1_provider'].lower() == site_data['wan1_arin_org'].lower():
                        needs_circuit = True
                        print(f"  → Needs WAN1 Non-DSR circuit for {site_data['wan1_provider']}")
            
            if site_data['wan2_speed'] and site_data['wan2_speed'].lower() in ['cell', 'satellite']:
                if site_data['wan2_provider'] and site_data['wan2_arin_org']:
                    if site_data['wan2_provider'].lower() == site_data['wan2_arin_org'].lower():
                        needs_circuit = True
                        print(f"  → Needs WAN2 Non-DSR circuit for {site_data['wan2_provider']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()