#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import Config

# Test database connection
try:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT network_name FROM enriched_circuits WHERE network_name = 'AZC 01'"))
        row = result.fetchone()
        if row:
            print(f"✅ Found AZC 01: {row[0]}")
        else:
            print("❌ AZC 01 not found in enriched_circuits")
            
        # Test a simple update
        print("Testing database update...")
        conn.execute(text("UPDATE enriched_circuits SET last_updated = CURRENT_TIMESTAMP WHERE network_name = 'AZC 01'"))
        conn.commit()
        print("✅ Database update successful")
        
except Exception as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()