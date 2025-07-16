#!/usr/bin/env python3
"""
Sync DSR circuit data to enriched_circuits table with ARIN verification
Updates enriched_circuits with DSR provider/speed/cost only when ARIN matches
"""

import psycopg2
import psycopg2.extras
from config import Config
import re
import csv
from datetime import datetime

def normalize_provider(provider):
    """Normalize provider name for comparison"""
    if not provider:
        return ""
    
    provider = provider.lower()
    
    # Common mappings
    mappings = {
        'at&t': ['att', 'at&t enterprises', 'at & t'],
        'verizon': ['vzw', 'verizon business', 'vz'],
        'comcast': ['xfinity', 'comcast cable'],
        'centurylink': ['embarq', 'qwest', 'lumen'],
        'cox': ['cox business', 'cox communications'],
        'charter': ['spectrum'],
        'brightspeed': ['level 3']
    }
    
    # Check if provider contains any of these key terms
    for key, variants in mappings.items():
        if key in provider:
            return key
        for variant in variants:
            if variant in provider:
                return key
    
    # Return first word if no mapping found
    return provider.split()[0] if provider else ""

def providers_match(dsr_provider, arin_provider):
    """Check if DSR and ARIN providers are compatible"""
    if not dsr_provider or not arin_provider:
        return False
    
    dsr_norm = normalize_provider(dsr_provider)
    arin_norm = normalize_provider(arin_provider)
    
    return dsr_norm == arin_norm

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== DSR to Enriched Sync with ARIN Verification ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Get all sites with DSR circuits and their ARIN data
    cursor.execute("""
        SELECT DISTINCT
            c_primary.site_name,
            c_primary.provider_name as primary_provider,
            c_primary.details_service_speed as primary_speed,
            c_primary.billing_monthly_cost as primary_cost,
            c_secondary.provider_name as secondary_provider,
            c_secondary.details_service_speed as secondary_speed,
            c_secondary.billing_monthly_cost as secondary_cost,
            m.wan1_arin_provider,
            m.wan2_arin_provider,
            e.wan1_provider as current_wan1_provider,
            e.wan2_provider as current_wan2_provider
        FROM circuits c_primary
        LEFT JOIN circuits c_secondary ON c_primary.site_name = c_secondary.site_name 
            AND c_secondary.circuit_purpose = 'Secondary' 
            AND c_secondary.status = 'Enabled'
        JOIN enriched_circuits e ON c_primary.site_name = e.network_name
        LEFT JOIN meraki_inventory m ON c_primary.site_name = m.network_name
        WHERE c_primary.circuit_purpose = 'Primary'
        AND c_primary.status = 'Enabled'
        AND c_primary.site_name NOT ILIKE '%hub%'
        AND c_primary.site_name NOT ILIKE '%lab%'
        AND c_primary.site_name NOT ILIKE '%voice%'
        AND c_primary.site_name NOT ILIKE '%test%'
        ORDER BY c_primary.site_name
    """)
    
    sites = cursor.fetchall()
    
    # Create results tracking
    results = {
        'wan1_matches': [],
        'wan1_mismatches': [],
        'wan2_matches': [],
        'wan2_mismatches': [],
        'updates_made': []
    }
    
    print(f"Found {len(sites)} DSR sites to process")
    print()
    
    try:
        for site in sites:
            site_name = site['site_name']
            
            # Check WAN1 (Primary circuit)
            wan1_can_update = False
            if site['primary_provider'] and site['wan1_arin_provider']:
                if providers_match(site['primary_provider'], site['wan1_arin_provider']):
                    results['wan1_matches'].append({
                        'site': site_name,
                        'dsr_provider': site['primary_provider'],
                        'arin_provider': site['wan1_arin_provider']
                    })
                    wan1_can_update = True
                else:
                    results['wan1_mismatches'].append({
                        'site': site_name,
                        'dsr_provider': site['primary_provider'],
                        'arin_provider': site['wan1_arin_provider']
                    })
            
            # Check WAN2 (Secondary circuit)
            wan2_can_update = False
            if site['secondary_provider'] and site['wan2_arin_provider']:
                if providers_match(site['secondary_provider'], site['wan2_arin_provider']):
                    results['wan2_matches'].append({
                        'site': site_name,
                        'dsr_provider': site['secondary_provider'],
                        'arin_provider': site['wan2_arin_provider']
                    })
                    wan2_can_update = True
                else:
                    results['wan2_mismatches'].append({
                        'site': site_name,
                        'dsr_provider': site['secondary_provider'],
                        'arin_provider': site['wan2_arin_provider']
                    })
            
            # Update enriched_circuits if we have matches
            if wan1_can_update or wan2_can_update:
                update_fields = []
                update_values = []
                
                if wan1_can_update:
                    update_fields.extend(['wan1_provider = %s', 'wan1_speed = %s'])
                    update_values.extend([site['primary_provider'], site['primary_speed']])
                
                if wan2_can_update:
                    update_fields.extend(['wan2_provider = %s', 'wan2_speed = %s'])
                    update_values.extend([site['secondary_provider'], site['secondary_speed']])
                
                update_fields.append('last_updated = NOW()')
                update_values.append(site_name)
                
                update_sql = f"""
                    UPDATE enriched_circuits
                    SET {', '.join(update_fields)}
                    WHERE network_name = %s
                """
                
                cursor.execute(update_sql, update_values)
                
                if cursor.rowcount > 0:
                    results['updates_made'].append({
                        'site': site_name,
                        'wan1_updated': wan1_can_update,
                        'wan2_updated': wan2_can_update,
                        'wan1_provider': site['primary_provider'] if wan1_can_update else None,
                        'wan2_provider': site['secondary_provider'] if wan2_can_update else None
                    })
        
        # Commit all updates
        conn.commit()
        
        # Generate report
        print("=== UPDATE SUMMARY ===")
        print(f"Total updates made: {len(results['updates_made'])}")
        print(f"WAN1 matches found: {len(results['wan1_matches'])}")
        print(f"WAN1 mismatches: {len(results['wan1_mismatches'])}")
        print(f"WAN2 matches found: {len(results['wan2_matches'])}")
        print(f"WAN2 mismatches: {len(results['wan2_mismatches'])}")
        
        # Create detailed CSV report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/usr/local/bin/dsr_arin_sync_report_{timestamp}.csv'
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Site Name',
                'Interface',
                'Status',
                'DSR Provider',
                'ARIN Provider',
                'Match',
                'Action Taken'
            ])
            
            # Write WAN1 results
            for match in results['wan1_matches']:
                writer.writerow([
                    match['site'],
                    'WAN1',
                    'MATCH',
                    match['dsr_provider'],
                    match['arin_provider'],
                    'Yes',
                    'Updated'
                ])
            
            for mismatch in results['wan1_mismatches']:
                writer.writerow([
                    mismatch['site'],
                    'WAN1',
                    'MISMATCH',
                    mismatch['dsr_provider'],
                    mismatch['arin_provider'],
                    'No',
                    'Skipped'
                ])
            
            # Write WAN2 results
            for match in results['wan2_matches']:
                writer.writerow([
                    match['site'],
                    'WAN2',
                    'MATCH',
                    match['dsr_provider'],
                    match['arin_provider'],
                    'Yes',
                    'Updated'
                ])
            
            for mismatch in results['wan2_mismatches']:
                writer.writerow([
                    mismatch['site'],
                    'WAN2',
                    'MISMATCH',
                    mismatch['dsr_provider'],
                    mismatch['arin_provider'],
                    'No',
                    'Skipped'
                ])
        
        print(f"\nDetailed report saved to: {filename}")
        
        # Show examples of mismatches
        if results['wan1_mismatches'] or results['wan2_mismatches']:
            print("\n=== MISMATCHES TO INVESTIGATE ===")
            
            all_mismatches = results['wan1_mismatches'] + results['wan2_mismatches']
            for mismatch in all_mismatches[:10]:  # Show first 10
                print(f"  {mismatch['site']}: DSR='{mismatch['dsr_provider']}' vs ARIN='{mismatch['arin_provider']}'")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print(f"\nCompleted at: {datetime.now()}")