#!/usr/bin/env python3
"""
Full update of circuits from CSV - working version
"""

import os
import subprocess
import pandas as pd
import re
from datetime import datetime

def normalize_speed(speed_value):
    """Normalize speed values (convert G to M if needed)"""
    if pd.isna(speed_value) or speed_value == '':
        return 'NULL'
    
    speed_str = str(speed_value)
    # Convert G to M
    if 'G' in speed_str:
        match = re.search(r'(\d+(?:\.\d+)?)G', speed_str)
        if match:
            gb_value = float(match.group(1))
            mb_value = gb_value * 1000
            speed_str = speed_str.replace(match.group(0), f"{mb_value:.0f}M")
    
    return "'" + speed_str + "'"

def sql_value(value):
    """Convert value to SQL format"""
    if pd.isna(value) or value == '' or value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"

def sql_date(date_value):
    """Convert date to SQL format"""
    if pd.isna(date_value) or date_value == '' or str(date_value) == '0000-00-00':
        return 'NULL'
    
    date_str = str(date_value)
    if date_str.startswith('0000-'):
        return 'NULL'
    
    try:
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return "'" + dt.strftime('%Y-%m-%d %H:%M:%S') + "'"
            except ValueError:
                continue
        return 'NULL'
    except:
        return 'NULL'

def sql_number(value):
    """Convert number to SQL format"""
    if pd.isna(value) or value == '':
        return 'NULL'
    try:
        return str(float(value))
    except:
        return 'NULL'

# Get CSV file from command line or default
import sys
csv_file = sys.argv[1] if len(sys.argv) > 1 else "/var/www/html/circuitinfo/tracking_data_2025-07-05.csv"

# Read CSV
print("Reading CSV file...")
df = pd.read_csv(csv_file, low_memory=False)
df.columns = df.columns.str.lower().str.replace(' ', '_')
print(f"Found {len(df)} records")

# Generate SQL
print("Generating SQL updates...")
sql_lines = []
sql_lines.append("BEGIN;")
sql_lines.append("")
sql_lines.append("-- Update fingerprints")
sql_lines.append("UPDATE circuits SET fingerprint = site_name || '|' || site_id || '|' || circuit_purpose WHERE fingerprint IS NULL OR fingerprint = '';")
sql_lines.append("")

# Track unique records
seen_records = set()
count = 0

for _, row in df.iterrows():
    record_num = row.get('record_number')
    if pd.isna(record_num) or not record_num or record_num in seen_records:
        continue
    seen_records.add(record_num)
    
    # Create SQL for this record
    sql = f"""INSERT INTO circuits (
    record_number, site_name, site_id, circuit_purpose, status, substatus,
    provider_name, details_service_speed, details_ordered_service_speed,
    billing_monthly_cost, ip_address_start, date_record_updated,
    milestone_service_activated, milestone_enabled, assigned_to, sctask,
    created_at, updated_at, data_source, address_1, city, state, zipcode,
    primary_contact_name, primary_contact_email, billing_install_cost,
    target_enablement_date, details_provider, details_provider_phone,
    billing_account, fingerprint, last_csv_file
) VALUES (
    {sql_value(record_num)}, {sql_value(row.get('site_name'))}, {sql_value(row.get('site_id'))},
    {sql_value(row.get('circuit_purpose'))}, {sql_value(row.get('status'))}, {sql_value(row.get('substatus'))},
    {sql_value(row.get('provider_name'))}, {normalize_speed(row.get('details_service_speed'))},
    {normalize_speed(row.get('details_ordered_service_speed'))}, {sql_number(row.get('billing_monthly_cost'))},
    {sql_value(row.get('ip_address_start'))}, {sql_date(row.get('date_record_updated'))},
    {sql_date(row.get('milestone_service_activated'))}, {sql_date(row.get('milestone_enabled'))},
    {sql_value(row.get('assigned_to'))}, {sql_value(row.get('sctask'))},
    NOW(), NOW(), 'csv_import',
    {sql_value(row.get('address_1'))}, {sql_value(row.get('city'))}, {sql_value(row.get('state'))},
    {sql_value(row.get('zipcode'))}, {sql_value(row.get('primary_contact_name'))},
    {sql_value(row.get('primary_contact_email'))}, {sql_number(row.get('billing_install_cost'))},
    {sql_date(row.get('target_enablement_date'))}, {sql_value(row.get('details_provider'))},
    {sql_value(row.get('details_provider_phone'))}, {sql_value(row.get('billing_account'))},
    {sql_value(str(row.get('site_name', '')) + '|' + str(row.get('site_id', '')) + '|' + str(row.get('circuit_purpose', '')))},
    '" + os.path.basename(csv_file) + "'
)
ON CONFLICT (record_number) DO UPDATE SET
    site_name = EXCLUDED.site_name,
    site_id = EXCLUDED.site_id,
    circuit_purpose = EXCLUDED.circuit_purpose,
    status = EXCLUDED.status,
    substatus = EXCLUDED.substatus,
    provider_name = EXCLUDED.provider_name,
    details_service_speed = EXCLUDED.details_service_speed,
    details_ordered_service_speed = EXCLUDED.details_ordered_service_speed,
    billing_monthly_cost = EXCLUDED.billing_monthly_cost,
    ip_address_start = EXCLUDED.ip_address_start,
    date_record_updated = EXCLUDED.date_record_updated,
    milestone_service_activated = EXCLUDED.milestone_service_activated,
    milestone_enabled = EXCLUDED.milestone_enabled,
    assigned_to = COALESCE(circuits.assigned_to, EXCLUDED.assigned_to),
    sctask = COALESCE(circuits.sctask, EXCLUDED.sctask),
    address_1 = EXCLUDED.address_1,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    zipcode = EXCLUDED.zipcode,
    primary_contact_name = EXCLUDED.primary_contact_name,
    primary_contact_email = EXCLUDED.primary_contact_email,
    billing_install_cost = EXCLUDED.billing_install_cost,
    target_enablement_date = EXCLUDED.target_enablement_date,
    details_provider = EXCLUDED.details_provider,
    details_provider_phone = EXCLUDED.details_provider_phone,
    billing_account = EXCLUDED.billing_account,
    fingerprint = EXCLUDED.fingerprint,
    last_csv_file = EXCLUDED.last_csv_file,
    data_source = EXCLUDED.data_source,
    updated_at = NOW()
WHERE circuits.manual_override IS NOT TRUE;"""
    
    sql_lines.append(sql)
    count += 1
    
    if count % 500 == 0:
        print(f"Processed {count} records...")

# Add cleanup and summary update
sql_lines.append("")
sql_lines.append("-- Clear notes for enabled/cancelled circuits")
sql_lines.append("UPDATE circuits SET notes = NULL WHERE (status ILIKE '%enabled%' OR status ILIKE '%cancelled%' OR status ILIKE '%canceled%') AND notes IS NOT NULL;")
sql_lines.append("")
sql_lines.append("-- Update daily summary")
sql_lines.append("""INSERT INTO daily_summaries (
    summary_date, total_circuits, enabled_count, ready_count,
    customer_action_count, construction_count, planning_count,
    csv_file_processed, processing_time_seconds, created_at
)
SELECT
    CURRENT_DATE as summary_date,
    COUNT(*) as total_circuits,
    COUNT(*) FILTER (WHERE status ILIKE '%enabled%' OR status ILIKE '%activated%') as enabled_count,
    COUNT(*) FILTER (WHERE status ILIKE '%ready%') as ready_count,
    COUNT(*) FILTER (WHERE status ILIKE '%customer action%') as customer_action_count,
    COUNT(*) FILTER (WHERE status ILIKE '%construction%') as construction_count,
    COUNT(*) FILTER (WHERE status ILIKE '%planning%') as planning_count,
    '" + os.path.basename(csv_file) + "' as csv_file_processed,
    0 as processing_time_seconds,
    NOW() as created_at
FROM circuits
ON CONFLICT (summary_date) DO UPDATE SET
    total_circuits = EXCLUDED.total_circuits,
    enabled_count = EXCLUDED.enabled_count,
    ready_count = EXCLUDED.ready_count,
    customer_action_count = EXCLUDED.customer_action_count,
    construction_count = EXCLUDED.construction_count,
    planning_count = EXCLUDED.planning_count,
    csv_file_processed = EXCLUDED.csv_file_processed,
    processing_time_seconds = EXCLUDED.processing_time_seconds,
    created_at = NOW();""")

sql_lines.append("")
sql_lines.append("COMMIT;")

# Write SQL file
sql_file = '/tmp/full_circuit_update.sql'
print(f"Writing SQL file with {len(seen_records)} unique records...")
with open(sql_file, 'w') as f:
    f.write('\n'.join(sql_lines))

# Execute SQL
print("Executing database update...")
result = subprocess.run(['psql', '-U', 'dsruser', '-d', 'dsrcircuits', '-f', sql_file], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("Update completed successfully!")
    
    # Get stats
    cmd = "SELECT COUNT(*) as total, COUNT(CASE WHEN DATE(updated_at) = CURRENT_DATE THEN 1 END) as updated_today FROM circuits;"
    result = subprocess.run(['psql', '-U', 'dsruser', '-d', 'dsrcircuits', '-t', '-c', cmd],
                           capture_output=True, text=True)
    if result.returncode == 0:
        stats = result.stdout.strip()
        print(f"Database stats: {stats}")
else:
    print(f"Error: {result.stderr}")
    exit(1)