#!/usr/bin/env python3
"""
Add raw notes from MX inventory JSON to the non-DSR circuits export
"""

import pandas as pd
import json
from datetime import datetime

def add_raw_notes():
    """Add raw notes from MX inventory JSON to the export"""
    
    print("=== ADDING RAW NOTES TO NON-DSR CIRCUITS EXPORT ===\n")
    
    # Read the existing CSV export
    csv_file = '/usr/local/bin/non_dsr_circuits_for_import_20250709_112240.csv'
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} circuits from CSV\n")
    
    # Load the MX inventory JSON
    json_file = '/tmp/mx_inventory.json'
    print(f"Loading MX inventory from: {json_file}")
    
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    # Extract devices array
    mx_data = json_data.get('devices', [])
    print(f"Loaded {len(mx_data)} devices from JSON\n")
    
    # Create a lookup dictionary for device notes by network name
    notes_lookup = {}
    for device in mx_data:
        network_name = device.get('network_name', '')
        # Look for raw_notes or device_notes
        device_notes = device.get('raw_notes', '') or device.get('device_notes', '')
        if network_name:
            notes_lookup[network_name] = device_notes
    
    # Add raw notes column
    df['raw_notes'] = df['site_name'].map(notes_lookup).fillna('')
    
    # Count how many got notes
    notes_found = (df['raw_notes'] != '').sum()
    print(f"Found raw notes for {notes_found} out of {len(df)} circuits")
    
    # Show sample of sites with notes
    print("\nSample of raw notes found:")
    sample = df[df['raw_notes'] != ''].head(5)
    for _, row in sample.iterrows():
        notes_preview = row['raw_notes'][:100] + '...' if len(row['raw_notes']) > 100 else row['raw_notes']
        print(f"\n{row['site_name']} ({row['wan_interface']}):")
        print(f"  {notes_preview}")
    
    # Save updated CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/usr/local/bin/non_dsr_circuits_with_notes_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Updated export saved to: {output_file}")
    
    # Show statistics
    print(f"\nStatistics:")
    print(f"  Total circuits: {len(df)}")
    print(f"  Circuits with raw notes: {notes_found}")
    print(f"  Circuits without notes: {len(df) - notes_found}")
    
    # List sites without notes
    no_notes_sites = df[df['raw_notes'] == '']['site_name'].unique()
    if len(no_notes_sites) > 0:
        print(f"\nSites without notes in JSON ({len(no_notes_sites)} sites):")
        for site in no_notes_sites[:10]:
            print(f"  - {site}")
        if len(no_notes_sites) > 10:
            print(f"  ... and {len(no_notes_sites) - 10} more")
    
    return output_file

if __name__ == "__main__":
    add_raw_notes()