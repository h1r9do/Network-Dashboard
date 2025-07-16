#!/usr/bin/env python3
"""
Manually populate historical data for testing
This script will compare consecutive days and populate the circuit_history table
"""

import os
import sys
from datetime import datetime, timedelta

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import TRACKING_DATA_DIR, read_csv_safely, compare_dataframes_improved
from models import db, Circuit, CircuitHistory
from dsrcircuits import create_app

def populate_historical_for_date_range(start_date, end_date):
    """Populate historical data for a date range"""
    print(f"🔍 Populating historical data from {start_date} to {end_date}")
    
    current_date = start_date
    total_changes = 0
    
    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        
        # File paths
        current_file = os.path.join(TRACKING_DATA_DIR, f"tracking_data_{current_date}.csv")
        next_file = os.path.join(TRACKING_DATA_DIR, f"tracking_data_{next_date}.csv")
        
        if not os.path.exists(current_file) or not os.path.exists(next_file):
            print(f"⚠️  Skipping {current_date} to {next_date} - files missing")
            current_date = next_date
            continue
            
        print(f"\n📅 Comparing {current_date} vs {next_date}")
        
        # Read CSV files
        df_prev = read_csv_safely(current_file)
        df_curr = read_csv_safely(next_file)
        
        if df_prev is None or df_curr is None:
            print(f"❌ Error reading CSV files")
            current_date = next_date
            continue
        
        # Find changes
        changes = compare_dataframes_improved(df_prev, df_curr, str(next_date))
        
        if not changes:
            print(f"✓ No changes detected")
            current_date = next_date
            continue
            
        print(f"📝 Found {len(changes)} changes")
        
        # Save changes to database
        changes_saved = 0
        circuits_not_found = []
        
        for change in changes:
            # Find the circuit by site name AND site_id for exact match
            circuit = None
            if 'site_id' in change and change['site_id']:
                # First try exact match on site_id
                circuit = Circuit.query.filter_by(
                    site_name=change['site_name'],
                    site_id=change['site_id']
                ).first()
            
            if not circuit:
                # Fallback to site_name only
                circuit = Circuit.query.filter_by(site_name=change['site_name']).first()
            
            if circuit:
                # Check if this change already exists
                existing = CircuitHistory.query.filter_by(
                    circuit_id=circuit.id,
                    change_date=next_date,
                    change_type=change.get('change_type', 'OTHER_CHANGE'),
                    field_changed=change.get('field_changed', 'unknown')
                ).first()
                
                if not existing:
                    # Create history entry
                    history_entry = CircuitHistory(
                        circuit_id=circuit.id,
                        change_type=change.get('change_type', 'OTHER_CHANGE'),
                        field_changed=change.get('field_changed', 'unknown'),
                        old_value=str(change.get('before_value', '')) if change.get('before_value') else None,
                        new_value=str(change.get('after_value', '')) if change.get('after_value') else None,
                        change_date=next_date,
                        csv_file_source=f"tracking_data_{next_date}.csv"
                    )
                    db.session.add(history_entry)
                    changes_saved += 1
            else:
                circuits_not_found.append(f"{change['site_name']} (ID: {change.get('site_id', 'N/A')})")
        
        if circuits_not_found:
            print(f"  ⚠️  {len(circuits_not_found)} circuits not found in database")
            if len(circuits_not_found) <= 5:
                for cnf in circuits_not_found:
                    print(f"     - {cnf}")
        
        # Commit changes
        try:
            db.session.commit()
            print(f"✅ Successfully saved {changes_saved} changes")
            total_changes += changes_saved
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            db.session.rollback()
        
        current_date = next_date
    
    return total_changes

def main():
    """Main function"""
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Check current state of circuit_history
        current_count = CircuitHistory.query.count()
        print(f"📊 Current circuit_history records: {current_count}")
        
        # Populate last 7 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        total = populate_historical_for_date_range(start_date, end_date)
        
        # Final count
        final_count = CircuitHistory.query.count()
        print(f"\n✅ Population complete!")
        print(f"   Added: {final_count - current_count} records")
        print(f"   Total: {final_count} records")
        
        # Show sample data
        if final_count > 0:
            print("\n📈 Sample historical data:")
            samples = CircuitHistory.query.order_by(CircuitHistory.change_date.desc()).limit(5).all()
            for sample in samples:
                circuit = Circuit.query.get(sample.circuit_id)
                print(f"   - {sample.change_date}: {circuit.site_name if circuit else 'Unknown'} - {sample.field_changed}: {sample.old_value} → {sample.new_value}")

if __name__ == '__main__':
    main()