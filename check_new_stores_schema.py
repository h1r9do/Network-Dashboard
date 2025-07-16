#!/usr/bin/env python3
"""
Check the schema of the new_stores table
"""

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def check_new_stores_schema():
    """Query the schema of new_stores table"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Query to get column information
        query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM 
            information_schema.columns
        WHERE 
            table_schema = 'public' 
            AND table_name = 'new_stores'
        ORDER BY 
            ordinal_position;
        """
        
        cur.execute(query)
        columns = cur.fetchall()
        
        # Format the results
        print("\nCurrent schema of new_stores table:")
        print("=" * 80)
        print(f"{'Column Name':<30} {'Data Type':<20} {'Max Length':<12} {'Nullable':<10} {'Default':<30}")
        print("-" * 102)
        for col in columns:
            col_name, data_type, max_len, nullable, default = col
            max_len_str = str(max_len) if max_len else 'N/A'
            default_str = str(default) if default else 'None'
            print(f"{col_name:<30} {data_type:<20} {max_len_str:<12} {nullable:<10} {default_str:<30}")
        
        # Also get constraints
        constraint_query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM 
            information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
        WHERE 
            tc.table_schema = 'public'
            AND tc.table_name = 'new_stores'
        ORDER BY 
            tc.constraint_type, tc.constraint_name;
        """
        
        cur.execute(constraint_query)
        constraints = cur.fetchall()
        
        if constraints:
            print("\nTable Constraints:")
            print("=" * 80)
            print(f"{'Constraint Name':<40} {'Type':<20} {'Column':<20}")
            print("-" * 80)
            for constraint in constraints:
                const_name, const_type, col_name = constraint
                print(f"{const_name:<40} {const_type:<20} {col_name:<20}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_new_stores_schema()