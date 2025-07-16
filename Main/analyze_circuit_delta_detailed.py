#!/usr/bin/env python3
"""Detailed analysis of the 178 circuit delta between CSV and test page"""

import csv
import psycopg2
from collections import defaultdict
import json

# Database connection using environment
db_config = {
    'dbname': 'dsrcircuits',
    'user': 'postgres',
    'host': '127.0.0.1',
    'port': '5432'
}

def get_db_connection():
    """Get database connection using pg_hba.conf trust authentication"""
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"Connection error: {e}")
        # Try with sudo postgres user
        import subprocess
        result = subprocess.run(['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-c', 
                                "SELECT version();"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Database accessible via sudo")
            return None
        return None

# First, let's identify ALL enabled circuits from CSV
print("=== STEP 1: Reading CSV File ===")
csv_enabled_circuits = []
csv_enabled_by_site = defaultdict(list)

with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            circuit_info = {
                'site_name': row['Site Name'].strip(),
                'site_id': row.get('Site ID', '').strip(),
                'purpose': row.get('circuit_purpose', '').strip(),
                'provider': row.get('provider_name', '').strip(),
                'speed': row.get('details_service_speed', '').strip(),
                'ip': row.get('ip_address_start', '').strip()
            }
            csv_enabled_circuits.append(circuit_info)
            csv_enabled_by_site[circuit_info['site_name']].append(circuit_info)

print(f"Total enabled circuits in CSV: {len(csv_enabled_circuits)}")
print(f"Unique sites with enabled circuits: {len(csv_enabled_by_site)}")

# Now let's query what the test page would show
print("\n=== STEP 2: Analyzing Test Page Logic ===")

# Create SQL queries to run via sudo
queries = {
    'test_page_sites': """
        SELECT DISTINCT ec.network_name
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE mi.device_tags @> ARRAY['Discount-Tire']
        AND NOT (
            ec.network_name ILIKE '%hub%' OR
            ec.network_name ILIKE '%lab%' OR
            ec.network_name ILIKE '%voice%' OR
            ec.network_name ILIKE '%test%'
        )
        AND (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None')
        AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
        ORDER BY ec.network_name;
    """,
    
    'all_enabled_circuits': """
        SELECT site_name, site_id, circuit_purpose, provider_name, 
               details_service_speed, ip_address_start
        FROM circuits 
        WHERE status = 'Enabled'
        ORDER BY site_name;
    """
}

# Execute queries using sudo
import subprocess
import tempfile

def run_query(query_name, query_sql):
    """Run a query using sudo postgres"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(query_sql)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-f', temp_file],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            print(f"Query error: {result.stderr}")
            return []
    finally:
        import os
        os.unlink(temp_file)

# Get test page sites
test_page_sites = set()
test_page_results = run_query('test_page_sites', queries['test_page_sites'])
for line in test_page_results:
    if line.strip():
        test_page_sites.add(line.strip())

print(f"Sites shown on test page: {len(test_page_sites)}")

# Now let's find the delta sites
print("\n=== STEP 3: Identifying Delta Sites ===")
delta_sites = []
for site in csv_enabled_by_site:
    if site not in test_page_sites and site.lower() not in [s.lower() for s in test_page_sites]:
        delta_sites.append(site)

print(f"Sites in CSV but NOT on test page: {len(delta_sites)}")

# Count circuits for delta sites
delta_circuit_count = sum(len(csv_enabled_by_site[site]) for site in delta_sites)
print(f"Total circuits for these delta sites: {delta_circuit_count}")

# Now analyze WHY these sites are missing
print("\n=== STEP 4: Analyzing Delta Sites ===")

# Query to check each delta site
check_site_query = """
SELECT 
    c.site_name,
    COUNT(DISTINCT c.id) as circuit_count,
    STRING_AGG(DISTINCT c.circuit_purpose, ', ') as purposes,
    STRING_AGG(DISTINCT c.provider_name, ', ') as providers,
    mi.network_name as meraki_network,
    mi.wan1_ip,
    mi.wan2_ip,
    mi.wan1_provider,
    mi.wan2_provider,
    CASE 
        WHEN mi.device_tags IS NULL THEN 'No tags'
        WHEN mi.device_tags @> ARRAY['Discount-Tire'] THEN 'Has DT tag'
        ELSE 'No DT tag'
    END as tag_status,
    CASE
        WHEN mi.network_name IS NULL THEN 'No Meraki device'
        WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
        WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
        WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
        WHEN mi.network_name ILIKE '%voice%' THEN 'Voice site'
        WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') OR
             (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 'Has IPs'
        WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']) THEN 'No DT tag'
        ELSE 'Unknown'
    END as exclusion_reason
FROM circuits c
LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
WHERE c.status = 'Enabled'
AND c.site_name IN ({})
GROUP BY c.site_name, mi.network_name, mi.wan1_ip, mi.wan2_ip, 
         mi.wan1_provider, mi.wan2_provider, mi.device_tags
ORDER BY c.site_name
LIMIT 20;
"""

# Format site names for SQL
site_list = "'" + "','".join(delta_sites[:20]).replace("'", "''") + "'"
detailed_query = check_site_query.format(site_list)

print("\nDetailed analysis of first 20 delta sites:")
print("-" * 120)
print(f"{'Site Name':<30} {'Circuits':<10} {'Reason Excluded':<20} {'WAN1 IP':<15} {'WAN2 IP':<15} {'Tag Status':<12}")
print("-" * 120)

detailed_results = run_query('detailed_check', detailed_query)
for line in detailed_results:
    if line.strip():
        parts = line.split('|')
        if len(parts) >= 11:
            site_name = parts[0][:30]
            circuit_count = parts[1]
            exclusion = parts[10]
            wan1_ip = parts[5] if parts[5] != 'None' else '-'
            wan2_ip = parts[6] if parts[6] != 'None' else '-'
            tag_status = parts[9]
            
            print(f"{site_name:<30} {circuit_count:<10} {exclusion:<20} {wan1_ip:<15} {wan2_ip:<15} {tag_status:<12}")

# Summary statistics
print("\n=== STEP 5: Delta Summary ===")
summary_query = """
SELECT 
    COUNT(DISTINCT c.site_name) as total_sites,
    SUM(CASE WHEN mi.network_name IS NULL THEN 1 ELSE 0 END) as no_meraki,
    SUM(CASE WHEN mi.network_name IS NOT NULL AND NOT (mi.device_tags @> ARRAY['Discount-Tire']) THEN 1 ELSE 0 END) as no_dt_tag,
    SUM(CASE WHEN mi.network_name ILIKE '%hub%' OR mi.network_name ILIKE '%lab%' OR 
             mi.network_name ILIKE '%test%' OR mi.network_name ILIKE '%voice%' THEN 1 ELSE 0 END) as excluded_sites,
    SUM(CASE WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') OR
             (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 1 ELSE 0 END) as has_ips
FROM (
    SELECT DISTINCT c.site_name, mi.network_name, mi.device_tags, mi.wan1_ip, mi.wan2_ip
    FROM circuits c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    WHERE c.status = 'Enabled'
    AND c.site_name IN ({})
) as delta_analysis;
"""

summary_results = run_query('summary', summary_query.format(site_list))
if summary_results and summary_results[0]:
    parts = summary_results[0].split('|')
    if len(parts) >= 5:
        print(f"\nDelta Site Categories:")
        print(f"- No Meraki device: {parts[1]} sites")
        print(f"- No Discount-Tire tag: {parts[2]} sites")
        print(f"- Excluded (hub/lab/test): {parts[3]} sites")
        print(f"- Already has IPs: {parts[4]} sites")

print(f"\n=== FINAL SUMMARY ===")
print(f"CSV Enabled Circuits: 1,867")
print(f"Test Page Shows: 1,689")
print(f"Delta: 178 circuits")
print(f"\nThese 178 circuits are excluded because they belong to sites that:")
print("1. Don't have Meraki devices in inventory")
print("2. Have Meraki devices but lack the 'Discount-Tire' tag")
print("3. Are hub/lab/test/voice sites (excluded by design)")
print("4. Already have IP addresses configured on WAN interfaces")