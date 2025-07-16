#!/usr/bin/env python3
"""
Create Non-DSR circuits for Cell and Satellite sites that need them
Logic: Sites with Cell/Satellite speed and no existing circuit for that provider
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
from datetime import datetime
import re

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

def normalize_provider(provider):
    """Normalize provider names for comparison"""
    if not provider:
        return ""
    
    # Common cellular provider normalizations
    mappings = {
        'vzw cell': 'Verizon',
        'verizon business': 'Verizon',
        'digi': 'AT&T',
        'at&t cell': 'AT&T',
        'accelerated': 'AT&T',
        'accelerated at&t': 'AT&T',
        'accerated at&t': 'AT&T',
        'first digital': 'FirstNet',
        'starlink': 'SpaceX'
    }
    
    provider_lower = provider.lower().strip()
    
    # Remove serial numbers and extra info
    provider_clean = re.sub(r'serial.*$|kitp.*$', '', provider_lower).strip()
    
    # Check mappings
    for key, value in mappings.items():
        if key in provider_clean:
            return value
    
    return provider

def get_candidates():
    """Find Cell/Satellite sites that need Non-DSR circuits"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Query for sites with Cell/Satellite that may need circuits
    query = """
        WITH cell_satellite_wans AS (
            SELECT 
                ec.network_name,
                -- WAN1 Cell/Satellite
                CASE WHEN LOWER(ec.wan1_speed) IN ('cell', 'satellite') 
                     THEN ec.wan1_provider END as wan1_cell_provider,
                CASE WHEN LOWER(ec.wan1_speed) IN ('cell', 'satellite')
                     THEN ec.wan1_speed END as wan1_cell_speed,
                -- WAN2 Cell/Satellite  
                CASE WHEN LOWER(ec.wan2_speed) IN ('cell', 'satellite')
                     THEN ec.wan2_provider END as wan2_cell_provider,
                CASE WHEN LOWER(ec.wan2_speed) IN ('cell', 'satellite')
                     THEN ec.wan2_speed END as wan2_cell_speed
            FROM enriched_circuits ec
            WHERE 
                LOWER(ec.wan1_speed) IN ('cell', 'satellite') OR 
                LOWER(ec.wan2_speed) IN ('cell', 'satellite')
        )
        SELECT 
            cs.*,
            -- Check existing circuits
            (SELECT COUNT(*) FROM circuits c 
             WHERE c.site_name = cs.network_name 
             AND c.status = 'Enabled') as total_circuits,
            (SELECT COUNT(*) FROM circuits c 
             WHERE c.site_name = cs.network_name 
             AND c.circuit_purpose = 'Primary'
             AND c.status = 'Enabled') as primary_circuits,
            (SELECT COUNT(*) FROM circuits c 
             WHERE c.site_name = cs.network_name 
             AND c.circuit_purpose = 'Secondary'
             AND c.status = 'Enabled') as secondary_circuits
        FROM cell_satellite_wans cs
        ORDER BY cs.network_name
    """
    
    cursor.execute(query)
    sites = cursor.fetchall()
    
    candidates = []
    
    for site in sites:
        # Check WAN1 Cell/Satellite
        if site['wan1_cell_provider'] and site['wan1_cell_speed']:
            # Normalize provider
            normalized_provider = normalize_provider(site['wan1_cell_provider'])
            
            # Check if we already have a Primary circuit for this provider
            cursor.execute("""
                SELECT COUNT(*) FROM circuits 
                WHERE site_name = %s 
                AND circuit_purpose = 'Primary'
                AND status = 'Enabled'
                AND (
                    provider_name = %s OR
                    provider_name = %s
                )
            """, (site['network_name'], site['wan1_cell_provider'], normalized_provider))
            
            existing = cursor.fetchone()['count']
            
            if existing == 0:
                candidates.append({
                    'site_name': site['network_name'],
                    'wan': 'WAN1',
                    'provider': normalized_provider,
                    'original_provider': site['wan1_cell_provider'],
                    'speed': site['wan1_cell_speed'],
                    'purpose': 'Primary'
                })
        
        # Check WAN2 Cell/Satellite
        if site['wan2_cell_provider'] and site['wan2_cell_speed']:
            # Normalize provider
            normalized_provider = normalize_provider(site['wan2_cell_provider'])
            
            # Check if we already have a Secondary circuit for this provider
            cursor.execute("""
                SELECT COUNT(*) FROM circuits 
                WHERE site_name = %s 
                AND circuit_purpose = 'Secondary'
                AND status = 'Enabled'
                AND (
                    provider_name = %s OR
                    provider_name = %s
                )
            """, (site['network_name'], site['wan2_cell_provider'], normalized_provider))
            
            existing = cursor.fetchone()['count']
            
            if existing == 0:
                candidates.append({
                    'site_name': site['network_name'],
                    'wan': 'WAN2',
                    'provider': normalized_provider,
                    'original_provider': site['wan2_cell_provider'],
                    'speed': site['wan2_cell_speed'],
                    'purpose': 'Secondary'
                })
    
    cursor.close()
    conn.close()
    
    return candidates

def create_circuits(candidates):
    """Create the Non-DSR circuits"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created = 0
    
    for candidate in candidates:
        try:
            # Get next ID
            cursor.execute("SELECT MAX(id) FROM circuits")
            max_id = cursor.fetchone()[0] or 0
            next_id = max_id + 1
            
            # Insert circuit
            insert_query = """
                INSERT INTO circuits (
                    id, site_name, site_id, circuit_purpose, status,
                    provider_name, details_ordered_service_speed,
                    billing_monthly_cost, data_source, record_number,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, NULL, %s, 'Enabled', %s, %s, 0.0, 'Non-DSR', NULL, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                next_id,
                candidate['site_name'],
                candidate['purpose'],
                candidate['provider'],
                candidate['speed'].capitalize(),
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            created += 1
            print(f"✓ Created {candidate['purpose']} circuit for {candidate['site_name']}: "
                  f"{candidate['provider']} ({candidate['original_provider']}) - {candidate['speed']}")
            
        except Exception as e:
            print(f"✗ Error creating circuit for {candidate['site_name']}: {e}")
            conn.rollback()
            continue
    
    if created > 0:
        conn.commit()
        print(f"\n✓ Successfully created {created} Non-DSR circuits")
    else:
        conn.rollback()
    
    cursor.close()
    conn.close()
    
    return created

def main():
    """Main process"""
    
    print("=== Creating Non-DSR Circuits for Cell/Satellite Sites ===\n")
    
    # Get candidates
    candidates = get_candidates()
    
    if not candidates:
        print("No Cell/Satellite sites need Non-DSR circuits")
        return
    
    # Group by provider for summary
    provider_summary = {}
    for c in candidates:
        provider = c['provider']
        if provider not in provider_summary:
            provider_summary[provider] = 0
        provider_summary[provider] += 1
    
    print(f"Found {len(candidates)} circuits to create:\n")
    
    print("By Provider:")
    for provider, count in sorted(provider_summary.items(), key=lambda x: -x[1]):
        print(f"  {provider}: {count}")
    
    print(f"\nFirst 20 candidates:")
    print(f"{'Site':<10} {'WAN':<5} {'Provider':<15} {'Original':<20} {'Speed':<10} {'Purpose'}")
    print("-" * 85)
    
    for c in candidates[:20]:
        print(f"{c['site_name']:<10} {c['wan']:<5} {c['provider']:<15} "
              f"{c['original_provider'][:19]:<20} {c['speed']:<10} {c['purpose']}")
    
    if len(candidates) > 20:
        print(f"\n... and {len(candidates) - 20} more")
    
    # Create circuits
    print(f"\n=== Creating {len(candidates)} Non-DSR circuits ===\n")
    
    created = create_circuits(candidates)
    
    print(f"\n=== Complete ===")
    print(f"✓ Created {created} of {len(candidates)} Non-DSR circuits")

if __name__ == "__main__":
    main()