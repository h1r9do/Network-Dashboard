#!/usr/bin/env python3
"""
Test script to verify the enriched -> circuits flow logic
This simulates what would happen without actually updating production data
"""

import psycopg2
import psycopg2.extras
from config import Config
import re
from datetime import datetime
import csv

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

def providers_match(provider1, provider2):
    """Check if two providers match"""
    if not provider1 or not provider2:
        return False
    
    norm1 = normalize_provider(provider1)
    norm2 = normalize_provider(provider2)
    
    return norm1 == norm2

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
    
    print("=== Test: Enriched -> Circuits Flow Logic ===")
    print(f"Generated: {datetime.now()}")
    print("\nThis is a DRY RUN - no actual updates will be made")
    print()
    
    # Step 1: Find all non-DSR circuits in circuits table
    print("Step 1: Finding non-DSR circuits...")
    cursor.execute("""
        SELECT 
            c.site_name,
            c.record_number,
            c.provider_name as circuits_provider,
            c.details_service_speed as circuits_speed,
            c.circuit_purpose,
            c.status,
            c.manual_override,
            e.wan1_provider as enriched_wan1_provider,
            e.wan1_speed as enriched_wan1_speed,
            e.wan1_confirmed,
            e.wan2_provider as enriched_wan2_provider,
            e.wan2_speed as enriched_wan2_speed,
            e.wan2_confirmed
        FROM circuits c
        JOIN enriched_circuits e ON c.site_name = e.network_name
        WHERE c.status = 'Enabled'
        AND c.site_name NOT IN (
            -- Exclude sites that have DSR Primary circuits
            SELECT DISTINCT site_name 
            FROM circuits 
            WHERE circuit_purpose = 'Primary' 
            AND status = 'Enabled'
            AND provider_name NOT LIKE '%Unknown%'
            AND provider_name IS NOT NULL
            AND provider_name != ''
        )
        ORDER BY c.site_name, c.circuit_purpose
    """)
    
    non_dsr_circuits = cursor.fetchall()
    
    print(f"Found {len(non_dsr_circuits)} non-DSR circuits")
    
    # Step 2: Check for manually confirmed enriched data
    updates_needed = []
    manual_override_protected = []
    
    for circuit in non_dsr_circuits:
        site = circuit['site_name']
        purpose = circuit['circuit_purpose']
        
        # Skip if manual_override is set
        if circuit['manual_override']:
            manual_override_protected.append({
                'site': site,
                'purpose': purpose,
                'reason': 'manual_override flag set'
            })
            continue
        
        # Determine which enriched data to use based on circuit purpose
        if purpose == 'Primary':
            enriched_provider = circuit['enriched_wan1_provider']
            enriched_speed = circuit['enriched_wan1_speed']
            is_confirmed = circuit['wan1_confirmed']
        else:  # Secondary
            enriched_provider = circuit['enriched_wan2_provider']
            enriched_speed = circuit['enriched_wan2_speed']
            is_confirmed = circuit['wan2_confirmed']
        
        # Check if update is needed
        current_provider = circuit['circuits_provider'] or ''
        current_speed = circuit['circuits_speed'] or ''
        
        provider_changed = not providers_match(current_provider, enriched_provider)
        speed_changed = str(current_speed).strip() != str(enriched_speed).strip()
        
        if (provider_changed or speed_changed) and is_confirmed:
            updates_needed.append({
                'site': site,
                'record_number': circuit['record_number'],
                'purpose': purpose,
                'current_provider': current_provider,
                'new_provider': enriched_provider,
                'current_speed': current_speed,
                'new_speed': enriched_speed,
                'reason': 'Confirmed enriched data differs from circuits table'
            })
    
    # Step 3: Show what would be updated
    print(f"\n=== PROPOSED UPDATES ===")
    print(f"Total non-DSR circuits: {len(non_dsr_circuits)}")
    print(f"Protected by manual_override: {len(manual_override_protected)}")
    print(f"Updates needed: {len(updates_needed)}")
    
    if updates_needed:
        print(f"\nShowing first 20 updates:")
        for i, update in enumerate(updates_needed[:20]):
            print(f"\n{i+1}. {update['site']} ({update['purpose']}):")
            print(f"   Record #: {update['record_number']}")
            print(f"   Provider: '{update['current_provider']}' → '{update['new_provider']}'")
            print(f"   Speed: '{update['current_speed']}' → '{update['new_speed']}'")
            print(f"   Reason: {update['reason']}")
    
    # Step 4: Check for DSR circuits that should NOT be updated
    print(f"\n=== DSR CIRCUIT PROTECTION CHECK ===")
    cursor.execute("""
        SELECT 
            c.site_name,
            c.circuit_purpose,
            c.provider_name,
            c.status,
            e.wan1_provider,
            e.wan2_provider
        FROM circuits c
        JOIN enriched_circuits e ON c.site_name = e.network_name
        WHERE c.status = 'Enabled'
        AND c.circuit_purpose = 'Primary'
        AND c.provider_name IS NOT NULL
        AND c.provider_name != ''
        AND c.provider_name NOT LIKE '%Unknown%'
        LIMIT 10
    """)
    
    dsr_samples = cursor.fetchall()
    print(f"Sample DSR circuits (these would be PROTECTED from enriched updates):")
    for circuit in dsr_samples[:5]:
        print(f"  {circuit['site_name']}: DSR='{circuit['provider_name']}' (would NOT be overwritten)")
    
    # Step 5: Generate test SQL
    if updates_needed:
        print(f"\n=== TEST SQL (NOT EXECUTED) ===")
        print("-- These updates would be applied to non-DSR circuits only:")
        for update in updates_needed[:5]:
            print(f"""
UPDATE circuits 
SET provider_name = '{update['new_provider']}',
    details_service_speed = '{update['new_speed']}',
    updated_at = NOW()
WHERE record_number = {update['record_number']}
AND manual_override IS NOT TRUE
AND site_name NOT IN (
    SELECT DISTINCT site_name FROM circuits 
    WHERE circuit_purpose = 'Primary' 
    AND status = 'Enabled'
    AND provider_name NOT LIKE '%Unknown%'
);""")
    
    # Step 6: Export detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'/usr/local/bin/enriched_to_circuits_test_{timestamp}.csv'
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Site Name', 'Record Number', 'Circuit Purpose',
            'Current Provider', 'New Provider', 'Provider Match',
            'Current Speed', 'New Speed', 'Speed Match',
            'Is Confirmed', 'Would Update', 'Reason'
        ])
        
        for circuit in non_dsr_circuits:
            site = circuit['site_name']
            purpose = circuit['circuit_purpose']
            
            if purpose == 'Primary':
                enriched_provider = circuit['enriched_wan1_provider']
                enriched_speed = circuit['enriched_wan1_speed']
                is_confirmed = circuit['wan1_confirmed']
            else:
                enriched_provider = circuit['enriched_wan2_provider']
                enriched_speed = circuit['enriched_wan2_speed']
                is_confirmed = circuit['wan2_confirmed']
            
            current_provider = circuit['circuits_provider'] or ''
            current_speed = circuit['circuits_speed'] or ''
            
            provider_match = providers_match(current_provider, enriched_provider)
            speed_match = str(current_speed).strip() == str(enriched_speed).strip()
            would_update = (not provider_match or not speed_match) and is_confirmed and not circuit['manual_override']
            
            if circuit['manual_override']:
                reason = 'Protected by manual_override'
            elif not is_confirmed:
                reason = 'Not confirmed in enriched'
            elif provider_match and speed_match:
                reason = 'Already matches'
            else:
                reason = 'Needs update'
            
            writer.writerow([
                site, circuit['record_number'], purpose,
                current_provider, enriched_provider, provider_match,
                current_speed, enriched_speed, speed_match,
                is_confirmed, would_update, reason
            ])
    
    print(f"\nDetailed report saved to: {filename}")
    
    # Close connection
    conn.close()
    
    print("\n=== TEST COMPLETE ===")
    print("This was a dry run - no data was modified")
    print("\nKey findings:")
    print(f"- {len(non_dsr_circuits)} non-DSR circuits found")
    print(f"- {len(updates_needed)} would be updated with confirmed enriched data")
    print(f"- {len(manual_override_protected)} protected by manual_override flag")
    print(f"- DSR circuits would remain untouched (source of truth)")