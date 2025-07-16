#!/usr/bin/env python3
"""
Get complete schema information for all tables and views in the database
"""

import psycopg2
from psycopg2 import sql
import json

# Database connection
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def get_connection():
    """Create database connection"""
    return psycopg2.connect(**DATABASE_CONFIG)

def get_all_tables(conn):
    """Get all table names"""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        return [row[0] for row in cur.fetchall()]

def get_all_views(conn):
    """Get all view names"""
    query = """
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        return [row[0] for row in cur.fetchall()]

def get_table_columns(conn, table_name):
    """Get column information for a table"""
    query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (table_name,))
        columns = []
        for row in cur.fetchall():
            col_name, data_type, char_len, num_prec, num_scale, nullable, default = row
            
            # Format the data type
            if data_type in ['character varying', 'varchar']:
                type_str = f"VARCHAR({char_len})" if char_len else "VARCHAR"
            elif data_type == 'character':
                type_str = f"CHAR({char_len})" if char_len else "CHAR"
            elif data_type == 'numeric':
                if num_prec and num_scale:
                    type_str = f"NUMERIC({num_prec},{num_scale})"
                elif num_prec:
                    type_str = f"NUMERIC({num_prec})"
                else:
                    type_str = "NUMERIC"
            else:
                type_str = data_type.upper()
            
            columns.append({
                'name': col_name,
                'type': type_str,
                'nullable': nullable == 'YES',
                'default': default
            })
        
        return columns

def get_table_constraints(conn, table_name):
    """Get constraints for a table"""
    # Get primary keys
    pk_query = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass AND i.indisprimary
    """
    
    # Get foreign keys
    fk_query = """
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = %s
    """
    
    constraints = {'primary_keys': [], 'foreign_keys': []}
    
    with conn.cursor() as cur:
        # Get primary keys
        try:
            cur.execute(pk_query, (table_name,))
            constraints['primary_keys'] = [row[0] for row in cur.fetchall()]
        except:
            pass
        
        # Get foreign keys
        try:
            cur.execute(fk_query, (table_name,))
            for row in cur.fetchall():
                constraints['foreign_keys'].append({
                    'column': row[0],
                    'references_table': row[1],
                    'references_column': row[2],
                    'constraint_name': row[3]
                })
        except:
            pass
    
    return constraints

def get_table_row_count(conn, table_name):
    """Get row count for a table"""
    try:
        with conn.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            return cur.fetchone()[0]
    except:
        return "Error"

def get_view_definition(conn, view_name):
    """Get the SQL definition of a view"""
    query = "SELECT pg_get_viewdef(%s, true)"
    
    with conn.cursor() as cur:
        cur.execute(query, (view_name,))
        result = cur.fetchone()
        return result[0] if result else None

def print_table_schema(table_name, columns, constraints, row_count):
    """Pretty print table schema"""
    print(f"\n--- {table_name} ({row_count} rows) ---")
    print("Columns:")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"  {col['name']}: {col['type']} {nullable}{default}")
    
    if constraints['primary_keys']:
        print(f"Primary Key: {', '.join(constraints['primary_keys'])}")
    
    if constraints['foreign_keys']:
        print("Foreign Keys:")
        for fk in constraints['foreign_keys']:
            print(f"  {fk['constraint_name']}: {fk['column']} -> {fk['references_table']}({fk['references_column']})")

def main():
    conn = get_connection()
    
    try:
        # Get all tables and views
        tables = get_all_tables(conn)
        views = get_all_views(conn)
        
        print(f"Total tables: {len(tables)}")
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
        
        # Sort tables by category
        collected_tables = [t for t in tables if t.startswith('collected_')]
        device_tables = [t for t in tables if t.startswith('device_') and t not in priority_tables]
        network_tables = [t for t in tables if t.startswith('network_')]
        snmp_tables = [t for t in tables if t.startswith('snmp_')]
        other_tables = [t for t in tables if t not in collected_tables + device_tables + network_tables + snmp_tables + priority_tables]
        
        print("\n=== PRIORITY TABLES (with significant data) ===")
        for table in priority_tables:
            if table in tables:
                row_count = get_table_row_count(conn, table)
                columns = get_table_columns(conn, table)
                constraints = get_table_constraints(conn, table)
                print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== COLLECTED_* TABLES ===")
        for table in sorted(collected_tables):
            row_count = get_table_row_count(conn, table)
            columns = get_table_columns(conn, table)
            constraints = get_table_constraints(conn, table)
            print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== DEVICE_* TABLES ===")
        for table in sorted(device_tables):
            row_count = get_table_row_count(conn, table)
            columns = get_table_columns(conn, table)
            constraints = get_table_constraints(conn, table)
            print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== NETWORK_* TABLES ===")
        for table in sorted(network_tables):
            row_count = get_table_row_count(conn, table)
            columns = get_table_columns(conn, table)
            constraints = get_table_constraints(conn, table)
            print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== SNMP_* TABLES ===")
        for table in sorted(snmp_tables):
            row_count = get_table_row_count(conn, table)
            columns = get_table_columns(conn, table)
            constraints = get_table_constraints(conn, table)
            print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== OTHER TABLES ===")
        for table in sorted(other_tables):
            row_count = get_table_row_count(conn, table)
            columns = get_table_columns(conn, table)
            constraints = get_table_constraints(conn, table)
            print_table_schema(table, columns, constraints, row_count)
        
        print("\n=== VIEWS ===")
        for view in sorted(views):
            print(f"\n--- VIEW: {view} ---")
            definition = get_view_definition(conn, view)
            if definition:
                print("Definition:")
                print(definition)
            else:
                print("Could not retrieve view definition")
    
    finally:
        conn.close()

if __name__ == '__main__':
    main()