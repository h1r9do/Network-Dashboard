#!/usr/bin/env python3
"""
Populate ALL available historical data from tracking CSV files
This will process all available tracking files to build complete history
"""

import os
import sys
import glob
from datetime import datetime, timedelta

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import TRACKING_DATA_DIR, read_csv_safely, compare_dataframes_improved
from models import db, Circuit, CircuitHistory
from dsrcircuits import create_app

def get_all_tracking_files():
    """Get all tracking CSV files sorted by date"""
    pattern = os.path.join(TRACKING_DATA_DIR, "tracking_data_*.csv")
    files = glob.glob(pattern)
    
    # Extract dates and sort
    file_dates = []
    for f in files:
        try:
            # Extract date from filename
            basename = os.path.basename(f)
            date_str = basename.replace("tracking_data_", "").replace(".csv", "")
            # Skip dedup files
            if "_dedup" in date_str:
                continue
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            file_dates.append((date_obj, f))
        except ValueError:
            print(f"⚠️  Skipping file with invalid date format: {f}")
            continue
    
    # Sort by date
    file_dates.sort(key=lambda x: x[0])
    return file_dates

def populate_all_historical_data():
    """Populate historical data from all available tracking files"""
    file_dates = get_all_tracking_files()
    
    if len(file_dates) < 2:
        print("❌ Need at least 2 tracking files to generate history")
        return 0
    
    print(f"📊 Found {len(file_dates)} tracking files")
    print(f"📅 Date range: {file_dates[0][0]} to {file_dates[-1][0]}")
    
    total_changes = 0
    
    # Process consecutive file pairs
    for i in range(len(file_dates) - 1):
        current_date, current_file = file_dates[i]
        next_date, next_file = file_dates[i + 1]
        
        print(f"\n📅 Comparing {current_date} vs {next_date}")
        
        # Read CSV files
        df_prev = read_csv_safely(current_file)
        df_curr = read_csv_safely(next_file)
        
        if df_prev is None or df_curr is None:
            print(f"❌ Error reading CSV files")
            continue
        
        # Find changes
        changes = compare_dataframes_improved(df_prev, df_curr, str(next_date))
        
        if not changes:
            print(f"✓ No changes detected")
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
                # More thorough duplicate check including old/new values
                existing = CircuitHistory.query.filter_by(
                    circuit_id=circuit.id,
                    change_date=next_date,
                    change_type=change.get('change_type', 'OTHER_CHANGE'),
                    field_changed=change.get('field_changed', 'unknown')
                ).first()
                
                # If exists, check if values match
                if existing:
                    old_val = str(change.get('before_value', '')) if change.get('before_value') else None
                    new_val = str(change.get('after_value', '')) if change.get('after_value') else None
                    
                    # Only skip if the values also match
                    if existing.old_value == old_val and existing.new_value == new_val:
                        continue
                    else:
                        # Different values for same field/date - this is unusual, log it
                        print(f"  ⚠️  Duplicate with different values: {circuit.site_name} - {change.get('field_changed')} on {next_date}")
                        print(f"      Existing: {existing.old_value} → {existing.new_value}")
                        print(f"      New: {old_val} → {new_val}")
                        continue  # Skip to avoid duplicates
                
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
                site_info = f"{change['site_name']} (ID: {change.get('site_id', 'N/A')})"
                if site_info not in circuits_not_found:
                    circuits_not_found.append(site_info)
        
        if circuits_not_found and len(circuits_not_found) <= 10:
            print(f"  ⚠️  {len(circuits_not_found)} circuits not found in database:")
            for cnf in circuits_not_found[:10]:
                print(f"     - {cnf}")
            if len(circuits_not_found) > 10:
                print(f"     ... and {len(circuits_not_found) - 10} more")
        elif circuits_not_found:
            print(f"  ⚠️  {len(circuits_not_found)} circuits not found in database")
        
        # Commit changes for this date pair
        try:
            db.session.commit()
            print(f"✅ Successfully saved {changes_saved} changes")
            total_changes += changes_saved
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            db.session.rollback()
    
    return total_changes

def main():
    """Main function"""
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Clear existing data if requested
        if len(sys.argv) > 1 and sys.argv[1] == '--clear':
            print("🗑️  Clearing existing circuit history...")
            CircuitHistory.query.delete()
            db.session.commit()
            print("✅ Existing history cleared")
        
        # Check current state
        current_count = CircuitHistory.query.count()
        print(f"📊 Current circuit_history records: {current_count}")
        
        # Populate all historical data
        total = populate_all_historical_data()
        
        # Final count
        final_count = CircuitHistory.query.count()
        print(f"\n✅ Population complete!")
        print(f"   Added: {final_count - current_count} records")
        print(f"   Total: {final_count} records")
        
        # Show date range
        if final_count > 0:
            oldest = CircuitHistory.query.order_by(CircuitHistory.change_date.asc()).first()
            newest = CircuitHistory.query.order_by(CircuitHistory.change_date.desc()).first()
            print(f"\n📅 Historical data range:")
            print(f"   From: {oldest.change_date}")
            print(f"   To: {newest.change_date}")
            
            # Show sample data
            print("\n📈 Recent changes:")
            samples = CircuitHistory.query.order_by(CircuitHistory.change_date.desc()).limit(10).all()
            for sample in samples:
                circuit = Circuit.query.get(sample.circuit_id)
                if circuit:
                    print(f"   - {sample.change_date}: {circuit.site_name} - {sample.field_changed}: {sample.old_value} → {sample.new_value}")

if __name__ == '__main__':
    main()