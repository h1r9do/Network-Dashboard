#!/usr/bin/env python3
"""Export detailed delta analysis comparing CSV vs Database with WAN interfaces"""

import csv
import subprocess
import json
from datetime import datetime

print("=== Generating Detailed Delta Export ===\n")

# First, read all enabled circuits from CSV
csv_circuits = {}
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            site_name = row['Site Name'].strip()
            site_id = row.get('Site ID', '').strip()
            
            if site_name not in csv_circuits:
                csv_circuits[site_name] = []
            
            csv_circuits[site_name].append({
                'site_id': site_id,
                'circuit_purpose': row.get('circuit_purpose', ''),
                'provider_name': row.get('provider_name', ''),
                'service_speed': row.get('details_service_speed', ''),
                'monthly_cost': row.get('billing_monthly_cost', ''),
                'ip_address': row.get('ip_address_start', ''),
                'record_number': row.get('record_number', '')
            })

print(f"Found {len(csv_circuits)} sites with enabled circuits in CSV")
print(f"Total circuits: {sum(len(circuits) for circuits in csv_circuits.values())}")

# Create comprehensive query to get all data
query = """
WITH csv_enabled_sites AS (
    SELECT UNNEST(ARRAY[{sites}]::text[]) as site_name
),
delta_analysis AS (
    SELECT 
        ces.site_name,
        -- Circuit data from database
        c.site_id as db_site_id,
        c.circuit_purpose as db_circuit_purpose,
        c.provider_name as db_provider,
        c.details_service_speed as db_speed,
        c.billing_monthly_cost as db_cost,
        c.ip_address_start as db_ip,
        c.status as db_status,
        c.data_source,
        -- Meraki/Enriched data
        mi.network_name as meraki_network,
        mi.device_tags,
        ec.wan1_provider as meraki_wan1_provider,
        ec.wan1_speed as meraki_wan1_speed,
        ec.wan1_cost as meraki_wan1_cost,
        mi.wan1_ip as meraki_wan1_ip,
        ec.wan2_provider as meraki_wan2_provider,
        ec.wan2_speed as meraki_wan2_speed,
        ec.wan2_cost as meraki_wan2_cost,
        mi.wan2_ip as meraki_wan2_ip,
        -- DSR badge eligibility
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
            WHEN mi.network_name ILIKE '%voice%' THEN 'Voice site'
            WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') OR
                 (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 'Has IP addresses'
            ELSE 'Eligible for DSR badge'
        END as exclusion_reason,
        -- Provider matching
        CASE 
            WHEN c.provider_name IS NULL THEN 'No provider in circuit'
            WHEN LOWER(c.provider_name) = LOWER(ec.wan1_provider) THEN 'Matches WAN1'
            WHEN LOWER(c.provider_name) = LOWER(ec.wan2_provider) THEN 'Matches WAN2'
            WHEN ec.wan1_provider IS NOT NULL AND 
                 LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%' THEN 'Partial match WAN1'
            WHEN ec.wan2_provider IS NOT NULL AND 
                 LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%' THEN 'Partial match WAN2'
            ELSE 'No provider match'
        END as provider_match_status
    FROM csv_enabled_sites ces
    LEFT JOIN circuits c ON LOWER(ces.site_name) = LOWER(c.site_name) AND c.status = 'Enabled'
    LEFT JOIN meraki_inventory mi ON LOWER(ces.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(ces.site_name) = LOWER(ec.network_name)
    ORDER BY ces.site_name, c.circuit_purpose
)
SELECT * FROM delta_analysis;
"""

# Format site list for query
site_list = "'" + "','".join([s.replace("'", "''") for s in csv_circuits.keys()]) + "'"
formatted_query = query.format(sites=site_list)

# Execute query and save to temporary file
with open('/tmp/delta_query.sql', 'w') as f:
    f.write(formatted_query)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-f', '/tmp/delta_query.sql'],
    capture_output=True, text=True
)

# Process results and create output CSV
output_file = f'/usr/local/bin/Main/dsr_delta_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

with open(output_file, 'w', newline='') as csvfile:
    fieldnames = [
        'site_name', 'csv_site_id', 'csv_circuit_purpose', 'csv_provider', 'csv_speed', 
        'csv_monthly_cost', 'csv_ip_address', 'db_site_id', 'db_circuit_purpose', 
        'db_provider', 'db_speed', 'db_cost', 'db_ip', 'db_status', 'data_source',
        'meraki_network_exists', 'has_discount_tire_tag', 'meraki_wan1_provider', 
        'meraki_wan1_speed', 'meraki_wan1_cost', 'meraki_wan1_ip', 'meraki_wan2_provider',
        'meraki_wan2_speed', 'meraki_wan2_cost', 'meraki_wan2_ip', 'exclusion_reason',
        'provider_match_status', 'would_get_dsr_badge'
    ]
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    # Parse database results
    db_results = {}
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 20:
                    site_name = parts[0]
                    if site_name not in db_results:
                        db_results[site_name] = []
                    db_results[site_name].append(parts)
    
    # Write combined data
    rows_written = 0
    for site_name, csv_circs in csv_circuits.items():
        db_data = db_results.get(site_name, [])
        
        for csv_circ in csv_circs:
            # Find matching DB record
            db_match = None
            if db_data:
                for db_rec in db_data:
                    if len(db_rec) > 2 and db_rec[2] == csv_circ['circuit_purpose']:
                        db_match = db_rec
                        break
                if not db_match:  # If no purpose match, take first
                    db_match = db_data[0]
            
            # Build row
            row = {
                'site_name': site_name,
                'csv_site_id': csv_circ['site_id'],
                'csv_circuit_purpose': csv_circ['circuit_purpose'],
                'csv_provider': csv_circ['provider_name'],
                'csv_speed': csv_circ['service_speed'],
                'csv_monthly_cost': csv_circ['monthly_cost'],
                'csv_ip_address': csv_circ['ip_address']
            }
            
            if db_match and len(db_match) >= 20:
                row.update({
                    'db_site_id': db_match[1] if db_match[1] else '',
                    'db_circuit_purpose': db_match[2] if db_match[2] else '',
                    'db_provider': db_match[3] if db_match[3] else '',
                    'db_speed': db_match[4] if db_match[4] else '',
                    'db_cost': db_match[5] if db_match[5] else '',
                    'db_ip': db_match[6] if db_match[6] else '',
                    'db_status': db_match[7] if db_match[7] else '',
                    'data_source': db_match[8] if db_match[8] else '',
                    'meraki_network_exists': 'Yes' if db_match[9] else 'No',
                    'has_discount_tire_tag': 'Yes' if db_match[10] and 'Discount-Tire' in str(db_match[10]) else 'No',
                    'meraki_wan1_provider': db_match[11] if db_match[11] else '',
                    'meraki_wan1_speed': db_match[12] if db_match[12] else '',
                    'meraki_wan1_cost': db_match[13] if db_match[13] else '',
                    'meraki_wan1_ip': db_match[14] if db_match[14] else '',
                    'meraki_wan2_provider': db_match[15] if db_match[15] else '',
                    'meraki_wan2_speed': db_match[16] if db_match[16] else '',
                    'meraki_wan2_cost': db_match[17] if db_match[17] else '',
                    'meraki_wan2_ip': db_match[18] if db_match[18] else '',
                    'exclusion_reason': db_match[19] if len(db_match) > 19 else '',
                    'provider_match_status': db_match[20] if len(db_match) > 20 else ''
                })
                
                # Determine if would get DSR badge
                would_badge = (
                    row['db_status'] == 'Enabled' and
                    row['data_source'] == 'csv_import' and
                    row['has_discount_tire_tag'] == 'Yes' and
                    row['exclusion_reason'] == 'Eligible for DSR badge' and
                    row['provider_match_status'] in ['Matches WAN1', 'Matches WAN2', 'Partial match WAN1', 'Partial match WAN2']
                )
                row['would_get_dsr_badge'] = 'Yes' if would_badge else 'No'
            else:
                # No database match
                row.update({
                    'db_site_id': 'NOT IN DB',
                    'db_circuit_purpose': 'NOT IN DB',
                    'db_provider': 'NOT IN DB',
                    'db_speed': 'NOT IN DB',
                    'db_cost': 'NOT IN DB',
                    'db_ip': 'NOT IN DB',
                    'db_status': 'NOT IN DB',
                    'data_source': 'NOT IN DB',
                    'meraki_network_exists': 'No',
                    'has_discount_tire_tag': 'No',
                    'meraki_wan1_provider': '',
                    'meraki_wan1_speed': '',
                    'meraki_wan1_cost': '',
                    'meraki_wan1_ip': '',
                    'meraki_wan2_provider': '',
                    'meraki_wan2_speed': '',
                    'meraki_wan2_cost': '',
                    'meraki_wan2_ip': '',
                    'exclusion_reason': 'Not in database',
                    'provider_match_status': 'Not in database',
                    'would_get_dsr_badge': 'No'
                })
            
            writer.writerow(row)
            rows_written += 1

print(f"\nExport complete!")
print(f"File: {output_file}")
print(f"Rows written: {rows_written}")

# Generate summary
dsr_badge_count = 0
exclusion_counts = {}

# Re-read the file to generate summary
with open(output_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['would_get_dsr_badge'] == 'Yes':
            dsr_badge_count += 1
        else:
            reason = row['exclusion_reason']
            exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1

print("\nSummary:")
print(f"- Would get DSR badge: {dsr_badge_count}")
print(f"- Excluded: {rows_written - dsr_badge_count}")
print("\nExclusion breakdown:")
for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {reason}: {count}")

# Clean up
subprocess.run(['rm', '-f', '/tmp/delta_query.sql'], capture_output=True)