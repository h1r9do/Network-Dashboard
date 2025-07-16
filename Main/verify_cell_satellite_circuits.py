#!/usr/bin/env python3
"""
Verify the Cell/Satellite Non-DSR circuits were created correctly
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
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

def main():
    """Verify Cell/Satellite Non-DSR circuits"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Verifying Cell/Satellite Non-DSR Circuits ===\n")
    
    # Count new Non-DSR circuits
    cursor.execute("""
        SELECT 
            COUNT(*) as total_circuits,
            COUNT(CASE WHEN data_source = 'Non-DSR' THEN 1 END) as non_dsr_circuits,
            COUNT(CASE WHEN data_source = 'Non-DSR' AND created_at >= CURRENT_DATE THEN 1 END) as created_today,
            COUNT(CASE WHEN data_source = 'Non-DSR' AND 
                       details_ordered_service_speed IN ('Cell', 'Satellite') THEN 1 END) as cell_satellite_circuits
        FROM circuits
        WHERE status = 'Enabled'
    """)
    
    stats = cursor.fetchone()
    
    print(f"Total enabled circuits: {stats['total_circuits']:,}")
    print(f"Total Non-DSR circuits: {stats['non_dsr_circuits']:,}")
    print(f"Created today: {stats['created_today']:,}")
    print(f"Cell/Satellite circuits: {stats['cell_satellite_circuits']:,}")
    
    # Check breakdown by provider
    print("\n=== Non-DSR Cell/Satellite Circuits by Provider ===\n")
    
    cursor.execute("""
        SELECT 
            provider_name,
            details_ordered_service_speed as speed,
            circuit_purpose as purpose,
            COUNT(*) as count
        FROM circuits
        WHERE data_source = 'Non-DSR'
        AND details_ordered_service_speed IN ('Cell', 'Satellite')
        AND status = 'Enabled'
        GROUP BY provider_name, details_ordered_service_speed, circuit_purpose
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    
    print(f"{'Provider':<20} {'Speed':<10} {'Purpose':<10} {'Count'}")
    print("-" * 55)
    
    for row in results:
        print(f"{row['provider_name']:<20} {row['speed']:<10} {row['purpose']:<10} {row['count']}")
    
    # Check some specific sites
    print("\n=== Sample Sites with New Cell/Satellite Circuits ===\n")
    
    cursor.execute("""
        SELECT 
            c.site_name,
            c.provider_name,
            c.details_ordered_service_speed as speed,
            c.circuit_purpose,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan2_provider,
            ec.wan2_speed
        FROM circuits c
        JOIN enriched_circuits ec ON c.site_name = ec.network_name
        WHERE c.data_source = 'Non-DSR'
        AND c.details_ordered_service_speed IN ('Cell', 'Satellite')
        AND c.status = 'Enabled'
        AND c.created_at >= CURRENT_DATE
        ORDER BY c.site_name
        LIMIT 10
    """)
    
    samples = cursor.fetchall()
    
    print(f"{'Site':<10} {'Circuit Provider':<15} {'Purpose':<10} {'Enriched WAN1':<20} {'Enriched WAN2':<20}")
    print("-" * 80)
    
    for sample in samples:
        wan1_info = f"{sample['wan1_provider'] or 'N/A'} ({sample['wan1_speed'] or 'N/A'})"[:19]
        wan2_info = f"{sample['wan2_provider'] or 'N/A'} ({sample['wan2_speed'] or 'N/A'})"[:19]
        
        print(f"{sample['site_name']:<10} {sample['provider_name']:<15} {sample['circuit_purpose']:<10} "
              f"{wan1_info:<20} {wan2_info:<20}")
    
    # Check impact on enrichment matching
    print("\n=== Impact on Enrichment Matching ===\n")
    
    # This would need to run after the next enrichment to see the full impact
    print("Note: Full impact will be visible after the next enrichment run")
    print("Expected improvements:")
    print("- Cell/Satellite sites will now have matching circuits")
    print("- Match rate should improve by ~460 sites")
    print("- These sites will show proper provider/speed/cost data")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()