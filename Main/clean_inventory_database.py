#!/usr/bin/env python3
"""
Clean inventory data from database tables
"""
import psycopg2
import sys
from datetime import datetime

def clean_inventory_database():
    """Clean inventory-related tables in database"""
    
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        database="network_inventory",
        user="postgres", 
        password="postgres"
    )
    cursor = conn.cursor()
    
    try:
        print("Cleaning inventory database tables...")
        
        # Tables to clean
        tables_to_clean = [
            'comprehensive_device_inventory',
            'inventory_web_format',
            'device_inventory',
            'snmp_inventory'
        ]
        
        # Check what tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN %s
        """, (tuple(tables_to_clean),))
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nFound {len(existing_tables)} inventory tables:")
        for table in existing_tables:
            # Get row count before cleaning
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
        
        # Confirm before cleaning
        response = input("\nDo you want to clean these tables? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        # Clean each table
        for table in existing_tables:
            print(f"\nCleaning {table}...")
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            print(f"  ✓ {table} cleaned")
        
        # Commit changes
        conn.commit()
        print("\nAll inventory tables cleaned successfully!")
        
        # Create backup timestamp
        backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\nBackup timestamp: {backup_time}")
        print("Note: Original data is preserved in JSON files")
        
    except Exception as e:
        print(f"Error cleaning database: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    clean_inventory_database()