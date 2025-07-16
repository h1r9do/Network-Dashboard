#!/usr/bin/env python3
"""
Update comprehensive_device_inventory table structure for enhanced data
"""
import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_connection

def update_table_structure():
    """Ensure table has proper structure for enhanced inventory data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comprehensive_device_inventory (
                id SERIAL PRIMARY KEY,
                device_name VARCHAR(255) UNIQUE NOT NULL,
                ip_address INET NOT NULL,
                entity_data JSONB,
                physical_inventory JSONB,
                summary JSONB,
                collection_timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_inventory_device_name 
            ON comprehensive_device_inventory(device_name);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_inventory_collection_time 
            ON comprehensive_device_inventory(collection_timestamp);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_inventory_physical_gin 
            ON comprehensive_device_inventory USING gin(physical_inventory);
        """)
        
        # Add trigger to update updated_at timestamp
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_comprehensive_device_inventory_updated_at 
            ON comprehensive_device_inventory;
        """)
        
        cursor.execute("""
            CREATE TRIGGER update_comprehensive_device_inventory_updated_at 
            BEFORE UPDATE ON comprehensive_device_inventory 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        conn.commit()
        print("Table structure updated successfully")
        
        # Show current table info
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'comprehensive_device_inventory'
            ORDER BY ordinal_position;
        """)
        
        print("\nTable columns:")
        for col in cursor.fetchall():
            print(f"  {col[0]}: {col[1]}")
            
    except Exception as e:
        print(f"Error updating table structure: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_table_structure()