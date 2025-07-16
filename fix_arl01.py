#!/usr/bin/env python3
"""
Fix ARL 01 enriched data to match ARIN/DSR data
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

print("Fixing ARL 01 enriched data...")

# Update WAN1 to match ARIN data (AT&T)
session.execute(text("""
    UPDATE enriched_circuits
    SET wan1_provider = 'AT&T',
        wan1_speed = '1000.0M x 1000.0M',
        last_updated = CURRENT_TIMESTAMP
    WHERE LOWER(network_name) = 'arl 01'
"""))

session.commit()
print("✅ Updated ARL 01 WAN1 to AT&T (matching ARIN)")

session.close()