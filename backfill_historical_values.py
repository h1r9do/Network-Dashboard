#!/usr/bin/env python3
"""
Backfill Historical Values - Fix Missing Before/After Values
===========================================================

This script fixes the missing old_value/new_value data in circuit_history
by re-running CSV comparisons with the corrected field mapping.

It updates existing records instead of creating duplicates.
"""

import os
import sys
import glob
import re
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import db, Circuit, CircuitHistory
from utils import TRACKING_DATA_DIR, read_csv_safely, compare_dataframes_improved

def backfill_missing_values():
    """Backfill missing old_value/new_value data in circuit_history"""
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    
    print(f"🔄 Starting backfill of missing historical values")
    
    # Count records with missing values
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN old_value IS NULL OR old_value = '' THEN 1 END) as missing
            FROM circuit_history
        """))
        stats = result.fetchone()
        total_records = stats.total
        missing_records = stats.missing
    
    print(f"📊 Found {missing_records} of {total_records} records with missing before/after values")
    
    if missing_records == 0:
        print("✅ All records already have proper values")
        return
    
    # Find all tracking CSV files
    tracking_pattern = os.path.join(TRACKING_DATA_DIR, "tracking_data_*.csv")
    all_files = glob.glob(tracking_pattern)
    
    # Filter to only files that match the exact pattern
    valid_pattern = re.compile(r'tracking_data_(\d{4}-\d{2}-\d{2})\.csv$')
    file_info = []
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        match = valid_pattern.match(filename)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                file_info.append({
                    'path': file_path,
                    'date': file_date,
                    'date_str': date_str,
                    'filename': filename
                })
            except ValueError:
                continue
    
    # Sort by date
    file_info.sort(key=lambda x: x['date'])
    
    print(f"📂 Found {len(file_info)} valid CSV files to process")
    
    if len(file_info) < 2:
        print("❌ Need at least 2 CSV files to compare for changes")
        return
    
    # Track updates
    updates_made = 0
    
    # Compare consecutive files and update missing values
    for i in range(1, len(file_info)):
        prev_file = file_info[i-1]
        curr_file = file_info[i]
        
        print(f"\n🔄 Processing {curr_file['date_str']}")
        
        # Check if this date has records with missing values
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as missing_count
                FROM circuit_history 
                WHERE change_date = :date 
                AND (old_value IS NULL OR old_value = '' OR new_value IS NULL OR new_value = '')
            """), {'date': curr_file['date']})
            missing_for_date = result.fetchone().missing_count
        
        if missing_for_date == 0:
            print(f"  ✓ No missing values for {curr_file['date_str']}")
            continue
        
        print(f"  📝 Found {missing_for_date} records with missing values")
        
        try:
            # Read CSV files
            df_prev = read_csv_safely(prev_file['path'])
            df_curr = read_csv_safely(curr_file['path'])
            
            if df_prev is None or df_curr is None:
                print(f"  ⚠️  Skipping due to CSV parsing errors")
                continue
            
            # Find changes between the two files
            file_changes = compare_dataframes_improved(df_prev, df_curr, curr_file['date_str'])
            
            if not file_changes:
                print(f"  ✓ No changes detected")
                continue
            
            print(f"  🔍 Found {len(file_changes)} changes, updating database...")
            
            # Update existing records with the correct before/after values
            date_updates = 0
            for change in file_changes:
                # Find the circuit by site name
                circuit = Circuit.query.filter_by(site_name=change['site_name']).first()
                
                if not circuit:
                    continue
                
                # Find the corresponding history record
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        UPDATE circuit_history 
                        SET old_value = :old_value,
                            new_value = :new_value
                        WHERE circuit_id = :circuit_id 
                        AND change_date = :change_date 
                        AND change_type = :change_type 
                        AND field_changed = :field_changed
                        AND (old_value IS NULL OR old_value = '' OR new_value IS NULL OR new_value = '')
                    """), {
                        'old_value': change.get('before_value', ''),
                        'new_value': change.get('after_value', ''),
                        'circuit_id': circuit.id,
                        'change_date': curr_file['date'],
                        'change_type': change.get('change_type', 'OTHER_CHANGE'),
                        'field_changed': change.get('field_changed', 'unknown')
                    })
                    
                    if result.rowcount > 0:
                        date_updates += result.rowcount
            
            updates_made += date_updates
            print(f"  ✅ Updated {date_updates} records for {curr_file['date_str']}")
            
        except Exception as e:
            print(f"  ❌ Error processing {curr_file['date_str']}: {e}")
            continue
    
    print(f"\n🎉 Backfill complete!")
    print(f"   📊 Total records updated: {updates_made}")
    print(f"   📈 Original missing records: {missing_records}")
    
    # Final count
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN old_value IS NULL OR old_value = '' THEN 1 END) as still_missing
            FROM circuit_history
        """))
        final_stats = result.fetchone()
        remaining_missing = final_stats.still_missing
    
    print(f"   📉 Remaining missing: {remaining_missing}")
    print(f"   ✅ Improvement: {missing_records - remaining_missing} records now have proper values")

if __name__ == '__main__':
    # Create Flask app context
    try:
        from dsrcircuits_integrated import create_app
        app = create_app()
        
        with app.app_context():
            backfill_missing_values()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()