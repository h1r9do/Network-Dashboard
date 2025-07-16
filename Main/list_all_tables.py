#!/usr/bin/env python3
"""
List all tables in the dsrcircuits database with detailed information
"""

import psycopg2
from psycopg2.extras import RealDictCursor
# from tabulate import tabulate  # Not available in this environment
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'meraki',
    'password': 'admin',
    'port': 5432
}

def get_all_tables():
    """Get all tables in the public schema"""
    query = """
    SELECT 
        schemaname,
        tablename,
        tableowner
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute(query)
    tables = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return tables

def get_table_columns(table_name):
    """Get column information for a specific table"""
    query = """
    SELECT 
        column_name,
        data_type,
        character_maximum_length,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = %s
    ORDER BY ordinal_position;
    """
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute(query, (table_name,))
    columns = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return columns

def get_table_row_count(table_name):
    """Get row count for a specific table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Use quote_ident to handle special characters in table names
    query = f"SELECT COUNT(*) FROM {psycopg2.extensions.quote_ident(table_name, cur)}"
    
    try:
        cur.execute(query)
        count = cur.fetchone()[0]
    except Exception as e:
        count = f"Error: {str(e)}"
    
    cur.close()
    conn.close()
    
    return count

def main():
    print("=" * 80)
    print(f"DSR Circuits Database Table Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get all tables
    tables = get_all_tables()
    
    print(f"\nTotal number of tables in public schema: {len(tables)}")
    print("\n" + "=" * 80)
    print("ALL TABLES (Alphabetically)")
    print("=" * 80)
    
    # Create a list for table summary
    table_summary = []
    
    for i, table in enumerate(tables, 1):
        table_name = table['tablename']
        row_count = get_table_row_count(table_name)
        
        table_summary.append({
            'No': i,
            'Table Name': table_name,
            'Row Count': row_count,
            'Owner': table['tableowner']
        })
        
        print(f"{i:3d}. {table_name:<40} (Rows: {row_count})")
    
    # Print summary table
    print("\n" + "=" * 80)
    print("TABLE SUMMARY")
    print("=" * 80)
    print(f"{'No':<4} {'Table Name':<40} {'Row Count':<15} {'Owner':<15}")
    print("-" * 80)
    for item in table_summary:
        print(f"{item['No']:<4} {item['Table Name']:<40} {str(item['Row Count']):<15} {item['Owner']:<15}")
    
    # List of documented tables (from DATABASE_SCHEMA_DOCUMENTATION.md)
    documented_tables = [
        'circuits', 'circuit_history', 'new_stores', 'meraki_inventory',
        'firewall_rules', 'circuit_assignments', 'provider_mappings',
        'daily_summaries', 'firewall_deployment_log', 'rdap_cache',
        'enriched_circuits', 'enrichment_change_tracking', 'netdisco_devices',
        'netdisco_device_port', 'netdisco_device_ip', 'netdisco_node',
        'netdisco_node_ip', 'netdisco_node_nbt', 'netdisco_node_wireless',
        'device', 'device_ip', 'device_port', 'node', 'node_ip', 'node_nbt',
        'node_wireless', 'oui', 'sessions', 'topology', 'users', 'log',
        'admin', 'device_vlan', 'device_power', 'device_module',
        'device_port_log', 'device_route', 'device_port_vlan',
        'device_port_wireless', 'device_port_properties', 'device_port_ssid',
        'device_port_power', 'node_monitor', 'statistics'
    ]
    
    # Find undocumented tables
    all_table_names = [t['tablename'] for t in tables]
    undocumented_tables = [t for t in all_table_names if t not in documented_tables]
    
    if undocumented_tables:
        print("\n" + "=" * 80)
        print(f"UNDOCUMENTED TABLES ({len(undocumented_tables)} tables)")
        print("=" * 80)
        
        for table_name in sorted(undocumented_tables):
            print(f"\n\nTable: {table_name}")
            print("-" * 40)
            
            columns = get_table_columns(table_name)
            if columns:
                column_data = []
                for col in columns:
                    column_data.append({
                        'Column': col['column_name'],
                        'Type': col['data_type'],
                        'Max Length': col['character_maximum_length'] or '',
                        'Nullable': col['is_nullable'],
                        'Default': col['column_default'] or ''
                    })
                print(f"{'Column':<30} {'Type':<20} {'Max Length':<12} {'Nullable':<10} {'Default':<30}")
                print("-" * 102)
                for col in column_data:
                    print(f"{col['Column']:<30} {col['Type']:<20} {str(col['Max Length']):<12} {col['Nullable']:<10} {str(col['Default'])[:30]:<30}")
            else:
                print("No columns found or error accessing table structure")
    
    # Find documented tables that don't exist
    missing_tables = [t for t in documented_tables if t not in all_table_names]
    if missing_tables:
        print("\n" + "=" * 80)
        print(f"DOCUMENTED BUT MISSING TABLES ({len(missing_tables)} tables)")
        print("=" * 80)
        for table in sorted(missing_tables):
            print(f"- {table}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tables found: {len(tables)}")
    print(f"Documented tables: {len(documented_tables)}")
    print(f"Undocumented tables: {len(undocumented_tables)}")
    print(f"Missing documented tables: {len(missing_tables)}")

if __name__ == "__main__":
    main()