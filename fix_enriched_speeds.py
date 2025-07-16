#!/usr/bin/env python3
"""
Manual fix for speed corruption in enriched_circuits table
Run this after the nightly enrichment to fix corrupted speed values
"""

import psycopg2
import re
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def fix_corrupted_speeds():
    """Fix speed values that show only download speed"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Starting speed corruption fix at {datetime.now()}")
    
    # Find corrupted speeds (format like "300.0 M" instead of "300.0M x 30.0M")
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_speed,
            ec.wan2_speed,
            c1.details_ordered_service_speed as dsr_primary_speed,
            c2.details_ordered_service_speed as dsr_secondary_speed,
            mi.device_notes
        FROM enriched_circuits ec
        LEFT JOIN circuits c1 ON c1.site_name = REPLACE(ec.network_name, '_', '')
            AND c1.circuit_purpose = 'Primary' AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON c2.site_name = REPLACE(ec.network_name, '_', '')
            AND c2.circuit_purpose = 'Secondary' AND c2.status = 'Enabled'
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        WHERE ec.wan1_speed LIKE '% M' OR ec.wan2_speed LIKE '% M'
    """)
    
    fixes = []
    for row in cursor.fetchall():
        network_name = row[0]
        wan1_speed = row[1]
        wan2_speed = row[2]
        dsr_primary = row[3]
        dsr_secondary = row[4]
        device_notes = row[5]
        
        # Determine correct speeds
        wan1_correct = dsr_primary if dsr_primary and 'x' in str(dsr_primary) else wan1_speed
        wan2_correct = dsr_secondary if dsr_secondary and 'x' in str(dsr_secondary) else wan2_speed
        
        # If still corrupted and we have device notes, parse them
        if device_notes and ('% M' in str(wan1_correct) or '% M' in str(wan2_correct)):
            # Parse device notes for speed
            notes_lines = device_notes.strip().split('\n')
            wan1_section = False
            wan2_section = False
            
            for i, line in enumerate(notes_lines):
                if 'WAN 1' in line or 'WAN1' in line:
                    wan1_section = True
                    wan2_section = False
                elif 'WAN 2' in line or 'WAN2' in line:
                    wan1_section = False
                    wan2_section = True
                elif re.match(r'\d+\.?\d*M\s*x\s*\d+\.?\d*M', line):
                    if wan1_section and '% M' in str(wan1_correct):
                        wan1_correct = line.strip()
                    elif wan2_section and '% M' in str(wan2_correct):
                        wan2_correct = line.strip()
        
        # Check if we need to fix anything
        if wan1_correct != wan1_speed or wan2_correct != wan2_speed:
            fixes.append({
                'network_name': network_name,
                'wan1_old': wan1_speed,
                'wan1_new': wan1_correct,
                'wan2_old': wan2_speed,
                'wan2_new': wan2_correct
            })
    
    # Apply fixes
    if fixes:
        print(f"\nFound {len(fixes)} networks with corrupted speeds. Fixing...")
        
        for fix in fixes:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan1_speed = %s, wan2_speed = %s
                WHERE network_name = %s
            """, (fix['wan1_new'], fix['wan2_new'], fix['network_name']))
            
            print(f"Fixed {fix['network_name']}:")
            print(f"  WAN1: '{fix['wan1_old']}' → '{fix['wan1_new']}'")
            print(f"  WAN2: '{fix['wan2_old']}' → '{fix['wan2_new']}'")
        
        conn.commit()
        print(f"\n✅ Successfully fixed {len(fixes)} corrupted speed entries")
    else:
        print("✅ No corrupted speeds found")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fix_corrupted_speeds()
