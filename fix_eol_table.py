#!/usr/bin/env python3
"""Fix EOL table constraints"""

import psycopg2
import re
from config import Config

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

def fix_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Drop the table and recreate with proper constraints
        cursor.execute("DROP TABLE IF EXISTS meraki_eol CASCADE")
        
        cursor.execute("""
            CREATE TABLE meraki_eol (
                id SERIAL PRIMARY KEY,
                model VARCHAR(100) NOT NULL,
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                source VARCHAR(50),
                pdf_url VARCHAR(500),
                pdf_name VARCHAR(200),
                confidence VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(model, source)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_eol_model ON meraki_eol(model)")
        cursor.execute("CREATE INDEX idx_eol_dates ON meraki_eol(end_of_sale, end_of_support)")
        
        conn.commit()
        print("✅ EOL table fixed with proper constraints")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_table()