#!/usr/bin/env python3
"""
Status and Substatus Analysis Script
Analyze the actual status/substatus combinations in the latest CSV
"""

import pandas as pd
import glob
import os
import re
from datetime import datetime
from collections import Counter

# Configuration
TRACKING_DATA_DIR = "/var/www/html/circuitinfo"

def safe_str(value):
    """Convert value to string, handling NaN and None safely"""
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()

def analyze_status_substatus():
    """Analyze status and substatus combinations in the latest CSV"""
    print("🔍 STATUS AND SUBSTATUS ANALYSIS")
    print("=" * 60)
    
    # Get the latest tracking file
    tracking_pattern = os.path.join(TRACKING_DATA_DIR, "tracking_data_*.csv")
    all_files = glob.glob(tracking_pattern)
    valid_pattern = re.compile(r'tracking_data_\d{4}-\d{2}-\d{2}\.csv$')
    
    exact_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        if valid_pattern.match(filename):
            try:
                date_str = filename.replace('tracking_data_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                exact_files.append((file_path, file_date))
            except ValueError:
                continue
    
    if not exact_files:
        print("❌ No valid tracking files found")
        return
    
    # Get the latest file
    exact_files.sort(key=lambda x: x[1])
    latest_file, latest_date = exact_files[-1]
    
    print(f"📂 Using latest file: {os.path.basename(latest_file)} ({latest_date.strftime('%Y-%m-%d')})")
    
    try:
        # Read the data
        df = pd.read_csv(latest_file, low_memory=False)
        print(f"📊 Loaded {len(df)} total rows")
        
        # Check if required columns exist
        if 'status' not in df.columns:
            print(f"❌ 'status' column not found. Available columns:")
            print(f"    {list(df.columns)[:15]}{'...' if len(df.columns) > 15 else ''}")
            return
        
        has_substatus = 'substatus' in df.columns
        print(f"📊 Substatus column exists: {has_substatus}")
        
        # Clean the data
        df['status_clean'] = df['status'].apply(safe_str)
        if has_substatus:
            df['substatus_clean'] = df['substatus'].apply(safe_str)
        else:
            df['substatus_clean'] = ""
        
        # Remove empty status records
        df_clean = df[df['status_clean'] != ''].copy()
        print(f"📊 Records with valid status: {len(df_clean)}")
        
        print(f"\n📋 STATUS ANALYSIS:")
        print("-" * 40)
        
        # Get all unique status values
        status_counts = df_clean['status_clean'].value_counts()
        print(f"Total unique status values: {len(status_counts)}")
        
        for status, count in status_counts.items():
            percentage = (count / len(df_clean)) * 100
            print(f"{count:5d} ({percentage:5.1f}%) | {status}")
        
        if has_substatus:
            print(f"\n📋 SUBSTATUS ANALYSIS:")
            print("-" * 40)
            
            # Get all unique substatus values (non-empty)
            substatus_counts = df_clean[df_clean['substatus_clean'] != '']['substatus_clean'].value_counts()
            print(f"Total unique substatus values: {len(substatus_counts)}")
            
            for substatus, count in substatus_counts.items():
                print(f"{count:5d} | {substatus}")
        
        print(f"\n📋 STATUS + SUBSTATUS COMBINATIONS:")
        print("-" * 60)
        
        # Analyze combinations
        if has_substatus:
            combinations = df_clean.groupby(['status_clean', 'substatus_clean']).size().reset_index(name='count')
            combinations = combinations.sort_values(['status_clean', 'count'], ascending=[True, False])
            
            current_status = None
            for _, row in combinations.iterrows():
                status = row['status_clean']
                substatus = row['substatus_clean']
                count = row['count']
                
                if status != current_status:
                    print(f"\n🏷️  {status} ({status_counts[status]} total):")
                    current_status = status
                
                if substatus:
                    print(f"    ├─ {substatus}: {count}")
                else:
                    print(f"    ├─ (no substatus): {count}")
        else:
            print("No substatus column to analyze combinations")
        
        # Special focus on "Ready for Enablement"
        print(f"\n🎯 DETAILED ANALYSIS: 'Ready for Enablement'")
        print("-" * 50)
        
        ready_data = df_clean[df_clean['status_clean'].str.lower() == 'ready for enablement']
        if len(ready_data) > 0:
            print(f"Total 'Ready for Enablement' records: {len(ready_data)}")
            
            if has_substatus:
                ready_substatus = ready_data['substatus_clean'].value_counts()
                print(f"Substatus breakdown:")
                for substatus, count in ready_substatus.items():
                    if substatus:
                        print(f"  • {substatus}: {count}")
                    else:
                        print(f"  • (no substatus): {count}")
            else:
                print("No substatus data available")
                
            # Show some sample records
            print(f"\nSample 'Ready for Enablement' records:")
            sample_cols = ['Site Name', 'status', 'substatus'] if has_substatus else ['Site Name', 'status']
            available_cols = [col for col in sample_cols if col in ready_data.columns]
            if available_cols:
                print(ready_data[available_cols].head(5).to_string(index=False))
        else:
            print("❌ No 'Ready for Enablement' records found")
            # Check for similar status values
            similar_statuses = [s for s in status_counts.index if 'ready' in s.lower() or 'enable' in s.lower()]
            if similar_statuses:
                print(f"Similar status values found: {similar_statuses}")
        
        # Provide categorization suggestions
        print(f"\n💡 CATEGORIZATION SUGGESTIONS:")
        print("-" * 40)
        
        print("Based on the data analysis, here are suggested categories:")
        
        # Group statuses by likely categories
        enabled_keywords = ['enabled', 'active', 'activated']
        ready_keywords = ['ready for enablement', 'pending scheduled deployment']
        customer_keywords = ['customer action required', 'customer']
        approval_keywords = ['information/approval needed', 'approval']
        construction_keywords = ['construction', 'installation', 'survey']
        canceled_keywords = ['order canceled', 'canceled', 'cancelled']
        
        categories = {
            '🟢 ENABLED/ACTIVE': [],
            '🟡 READY FOR ENABLEMENT': [],
            '🔴 CUSTOMER ACTION REQUIRED': [],
            '🟠 APPROVAL/INFORMATION NEEDED': [],
            '🔨 CONSTRUCTION/INSTALLATION': [],
            '❌ CANCELED/DISCONNECTED': [],
            '⚪ OTHER': []
        }
        
        for status in status_counts.index:
            status_lower = status.lower()
            categorized = False
            
            if any(keyword in status_lower for keyword in enabled_keywords):
                categories['🟢 ENABLED/ACTIVE'].append((status, status_counts[status]))
                categorized = True
            elif any(keyword in status_lower for keyword in ready_keywords):
                categories['🟡 READY FOR ENABLEMENT'].append((status, status_counts[status]))
                categorized = True
            elif any(keyword in status_lower for keyword in customer_keywords):
                categories['🔴 CUSTOMER ACTION REQUIRED'].append((status, status_counts[status]))
                categorized = True
            elif any(keyword in status_lower for keyword in approval_keywords):
                categories['🟠 APPROVAL/INFORMATION NEEDED'].append((status, status_counts[status]))
                categorized = True
            elif any(keyword in status_lower for keyword in construction_keywords):
                categories['🔨 CONSTRUCTION/INSTALLATION'].append((status, status_counts[status]))
                categorized = True
            elif any(keyword in status_lower for keyword in canceled_keywords):
                categories['❌ CANCELED/DISCONNECTED'].append((status, status_counts[status]))
                categorized = True
            
            if not categorized:
                categories['⚪ OTHER'].append((status, status_counts[status]))
        
        for category, statuses in categories.items():
            if statuses:
                total_count = sum(count for _, count in statuses)
                print(f"\n{category} ({total_count} total):")
                for status, count in sorted(statuses, key=lambda x: x[1], reverse=True):
                    print(f"  • {status}: {count}")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_status_substatus()
