#!/usr/bin/env python3
"""
Flatten raw notes to single line for CSV export
"""

import pandas as pd
import json
from datetime import datetime

def flatten_raw_notes():
    """Re-export with flattened raw notes (no newlines)"""
    
    print("=== FLATTENING RAW NOTES IN EXPORT ===\n")
    
    # Read the original export
    csv_file = '/usr/local/bin/non_dsr_circuits_for_import_20250709_112240.csv'
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} circuits from CSV\n")
    
    # Load the MX inventory JSON
    json_file = '/tmp/mx_inventory.json'
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    # Extract devices array
    mx_data = json_data.get('devices', [])
    print(f"Loaded {len(mx_data)} devices from JSON\n")
    
    # Create a lookup dictionary for device notes by network name
    notes_lookup = {}
    for device in mx_data:
        network_name = device.get('network_name', '')
        # Get raw notes and flatten them (replace newlines with spaces)
        device_notes = device.get('raw_notes', '') or device.get('device_notes', '')
        if network_name and device_notes:
            # Replace newlines with spaces to flatten
            flattened_notes = device_notes.replace('\n', ' ').replace('\r', ' ')
            # Clean up multiple spaces
            flattened_notes = ' '.join(flattened_notes.split())
            notes_lookup[network_name] = flattened_notes
    
    # Add flattened raw notes column
    df['raw_notes'] = df['site_name'].map(notes_lookup).fillna('')
    
    # Count how many got notes
    notes_found = (df['raw_notes'] != '').sum()
    print(f"Found raw notes for {notes_found} out of {len(df)} circuits")
    
    # Show sample of flattened notes
    print("\nSample of flattened raw notes:")
    sample = df[df['raw_notes'] != ''].head(5)
    for _, row in sample.iterrows():
        print(f"\n{row['site_name']} ({row['wan_interface']}):")
        print(f"  {row['raw_notes']}")
    
    # Save updated CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/usr/local/bin/non_dsr_circuits_flattened_notes_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Export with flattened notes saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    flatten_raw_notes()