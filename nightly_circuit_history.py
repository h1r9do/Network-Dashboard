#!/usr/bin/env python3
"""
Nightly Circuit History Update
==============================

This script compares today's tracking CSV file with yesterday's 
to detect changes and update the circuit_history table.

Should be run daily via cron after the tracking CSV is generated.
"""

import os
import sys
import glob
import re
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import db, Circuit, CircuitHistory
from utils import TRACKING_DATA_DIR, read_csv_safely, compare_dataframes_improved

def update_circuit_history():
    """Update circuit history with today's changes"""
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    
    print(f"🚀 Starting nightly circuit history update - {datetime.now()}")
    
    # Get today and yesterday dates
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # File paths
    yesterday_file = os.path.join(TRACKING_DATA_DIR, f"tracking_data_{yesterday}.csv")
    today_file = os.path.join(TRACKING_DATA_DIR, f"tracking_data_{today}.csv")
    
    print(f"📅 Comparing {yesterday} vs {today}")
    
    # Check if files exist
    if not os.path.exists(yesterday_file):
        print(f"❌ Yesterday's file not found: {yesterday_file}")
        return
        
    if not os.path.exists(today_file):
        print(f"❌ Today's file not found: {today_file}")
        return
    
    # Read CSV files
    print(f"📂 Reading CSV files...")
    df_yesterday = read_csv_safely(yesterday_file)
    df_today = read_csv_safely(today_file)
    
    if df_yesterday is None or df_today is None:
        print(f"❌ Error reading CSV files")
        return
    
    # Find changes
    print(f"🔍 Detecting changes...")
    changes = compare_dataframes_improved(df_yesterday, df_today, str(today))
    
    if not changes:
        print(f"✓ No changes detected for {today}")
        return
    
    print(f"📝 Found {len(changes)} changes")
    
    # Save changes to database
    changes_saved = 0
    for change in changes:
        # Find the circuit by site name
        circuit = Circuit.query.filter_by(site_name=change['site_name']).first()
        
        if circuit:
            # Create history entry
            history_entry = CircuitHistory(
                circuit_id=circuit.id,
                change_type=change.get('change_type', 'OTHER_CHANGE'),
                field_changed=change.get('field_changed', 'unknown'),
                old_value=str(change.get('before_value', '')) if change.get('before_value') else None,
                new_value=str(change.get('after_value', '')) if change.get('after_value') else None,
                change_date=today,
                csv_file_source=f"tracking_data_{today}.csv"
            )
            db.session.add(history_entry)
            changes_saved += 1
        else:
            print(f"  ⚠️  Circuit not found in database: {change['site_name']}")
    
    # Commit changes
    try:
        db.session.commit()
        print(f"✅ Successfully saved {changes_saved} changes to circuit history")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        db.session.rollback()
        raise
    
    # Clean up duplicate records (keep ones with data, remove empty ones)
    print("🧹 Cleaning up duplicate records...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM circuit_history ch1
                WHERE ch1.change_date = :today
                AND (ch1.old_value IS NULL OR ch1.old_value = '')
                AND (ch1.new_value IS NULL OR ch1.new_value = '')
                AND EXISTS (
                  SELECT 1 FROM circuit_history ch2
                  WHERE ch2.circuit_id = ch1.circuit_id
                  AND ch2.change_type = ch1.change_type
                  AND ch2.field_changed = ch1.field_changed
                  AND ch2.change_date = ch1.change_date
                  AND ch2.id <> ch1.id
                  AND (ch2.old_value IS NOT NULL AND ch2.old_value <> '')
                  AND (ch2.new_value IS NOT NULL AND ch2.new_value <> '')
                )
            """), {'today': today})
            
            duplicates_removed = result.rowcount
            if duplicates_removed > 0:
                print(f"🗑️ Removed {duplicates_removed} duplicate records with empty values")
            else:
                print("✓ No duplicate records found")
                
    except Exception as e:
        print(f"⚠️ Warning: Error during cleanup: {e}")
        # Don't fail the whole process for cleanup issues
    
    # Show summary
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as today_changes
            FROM circuit_history
            WHERE change_date = :today
        """), {'today': today})
        row = result.fetchone()
        
        print(f"\n📈 Today's Summary:")
        print(f"   Changes recorded: {row.today_changes}")
        print(f"   Date: {today}")
        print(f"   Source: tracking_data_{today}.csv")

if __name__ == '__main__':
    # Create Flask app context
    from dsrcircuits_integrated import create_app
    app = create_app()
    
    with app.app_context():
        update_circuit_history()