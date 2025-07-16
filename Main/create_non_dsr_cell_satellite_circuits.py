#!/usr/bin/env python3
"""
Create Non-DSR circuits for Cell and Satellite sites where:
1. Speed = Cell or Satellite
2. ARIN provider matches device notes provider
3. No existing circuit in the database
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
from datetime import datetime
from models import Circuit, db
from config import Config
from thefuzz import fuzz
import sqlalchemy

def get_db_connection():
    """Get database connection"""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    url = engine.url
    
    return psycopg2.connect(
        host=url.host,
        port=url.port,
        database=url.database,
        user=url.username,
        password=url.password
    )

def get_next_circuit_id(conn):
    """Get the next available circuit ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM circuits")
    result = cursor.fetchone()[0]
    cursor.close()
    return (result or 0) + 1

def providers_match(provider1, provider2):
    """Check if two providers match with fuzzy logic"""
    if not provider1 or not provider2:
        return False
    
    # Normalize
    p1 = provider1.lower().strip()
    p2 = provider2.lower().strip()
    
    # Exact match
    if p1 == p2:
        return True
    
    # Fuzzy match
    score = max(
        fuzz.ratio(p1, p2),
        fuzz.partial_ratio(p1, p2)
    )
    
    return score >= 80

def analyze_cell_satellite_sites():
    """Find sites with Cell/Satellite that need Non-DSR circuits"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Analyzing Cell/Satellite Sites for Non-DSR Circuit Creation ===\n")
    
    # Query for enriched circuits with Cell/Satellite
    query = """
        SELECT DISTINCT
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan1_arin_org,
            ec.wan2_provider,
            ec.wan2_speed,
            ec.wan2_arin_org,
            -- Check if circuits exist
            (SELECT COUNT(*) FROM circuits c 
             WHERE c.site_name = ec.network_name 
             AND c.status = 'Enabled') as circuit_count,
            -- Get device notes for comparison
            md.device_notes
        FROM enriched_circuits ec
        LEFT JOIN meraki_mx_uplink_data md ON ec.network_name = md.network_name
        WHERE 
            -- Has Cell or Satellite speed
            (LOWER(ec.wan1_speed) IN ('cell', 'satellite') OR 
             LOWER(ec.wan2_speed) IN ('cell', 'satellite'))
            -- Has ARIN provider data
            AND (ec.wan1_arin_org IS NOT NULL OR ec.wan2_arin_org IS NOT NULL)
        ORDER BY ec.network_name
    """
    
    cursor.execute(query)
    sites = cursor.fetchall()
    
    print(f"Found {len(sites)} sites with Cell/Satellite\n")
    
    # Analyze each site
    candidates = []
    
    for site in sites:
        site_name = site['network_name']
        circuit_count = site['circuit_count']
        
        # Check WAN1
        if site['wan1_speed'] and site['wan1_speed'].lower() in ['cell', 'satellite']:
            wan1_provider = site['wan1_provider']
            wan1_arin = site['wan1_arin_org']
            
            # Check if providers match
            if wan1_provider and wan1_arin and providers_match(wan1_provider, wan1_arin):
                # Check if circuit already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM circuits 
                    WHERE site_name = %s 
                    AND provider_name ILIKE %s
                    AND status = 'Enabled'
                """, (site_name, f'%{wan1_provider}%'))
                
                existing = cursor.fetchone()['count']
                
                if existing == 0:
                    candidates.append({
                        'site_name': site_name,
                        'wan': 'WAN1',
                        'provider': wan1_provider,
                        'arin_provider': wan1_arin,
                        'speed': site['wan1_speed'],
                        'purpose': 'Primary'
                    })
        
        # Check WAN2
        if site['wan2_speed'] and site['wan2_speed'].lower() in ['cell', 'satellite']:
            wan2_provider = site['wan2_provider']
            wan2_arin = site['wan2_arin_org']
            
            # Check if providers match
            if wan2_provider and wan2_arin and providers_match(wan2_provider, wan2_arin):
                # Check if circuit already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM circuits 
                    WHERE site_name = %s 
                    AND provider_name ILIKE %s
                    AND status = 'Enabled'
                """, (site_name, f'%{wan2_provider}%'))
                
                existing = cursor.fetchone()['count']
                
                if existing == 0:
                    candidates.append({
                        'site_name': site_name,
                        'wan': 'WAN2',
                        'provider': wan2_provider,
                        'arin_provider': wan2_arin,
                        'speed': site['wan2_speed'],
                        'purpose': 'Secondary'
                    })
    
    conn.close()
    
    return candidates

def create_non_dsr_circuits(candidates):
    """Create Non-DSR circuits for the candidates"""
    
    if not candidates:
        print("No candidates found for Non-DSR circuit creation")
        return 0
    
    print(f"\n=== Creating {len(candidates)} Non-DSR Circuits ===\n")
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_count = 0
    
    for candidate in candidates:
        try:
            # Get next ID
            next_id = get_next_circuit_id(conn)
            
            # Insert the circuit
            insert_query = """
                INSERT INTO circuits (
                    id, site_name, site_id, circuit_purpose, status,
                    provider_name, details_ordered_service_speed, 
                    billing_monthly_cost, data_source, record_number,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                next_id,
                candidate['site_name'],
                None,  # site_id
                candidate['purpose'],
                'Enabled',
                candidate['provider'],
                candidate['speed'].capitalize(),  # Cell or Satellite
                0.0,  # billing_monthly_cost
                'Non-DSR',
                None,  # record_number NULL for Non-DSR
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            created_count += 1
            
            print(f"✓ Created {candidate['purpose']} circuit for {candidate['site_name']}: {candidate['provider']} ({candidate['speed']})")
            
        except Exception as e:
            print(f"✗ Error creating circuit for {candidate['site_name']}: {e}")
            conn.rollback()
            continue
    
    if created_count > 0:
        print(f"\n=== Committing {created_count} new circuits ===")
        conn.commit()
        print("✓ Changes committed successfully!")
    else:
        conn.rollback()
        print("✗ No circuits were created")
    
    cursor.close()
    conn.close()
    
    return created_count

def main():
    """Main process"""
    
    # Find candidates
    candidates = analyze_cell_satellite_sites()
    
    if not candidates:
        print("\nNo Cell/Satellite sites need Non-DSR circuits")
        return
    
    # Show what will be created
    print(f"\n=== Found {len(candidates)} circuits to create ===\n")
    
    print(f"{'Site':<15} {'WAN':<6} {'Provider':<25} {'ARIN Provider':<25} {'Speed':<10} {'Purpose'}")
    print("-" * 110)
    
    for c in candidates[:20]:  # Show first 20
        print(f"{c['site_name']:<15} {c['wan']:<6} {c['provider']:<25} {c['arin_provider']:<25} {c['speed']:<10} {c['purpose']}")
    
    if len(candidates) > 20:
        print(f"\n... and {len(candidates) - 20} more")
    
    # Auto-proceed for non-interactive execution
    print(f"\nCreating {len(candidates)} Non-DSR circuits...")
    
    created = create_non_dsr_circuits(candidates)
    print(f"\n=== Complete ===")
    print(f"✓ Created {created} Non-DSR circuits for Cell/Satellite sites")

if __name__ == "__main__":
    main()