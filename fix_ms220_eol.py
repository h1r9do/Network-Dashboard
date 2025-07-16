#!/usr/bin/env python3
"""
Fix MS220 EOL data based on the PDF content we saw
"""

import psycopg2
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
import re

def get_db_connection():
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Fixing MS220 EOL data based on PDF content...")
    
    # Based on the MS220 PDF content:
    # MS220-24/48 series: Announced March 16, 2017, EOS July 29, 2017, EOL July 29, 2024
    # MS220-8 series: Announced Jan 9, 2018, EOS Sept 21, 2018, EOL Sept 21, 2025
    
    ms220_data = [
        # MS220-8 series (from ms220-8.pdf)
        ('MS220-8', 'MS220-8 Cloud Managed 8 Port GigE Switch', date(2018, 1, 9), date(2018, 9, 21), date(2025, 9, 21)),
        ('MS220-8P', 'MS220-8P Cloud Managed 8 Port GigE PoE Switch', date(2018, 1, 9), date(2018, 9, 21), date(2025, 9, 21)),
        
        # MS220-24/48 series (from ms220.pdf)
        ('MS220-24', 'MS220-24 L2 Cloud Managed 24 Port GigE Switch', date(2017, 3, 16), date(2017, 7, 29), date(2024, 7, 29)),
        ('MS220-24P', 'MS220-24P L2 Cloud Managed 24 Port GigE 370W PoE Switch', date(2017, 3, 16), date(2017, 7, 29), date(2024, 7, 29)),
        ('MS220-48', 'MS220-48 L2 Cloud Managed 48 Port GigE Switch', date(2017, 3, 16), date(2017, 7, 29), date(2024, 7, 29)),
        ('MS220-48LP', 'MS220-48LP L2 Cloud Managed 48 Port GigE 370W PoE Switch', date(2017, 3, 16), date(2017, 7, 29), date(2024, 7, 29)),
        ('MS220-48FP', 'MS220-48FP L2 Cloud Managed 48 Port GigE 740W PoE Switch', date(2017, 3, 16), date(2017, 7, 29), date(2024, 7, 29)),
    ]
    
    # Insert/update in enhanced EOL table
    for model, desc, ann_date, eos_date, eol_date in ms220_data:
        cursor.execute("""
            INSERT INTO meraki_eol_enhanced (
                model, description, announcement_date, end_of_sale, end_of_support,
                source, pdf_name, confidence
            ) VALUES (%s, %s, %s, %s, %s, 'PDF', %s, 'high')
            ON CONFLICT (model) DO UPDATE SET
                description = EXCLUDED.description,
                announcement_date = EXCLUDED.announcement_date,
                end_of_sale = EXCLUDED.end_of_sale,
                end_of_support = EXCLUDED.end_of_support,
                source = EXCLUDED.source,
                pdf_name = EXCLUDED.pdf_name,
                updated_at = NOW()
        """, (
            model, desc, ann_date, eos_date, eol_date,
            'meraki_eol_ms220-8.pdf' if '8' in model else 'meraki_eol_ms220.pdf'
        ))
        print(f"Updated {model}: EOS={eos_date}, EOL={eol_date}")
    
    # Update inventory summary
    cursor.execute("""
        UPDATE inventory_summary s
        SET 
            announcement_date = e.announcement_date,
            end_of_sale = e.end_of_sale,
            end_of_support = e.end_of_support,
            highlight = CASE
                WHEN e.end_of_support <= CURRENT_DATE THEN 'red'
                WHEN e.end_of_sale <= CURRENT_DATE THEN 'yellow'
                WHEN e.end_of_sale > CURRENT_DATE THEN 'blue'
                ELSE NULL
            END
        FROM meraki_eol_enhanced e
        WHERE s.model = e.model
          AND s.model LIKE 'MS220%'
    """)
    
    updated = cursor.rowcount
    print(f"\nUpdated {updated} models in inventory_summary")
    
    # Check results
    cursor.execute("""
        SELECT model, announcement_date, end_of_sale, end_of_support, highlight
        FROM inventory_summary
        WHERE model LIKE 'MS220%'
        ORDER BY model
    """)
    
    print("\n=== Updated MS220 Inventory Summary ===")
    for row in cursor.fetchall():
        model, ann, eos, eol, highlight = row
        status = "EOL" if highlight == 'red' else "EOS" if highlight == 'yellow' else "Active"
        print(f"{model}: EOS={eos}, EOL={eol} (Status: {status})")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\nMS220 EOL data fixed successfully!")

if __name__ == "__main__":
    main()