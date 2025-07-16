#!/usr/bin/env python3
"""
Add missing columns to new_stores table
Required columns:
- Store # (store_number)
- SAP # (sap_number)
- DBA (dba)
- Address (address)
- Zip (zip)
- Store Concept (store_concept)
- Unit Capacity (unit_capacity)
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
    print("Adding missing columns to new_stores table...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # List of columns to add
        columns_to_add = [
            ("store_number", "VARCHAR(50)", "Store number identifier"),
            ("sap_number", "VARCHAR(50)", "SAP number identifier"),
            ("dba", "VARCHAR(200)", "DBA (Doing Business As) name"),
            ("address", "VARCHAR(255)", "Street address"),
            ("zip", "VARCHAR(20)", "ZIP/Postal code"),
            ("store_concept", "VARCHAR(100)", "Store concept type"),
            ("unit_capacity", "VARCHAR(50)", "Unit capacity information")
        ]
        
        # Check which columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'new_stores' 
            AND column_name IN %s
        """, (tuple([col[0] for col in columns_to_add]),))
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        for col_name, col_type, col_comment in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column: {col_name} ({col_type})")
                cursor.execute(f"""
                    ALTER TABLE new_stores 
                    ADD COLUMN {col_name} {col_type}
                """)
                
                # Add comment to describe the column
                cursor.execute(f"""
                    COMMENT ON COLUMN new_stores.{col_name} IS %s
                """, (col_comment,))
            else:
                print(f"Column already exists: {col_name}")
        
        # Commit changes
        conn.commit()
        print("\nColumns added successfully!")
        
        # Verify the new schema
        print("\nUpdated new_stores table schema:")
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'new_stores'
            ORDER BY ordinal_position
        """)
        
        print(f"\n{'Column Name':<30} {'Type':<20} {'Max Length':<10} {'Nullable':<10}")
        print("-" * 70)
        for row in cursor.fetchall():
            col_name, data_type, max_length, nullable, default = row
            type_str = data_type
            if max_length:
                type_str += f"({max_length})"
            print(f"{col_name:<30} {type_str:<20} {str(max_length or ''):<10} {nullable:<10}")
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM new_stores")
        count = cursor.fetchone()[0]
        print(f"\nTotal records in new_stores: {count}")
        
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