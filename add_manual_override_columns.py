#!/usr/bin/env python3
"""
Database migration script to add manual_override columns to circuits table
This allows marking circuits that were manually added/edited so they won't be overwritten by DSR pull
"""

import psycopg2
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

def get_db_connection():
    """Get database connection using config"""
    import re
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

def add_manual_override_columns():
    """Add manual override columns to circuits table"""
    conn = None
    cursor = None
    
    try:
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circuits' 
            AND column_name IN ('manual_override', 'manual_override_date', 'manual_override_by')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if 'manual_override' not in existing_columns:
            print("Adding manual_override column...")
            cursor.execute("""
                ALTER TABLE circuits 
                ADD COLUMN manual_override BOOLEAN DEFAULT FALSE
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX idx_circuits_manual_override 
                ON circuits(manual_override)
            """)
            print("✓ Added manual_override column")
        else:
            print("✓ manual_override column already exists")
            
        if 'manual_override_date' not in existing_columns:
            print("Adding manual_override_date column...")
            cursor.execute("""
                ALTER TABLE circuits 
                ADD COLUMN manual_override_date TIMESTAMP
            """)
            print("✓ Added manual_override_date column")
        else:
            print("✓ manual_override_date column already exists")
            
        if 'manual_override_by' not in existing_columns:
            print("Adding manual_override_by column...")
            cursor.execute("""
                ALTER TABLE circuits 
                ADD COLUMN manual_override_by VARCHAR(100)
            """)
            print("✓ Added manual_override_by column")
        else:
            print("✓ manual_override_by column already exists")
        
        # Commit changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
        # Show current schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'circuits'
            AND column_name LIKE 'manual_override%'
            ORDER BY ordinal_position
        """)
        
        print("\nManual override columns in circuits table:")
        for col_name, data_type, nullable in cursor.fetchall():
            print(f"  - {col_name}: {data_type} (nullable: {nullable})")
            
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        if conn:
            conn.rollback()
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("DSR Circuits - Add Manual Override Columns Migration")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        add_manual_override_columns()
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)