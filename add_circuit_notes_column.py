#!/usr/bin/env python3
"""
Add notes column to circuits table
"""

import psycopg2
from config import Config
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_notes_column():
    """Add notes column to circuits table if it doesn't exist"""
    
    # Parse database URI
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    # Connect to database
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circuits' 
            AND column_name = 'notes'
        """)
        
        if cursor.fetchone():
            logger.info("Notes column already exists in circuits table")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE circuits 
                ADD COLUMN notes TEXT
            """)
            conn.commit()
            logger.info("Successfully added notes column to circuits table")
            
    except Exception as e:
        logger.error(f"Error adding notes column: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_notes_column()