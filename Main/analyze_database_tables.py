#!/usr/bin/env python3
"""
Analyze all tables in dsrcircuits database and identify undocumented ones
"""

import subprocess
import sys
from datetime import datetime

# Tables documented in CLAUDE.md (from the Primary Tables section)
DOCUMENTED_IN_CLAUDE = [
    'circuits', 'circuit_history', 'new_stores', 'meraki_inventory',
    'firewall_rules', 'circuit_assignments', 'provider_mappings',
    'daily_summaries', 'firewall_deployment_log', 'rdap_cache',
    'enriched_circuits', 'enrichment_change_tracking'
]

def run_psql_query(query):
    """Run a PostgreSQL query using sudo"""
    cmd = ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-c', query]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running query: {result.stderr}")
        return None
    return result.stdout

def get_table_columns(table_name):
    """Get column information for a table"""
    query = f"""
    SELECT 
        column_name || ' | ' || 
        data_type || 
        CASE 
            WHEN character_maximum_length IS NOT NULL THEN '(' || character_maximum_length || ')'
            ELSE ''
        END || ' | ' ||
        CASE 
            WHEN is_nullable = 'YES' THEN 'NULL'
            ELSE 'NOT NULL'
        END || ' | ' ||
        COALESCE(column_default, '')
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    result = run_psql_query(query)
    if result:
        return [line.strip() for line in result.strip().split('\n') if line.strip()]
    return []

def get_row_count(table_name):
    """Get row count for a table"""
    query = f"SELECT COUNT(*) FROM {table_name};"
    result = run_psql_query(query)
    if result:
        return result.strip()
    return "Error"

def main():
    print("=" * 80)
    print(f"DSR Circuits Database Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Read all tables from the file we created
    with open('/tmp/all_tables.txt', 'r') as f:
        all_tables = [line.strip() for line in f if line.strip()]
    
    print(f"\nTotal tables in database: {len(all_tables)}")
    
    # Categorize tables
    documented_tables = [t for t in all_tables if t in DOCUMENTED_IN_CLAUDE]
    undocumented_tables = [t for t in all_tables if t not in DOCUMENTED_IN_CLAUDE]
    
    print(f"Documented in CLAUDE.md: {len(documented_tables)}")
    print(f"Undocumented tables: {len(undocumented_tables)}")
    
    print("\n" + "=" * 80)
    print("DOCUMENTED TABLES (from CLAUDE.md)")
    print("=" * 80)
    for i, table in enumerate(documented_tables, 1):
        count = get_row_count(table)
        print(f"{i:2d}. {table:<40} Rows: {count}")
    
    print("\n" + "=" * 80)
    print(f"UNDOCUMENTED TABLES ({len(undocumented_tables)} tables)")
    print("=" * 80)
    
    # Group undocumented tables by category
    categories = {
        'EOL Related': [],
        'Inventory Related': [],
        'Network/Device Related': [],
        'Performance/Monitoring': [],
        'Enablement Related': [],
        'SNMP Related': [],
        'Backup Tables': [],
        'Other': []
    }
    
    for table in undocumented_tables:
        if 'eol' in table.lower():
            categories['EOL Related'].append(table)
        elif 'inventory' in table.lower() or 'collected' in table.lower():
            categories['Inventory Related'].append(table)
        elif 'network' in table.lower() or 'device' in table.lower() or 'port' in table.lower():
            categories['Network/Device Related'].append(table)
        elif 'performance' in table.lower() or 'metrics' in table.lower() or 'api' in table.lower():
            categories['Performance/Monitoring'].append(table)
        elif 'enablement' in table.lower() or 'enable' in table.lower():
            categories['Enablement Related'].append(table)
        elif 'snmp' in table.lower():
            categories['SNMP Related'].append(table)
        elif 'backup' in table.lower():
            categories['Backup Tables'].append(table)
        else:
            categories['Other'].append(table)
    
    # Print categorized tables
    for category, tables in categories.items():
        if tables:
            print(f"\n{category} ({len(tables)} tables):")
            print("-" * 50)
            for table in sorted(tables):
                count = get_row_count(table)
                print(f"  {table:<40} Rows: {count}")
    
    # Get detailed schema for specific new/important tables
    important_new_tables = [
        'api_performance',
        'circuit_enablements',
        'daily_enablements',
        'enablement_summary',
        'comprehensive_device_inventory',
        'eol_tracker_state',
        'performance_metrics'
    ]
    
    print("\n" + "=" * 80)
    print("DETAILED SCHEMA FOR KEY UNDOCUMENTED TABLES")
    print("=" * 80)
    
    for table in important_new_tables:
        if table in all_tables:
            print(f"\nTable: {table}")
            print("-" * 50)
            columns = get_table_columns(table)
            if columns:
                print("Column | Type | Nullable | Default")
                print("-" * 50)
                for col in columns:
                    print(col)
            else:
                print("Could not retrieve column information")

if __name__ == "__main__":
    main()