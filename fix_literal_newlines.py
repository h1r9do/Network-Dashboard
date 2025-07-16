#!/usr/bin/env python3
"""
Fix literal \n in device notes
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Find all sites with literal \n
    result = session.execute(text('''
        SELECT network_name, device_notes
        FROM meraki_inventory
        WHERE device_notes LIKE '%\\\\n%'
    '''))
    
    sites = result.fetchall()
    print(f'Found {len(sites)} sites with literal \\n in device notes')
    
    fixed_count = 0
    for network_name, old_notes in sites:
        if old_notes:
            # Replace literal \n with actual newlines
            new_notes = old_notes.replace('\\n', '\n')
            
            # Update the notes
            session.execute(text('''
                UPDATE meraki_inventory
                SET device_notes = :notes
                WHERE network_name = :network
            '''), {'notes': new_notes, 'network': network_name})
            
            fixed_count += 1
            if fixed_count % 10 == 0:
                print(f'  Fixed {fixed_count} sites...')
    
    session.commit()
    print(f'✅ Fixed {fixed_count} sites with literal newlines')
    
except Exception as e:
    print(f'Error: {e}')
    session.rollback()
finally:
    session.close()