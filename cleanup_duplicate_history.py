#!/usr/bin/env python3
"""
Cleanup Duplicate Circuit History Records
========================================

This script removes duplicate circuit history records, keeping the ones
with proper old_value/new_value data and removing empty duplicates.

This is useful for cleaning up historical data that may have been
created with different import processes.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config

def cleanup_duplicate_history(target_date=None):
    """
    Clean up duplicate circuit history records
    
    Args:
        target_date (str): Specific date to clean (YYYY-MM-DD) or None for all dates
    """
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    
    print(f"🧹 Starting duplicate circuit history cleanup")
    if target_date:
        print(f"📅 Target date: {target_date}")
    else:
        print(f"📅 Target: All dates")
    
    # Build the WHERE clause
    date_filter = "AND ch1.change_date = :target_date" if target_date else ""
    params = {'target_date': target_date} if target_date else {}
    
    # Count duplicates first
    with engine.connect() as conn:
        count_query = f"""
            SELECT COUNT(*) as duplicate_count
            FROM circuit_history ch1
            WHERE (ch1.old_value IS NULL OR ch1.old_value = '')
            AND (ch1.new_value IS NULL OR ch1.new_value = '')
            {date_filter}
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
        """
        
        result = conn.execute(text(count_query), params)
        duplicate_count = result.fetchone().duplicate_count
    
    if duplicate_count == 0:
        print("✅ No duplicate records found")
        return
    
    print(f"🔍 Found {duplicate_count} duplicate records with empty values")
    
    # Perform the cleanup
    try:
        with engine.connect() as conn:
            delete_query = f"""
                DELETE FROM circuit_history ch1
                WHERE (ch1.old_value IS NULL OR ch1.old_value = '')
                AND (ch1.new_value IS NULL OR ch1.new_value = '')
                {date_filter}
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
            """
            
            result = conn.execute(text(delete_query), params)
            deleted_count = result.rowcount
            
            print(f"🗑️ Successfully removed {deleted_count} duplicate records")
            
            # Show summary
            if target_date:
                summary_query = """
                    SELECT COUNT(*) as remaining_count
                    FROM circuit_history
                    WHERE change_date = :target_date
                """
                result = conn.execute(text(summary_query), {'target_date': target_date})
                remaining = result.fetchone().remaining_count
                print(f"📊 Remaining records for {target_date}: {remaining}")
            else:
                summary_query = """
                    SELECT COUNT(*) as total_records,
                           COUNT(CASE WHEN old_value IS NULL OR old_value = '' THEN 1 END) as empty_records
                    FROM circuit_history
                """
                result = conn.execute(text(summary_query))
                stats = result.fetchone()
                print(f"📊 Total remaining records: {stats.total_records}")
                print(f"📊 Records with empty values: {stats.empty_records}")
                
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up duplicate circuit history records')
    parser.add_argument('--date', help='Specific date to clean (YYYY-MM-DD)')
    parser.add_argument('--all', action='store_true', help='Clean all dates')
    
    args = parser.parse_args()
    
    if args.date:
        cleanup_duplicate_history(args.date)
    elif args.all:
        cleanup_duplicate_history()
    else:
        print("Usage:")
        print("  python3 cleanup_duplicate_history.py --date 2025-06-26")
        print("  python3 cleanup_duplicate_history.py --all")
        print("\nThis will remove duplicate circuit history records that have empty")
        print("old_value/new_value fields when better records exist for the same change.")