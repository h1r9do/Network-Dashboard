#!/usr/bin/env python3
"""
Get complete schema information for all tables and views in the database
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool
import json

# Database connection
DATABASE_URI = 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits'

def get_table_schema(inspector, table_name):
    """Get detailed schema for a single table"""
    schema = {
        'name': table_name,
        'columns': [],
        'primary_keys': [],
        'foreign_keys': [],
        'indexes': []
    }
    
    # Get columns
    for col in inspector.get_columns(table_name):
        column_info = {
            'name': col['name'],
            'type': str(col['type']),
            'nullable': col['nullable'],
            'default': str(col['default']) if col['default'] else None,
            'autoincrement': col.get('autoincrement', False)
        }
        schema['columns'].append(column_info)
    
    # Get primary keys
    pk_constraint = inspector.get_pk_constraint(table_name)
    if pk_constraint:
        schema['primary_keys'] = pk_constraint['constrained_columns']
    
    # Get foreign keys
    for fk in inspector.get_foreign_keys(table_name):
        fk_info = {
            'name': fk['name'],
            'constrained_columns': fk['constrained_columns'],
            'referred_table': fk['referred_table'],
            'referred_columns': fk['referred_columns']
        }
        schema['foreign_keys'].append(fk_info)
    
    # Get indexes
    for idx in inspector.get_indexes(table_name):
        idx_info = {
            'name': idx['name'],
            'columns': idx['column_names'],
            'unique': idx['unique']
        }
        schema['indexes'].append(idx_info)
    
    return schema

def get_view_definition(engine, view_name):
    """Get the SQL definition of a view"""
    query = text("""
        SELECT pg_get_viewdef(:view_name, true) as definition
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {'view_name': view_name})
        row = result.fetchone()
        return row[0] if row else None

def main():
    engine = create_engine(DATABASE_URI, poolclass=NullPool)
    inspector = inspect(engine)
    
    # Get all table names
    tables = inspector.get_table_names()
    print(f"Total tables: {len(tables)}")
    
    # Get all view names
    query = text("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        views = [row[0] for row in result]
    
    print(f"Total views: {len(views)}")
    
    # Priority tables with significant data
    priority_tables = [
        'comprehensive_device_inventory',
        'corporate_eol',
        'datacenter_inventory',
        'device_access',
        'device_components',
        'ip_assignment_history'
    ]
    
    # Get row counts for all tables
    table_row_counts = {}
    with engine.connect() as conn:
        for table in tables:
            try:
                count_query = text(f'SELECT COUNT(*) FROM "{table}"')
                result = conn.execute(count_query)
                count = result.scalar()
                table_row_counts[table] = count
            except Exception as e:
                table_row_counts[table] = f"Error: {str(e)}"
    
    # Sort tables by category
    collected_tables = [t for t in tables if t.startswith('collected_')]
    device_tables = [t for t in tables if t.startswith('device_') and t not in priority_tables]
    network_tables = [t for t in tables if t.startswith('network_')]
    snmp_tables = [t for t in tables if t.startswith('snmp_')]
    other_tables = [t for t in tables if t not in collected_tables + device_tables + network_tables + snmp_tables + priority_tables]
    
    print("\n=== PRIORITY TABLES (with significant data) ===")
    for table in priority_tables:
        if table in tables:
            print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
            schema = get_table_schema(inspector, table)
            print_table_schema(schema)
    
    print("\n=== COLLECTED_* TABLES ===")
    for table in sorted(collected_tables):
        print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
        schema = get_table_schema(inspector, table)
        print_table_schema(schema)
    
    print("\n=== DEVICE_* TABLES (excluding priority) ===")
    for table in sorted(device_tables):
        print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
        schema = get_table_schema(inspector, table)
        print_table_schema(schema)
    
    print("\n=== NETWORK_* TABLES ===")
    for table in sorted(network_tables):
        print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
        schema = get_table_schema(inspector, table)
        print_table_schema(schema)
    
    print("\n=== SNMP_* TABLES ===")
    for table in sorted(snmp_tables):
        print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
        schema = get_table_schema(inspector, table)
        print_table_schema(schema)
    
    print("\n=== OTHER TABLES ===")
    for table in sorted(other_tables):
        print(f"\n--- {table} ({table_row_counts.get(table, 'Unknown')} rows) ---")
        schema = get_table_schema(inspector, table)
        print_table_schema(schema)
    
    print("\n=== VIEWS ===")
    for view in sorted(views):
        print(f"\n--- VIEW: {view} ---")
        definition = get_view_definition(engine, view)
        if definition:
            print("Definition:")
            print(definition)
        else:
            print("Could not retrieve view definition")

def print_table_schema(schema):
    """Pretty print table schema"""
    print("Columns:")
    for col in schema['columns']:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        auto = " AUTO_INCREMENT" if col['autoincrement'] else ""
        print(f"  {col['name']}: {col['type']} {nullable}{default}{auto}")
    
    if schema['primary_keys']:
        print(f"Primary Key: {', '.join(schema['primary_keys'])}")
    
    if schema['foreign_keys']:
        print("Foreign Keys:")
        for fk in schema['foreign_keys']:
            print(f"  {fk['name']}: {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}({', '.join(fk['referred_columns'])})")
    
    if schema['indexes']:
        print("Indexes:")
        for idx in schema['indexes']:
            unique = "UNIQUE " if idx['unique'] else ""
            print(f"  {idx['name']}: {unique}({', '.join(idx['columns'])})")

if __name__ == '__main__':
    main()