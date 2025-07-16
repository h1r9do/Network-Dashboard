#!/usr/bin/env python3
"""
Populate Circuit History Table from CSV Files
=============================================

This script reads historical tracking CSV files and populates
the circuit_history table by comparing consecutive files to 
detect changes, mimicking the old CSV-based approach.
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

def populate_from_csv_files():
    """Main function to populate circuit history from CSV comparisons"""
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    
    print(f"🚀 Starting circuit history population from CSV files")
    print(f"📂 Looking for CSV files in: {TRACKING_DATA_DIR}")
    
    # Find all tracking CSV files with the EXACT pattern
    tracking_pattern = os.path.join(TRACKING_DATA_DIR, "tracking_data_*.csv")
    all_files = glob.glob(tracking_pattern)
    
    # Filter to only files that match the exact pattern
    valid_pattern = re.compile(r'tracking_data_\d{4}-\d{2}-\d{2}\.csv$')
    exact_match_files = []
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        if valid_pattern.match(filename):
            exact_match_files.append(file_path)
    
    print(f"📊 Found {len(exact_match_files)} valid CSV files")
    
    if len(exact_match_files) < 2:
        print("❌ Need at least 2 CSV files to compare for changes")
        return
    
    # Sort files by date
    file_info = []
    for file_path in exact_match_files:
        try:
            filename = os.path.basename(file_path)
            date_str = filename.replace('tracking_data_', '').replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            file_info.append({
                'path': file_path,
                'date': file_date,
                'date_str': date_str,
                'filename': filename
            })
        except ValueError as e:
            print(f"⚠️  Skipping file with invalid date: {filename}")
            continue
    
    file_info.sort(key=lambda x: x['date'])
    print(f"📅 Date range: {file_info[0]['date_str']} to {file_info[-1]['date_str']}")
    
    # Clear existing history data for fresh start
    with engine.connect() as conn:
        print("🗑️  Clearing existing circuit history...")
        conn.execute(text("TRUNCATE TABLE circuit_history RESTART IDENTITY"))
        conn.commit()
    
    changes_count = 0
    
    # Compare consecutive files
    for i in range(1, len(file_info)):
        prev_file = file_info[i-1]
        curr_file = file_info[i]
        
        print(f"\n🔄 Comparing {prev_file['filename']} vs {curr_file['filename']}")
        
        try:
            # Read CSV files
            df_prev = read_csv_safely(prev_file['path'])
            df_curr = read_csv_safely(curr_file['path'])
            
            if df_prev is None or df_curr is None:
                print(f"⚠️  Skipping comparison due to parsing errors")
                continue
            
            # Find changes between the two files
            file_changes = compare_dataframes_improved(df_prev, df_curr, curr_file['date_str'])
            
            if file_changes:
                print(f"  📝 Found {len(file_changes)} changes")
                
                # Save changes to database
                for change in file_changes:
                    # Find the circuit by site name
                    circuit = Circuit.query.filter_by(site_name=change['site_name']).first()
                    
                    if circuit:
                        # Map change data to CircuitHistory fields
                        history_entry = CircuitHistory(
                            circuit_id=circuit.id,
                            change_type=change.get('change_type', 'OTHER_CHANGE'),
                            field_changed=change.get('field_changed', 'unknown'),
                            old_value=str(change.get('old_value', '')) if change.get('old_value') else None,
                            new_value=str(change.get('new_value', '')) if change.get('new_value') else None,
                            change_date=curr_file['date'],
                            csv_file_source=curr_file['filename']
                        )
                        db.session.add(history_entry)
                        changes_count += 1
                    else:
                        # Circuit not in database, might be a new site
                        print(f"  ⚠️  Circuit not found in database: {change['site_name']}")
            else:
                print(f"  ✓ No changes detected")
                
        except Exception as e:
            print(f"❌ Error comparing files: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"\n✅ Successfully populated {changes_count} historical changes")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        db.session.rollback()
        raise
    
    # Show summary
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT circuit_id) as sites,
                   MIN(change_date) as oldest,
                   MAX(change_date) as newest
            FROM circuit_history
        """))
        row = result.fetchone()
        
        print("\n📈 Circuit History Summary:")
        print(f"   Total Changes: {row.total}")
        print(f"   Sites Tracked: {row.sites}")
        print(f"   Oldest Change: {row.oldest}")
        print(f"   Newest Change: {row.newest}")

def categorize_field(field):
    """Categorize a field for grouping"""
    field_lower = field.lower()
    
    if 'status' in field_lower:
        return 'Circuit Status'
    elif 'provider' in field_lower:
        return 'Service Provider'
    elif 'speed' in field_lower:
        return 'Technical'
    elif 'cost' in field_lower or 'rate' in field_lower:
        return 'Financial'
    elif field in ['sctask', 'assigned_to']:
        return 'Order Management'
    elif field in ['circuit_id', 'billing_wan_ckt_id']:
        return 'Circuit Identification'
    else:
        return 'Other'

def generate_description(change):
    """Generate human-readable description from change data"""
    field = change.get('field_changed', 'unknown')
    old_value = change.get('old_value')
    new_value = change.get('new_value')
    site_name = change.get('site_name', 'Unknown')
    change_type = change.get('change_type', '')
    
    # Handle specific change types
    if change_type == 'new_circuit':
        return f"New circuit added: {site_name}"
    elif change_type == 'removed_circuit':
        return f"Circuit removed: {site_name}"
    
    # Handle field changes
    if not old_value and new_value:
        return f"{field.replace('_', ' ').title()} added: {new_value}"
    elif old_value and not new_value:
        return f"{field.replace('_', ' ').title()} removed (was: {old_value})"
    else:
        if field == 'status':
            return f"Status changed from {old_value} to {new_value}"
        elif 'provider' in field:
            return f"Provider changed from {old_value} to {new_value}"
        elif 'speed' in field:
            return f"Speed changed from {old_value} to {new_value}"
        elif 'cost' in field:
            try:
                old_cost = float(str(old_value).replace('$', '').replace(',', ''))
                new_cost = float(str(new_value).replace('$', '').replace(',', ''))
                diff = new_cost - old_cost
                return f"Cost changed from ${old_cost:.2f} to ${new_cost:.2f} (${diff:+.2f})"
            except:
                return f"Cost changed from {old_value} to {new_value}"
        else:
            return f"{field.replace('_', ' ').title()} updated"

def assess_impact(change):
    """Assess the impact of a change"""
    field = change.get('field_changed', '')
    new_value = change.get('new_value', '')
    change_type = change.get('change_type', '')
    
    # High impact changes
    if change_type in ['new_circuit', 'removed_circuit']:
        return 'High - Circuit added/removed'
    elif field == 'status':
        if 'enabled' in str(new_value).lower():
            return 'High - Circuit now operational'
        elif 'disabled' in str(new_value).lower():
            return 'High - Circuit offline'
        return 'Medium - Status change'
    elif 'provider' in field:
        return 'High - Service provider change'
    
    # Medium impact changes
    elif 'speed' in field:
        return 'Medium - Bandwidth change'
    elif field in ['sctask', 'assigned_to']:
        return 'Medium - Assignment change'
    
    # Low impact changes
    elif 'cost' in field:
        return 'Low - Financial impact'
    else:
        return 'Low - Configuration update'

if __name__ == '__main__':
    # Create Flask app context
    from dsrcircuits_integrated import create_app
    app = create_app()
    
    with app.app_context():
        populate_from_csv_files()