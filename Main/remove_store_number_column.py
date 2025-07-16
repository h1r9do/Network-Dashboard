#!/usr/bin/env python3
"""
Remove the redundant store_number column from new_stores table
since site_name already serves this purpose
"""

import psycopg2
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
import re

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def main():
    print("Removing redundant store_number column from new_stores table...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'new_stores' 
            AND column_name = 'store_number'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("Found store_number column, removing it...")
            cursor.execute("ALTER TABLE new_stores DROP COLUMN store_number")
            conn.commit()
            print("✓ Column removed successfully")
        else:
            print("✓ Column store_number not found (already removed)")
        
        # Verify final schema
        print("\nFinal new_stores table schema:")
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'new_stores'
            ORDER BY ordinal_position
        """)
        
        print(f"\n{'Column Name':<30} {'Type':<20} {'Max Length':<10} {'Nullable':<10}")
        print("-" * 70)
        for row in cursor.fetchall():
            col_name, data_type, max_length, nullable = row
            type_str = data_type
            if max_length:
                type_str += f"({max_length})"
            print(f"{col_name:<30} {type_str:<20} {str(max_length or ''):<10} {nullable:<10}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())