#!/usr/bin/env python3
"""
Fix missing circuits by comparing CSV (source of truth) with database
and importing any missing enabled circuits
"""

import csv
import subprocess
import os
from datetime import datetime

def get_latest_csv():
    """Find the latest tracking CSV file"""
    csv_files = []
    for file in os.listdir('/var/www/html/circuitinfo/'):
        if file.startswith('tracking_data_') and file.endswith('.csv'):
            csv_files.append(file)
    
    latest_file = sorted(csv_files)[-1]
    return f'/var/www/html/circuitinfo/{latest_file}'

def get_enabled_circuits_from_csv(csv_path):
    """Get all enabled circuits from CSV"""
    enabled_circuits = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            record_number = row.get('record_number', '').strip()
            status = row.get('status', '').strip()
            
            if status.lower() == 'enabled' and record_number:
                enabled_circuits[record_number] = {
                    'record_number': record_number,
                    'site_name': row.get('Site Name', ''),
                    'site_id': row.get('Site ID', ''),
                    'circuit_purpose': row.get('Circuit Purpose', ''),
                    'status': status,
                    'provider_name': row.get('Provider Name', ''),
                    'details_service_speed': row.get('details_service_speed', ''),
                    'details_ordered_service_speed': row.get('Details Ordered Service Speed', ''),
                    'billing_monthly_cost': row.get('Billing Monthly Cost', ''),
                    'ip_address_start': row.get('IP Address Start', ''),
                    'assigned_to': row.get('Assigned To', ''),
                    'sctask': row.get('SCTASK', ''),
                    'milestone_enabled': row.get('Milestone Enabled', ''),
                    'date_record_updated': row.get('Date Record Updated', '')
                }
    
    return enabled_circuits

def get_enabled_circuits_from_db():
    """Get all enabled circuits from database"""
    query = "SELECT record_number FROM circuits WHERE status = 'Enabled';"
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-c', query],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        records = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return set(records)
    else:
        print(f"Error querying database: {result.stderr}")
        return set()

def sql_value(value):
    """Convert value to SQL format"""
    if not value or value == 'Unknown':
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"

def sql_date(date_value):
    """Convert date to SQL format"""
    if not date_value or date_value == 'Unknown' or date_value == '0000-00-00':
        return 'NULL'
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_value, fmt)
                return "'" + dt.strftime('%Y-%m-%d') + "'"
            except ValueError:
                continue
        return 'NULL'
    except:
        return 'NULL'

def sql_number(value):
    """Convert number to SQL format"""
    if not value or value == '':
        return 'NULL'
    try:
        return str(float(value))
    except:
        return 'NULL'

def main():
    print("=== FIXING MISSING CIRCUITS FROM CSV ===\n")
    
    # Get latest CSV file
    csv_path = get_latest_csv()
    print(f"Using CSV file: {csv_path}")
    
    # Get enabled circuits from CSV
    print("Reading enabled circuits from CSV...")
    csv_circuits = get_enabled_circuits_from_csv(csv_path)
    print(f"Found {len(csv_circuits)} enabled circuits in CSV")
    
    # Get enabled circuits from database
    print("\nReading enabled circuits from database...")
    db_records = get_enabled_circuits_from_db()
    print(f"Found {len(db_records)} enabled circuits in database")
    
    # Find missing circuits
    missing_records = set(csv_circuits.keys()) - db_records
    print(f"\n⚠️  Found {len(missing_records)} missing circuits that need to be imported")
    
    if missing_records:
        # Group missing circuits by site
        missing_by_site = {}
        for record in missing_records:
            circuit = csv_circuits[record]
            site_name = circuit['site_name']
            if site_name not in missing_by_site:
                missing_by_site[site_name] = []
            missing_by_site[site_name].append(circuit)
        
        # Show missing circuits
        print("\nMissing circuits by site:")
        for site_name in sorted(missing_by_site.keys()):
            circuits = missing_by_site[site_name]
            print(f"\n  {site_name}: {len(circuits)} missing circuit(s)")
            for circuit in circuits:
                print(f"    - {circuit['record_number']} | Site ID: {circuit['site_id']} | {circuit['circuit_purpose']}")
        
        # Generate SQL to insert missing circuits
        print("\n📝 Generating SQL to insert missing circuits...")
        sql_lines = ["BEGIN;", ""]
        
        for record in missing_records:
            circuit = csv_circuits[record]
            
            sql = f"""INSERT INTO circuits (
    record_number, site_name, site_id, circuit_purpose, status,
    provider_name, details_service_speed, details_ordered_service_speed,
    billing_monthly_cost, ip_address_start, assigned_to, sctask,
    milestone_enabled, date_record_updated,
    created_at, updated_at, data_source
) VALUES (
    {sql_value(circuit['record_number'])},
    {sql_value(circuit['site_name'])},
    {sql_value(circuit['site_id'])},
    {sql_value(circuit['circuit_purpose'])},
    {sql_value(circuit['status'])},
    {sql_value(circuit['provider_name'])},
    {sql_value(circuit['details_service_speed'])},
    {sql_value(circuit['details_ordered_service_speed'])},
    {sql_number(circuit['billing_monthly_cost'])},
    {sql_value(circuit['ip_address_start'])},
    {sql_value(circuit['assigned_to'])},
    {sql_value(circuit['sctask'])},
    {sql_date(circuit['milestone_enabled'])},
    {sql_date(circuit['date_record_updated'])},
    NOW(), NOW(), 'csv_import_fix'
);"""
            sql_lines.append(sql)
        
        sql_lines.append("")
        sql_lines.append("COMMIT;")
        
        # Write SQL file
        sql_file = '/tmp/fix_missing_circuits.sql'
        with open(sql_file, 'w') as f:
            f.write('\n'.join(sql_lines))
        
        print(f"\n✅ SQL file written to: {sql_file}")
        
        # Ask for confirmation
        print("\n" + "="*60)
        print("Ready to import missing circuits to database")
        print("This will add the missing enabled circuits to match the CSV")
        response = input("\nProceed with import? (yes/no): ")
        
        if response.lower() == 'yes':
            print("\n🚀 Executing database import...")
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-f', sql_file],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Import completed successfully!")
                
                # Verify the import
                print("\nVerifying sites with >2 circuits:")
                verify_query = """
                SELECT site_name, COUNT(*) as circuit_count 
                FROM circuits 
                WHERE status = 'Enabled' 
                GROUP BY site_name 
                HAVING COUNT(*) > 2 
                ORDER BY COUNT(*) DESC, site_name;
                """
                result = subprocess.run(
                    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-c', verify_query],
                    capture_output=True, text=True
                )
                print(result.stdout)
            else:
                print(f"❌ Import failed: {result.stderr}")
        else:
            print("\nImport cancelled. SQL file saved at: " + sql_file)
    else:
        print("\n✅ No missing circuits found. Database matches CSV!")

if __name__ == "__main__":
    main()