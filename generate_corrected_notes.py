#!/usr/bin/env python3
"""
Generate Corrected Notes JSON
Reads the enriched JSON from May 2nd restoration and creates formatted notes
"""

import json
import os
from datetime import datetime

# Configuration
ENRICHED_JSON_FILE = "/tmp/enriched_from_may2nd.json"
OUTPUT_FILE = "/tmp/corrected_notes.json"

def format_circuit_notes(wan1_data, wan2_data):
    """Format circuit data into Meraki device notes"""
    notes_lines = []
    
    # WAN1 formatting
    if wan1_data.get('provider') or wan1_data.get('speed'):
        notes_lines.append("WAN 1")
        if wan1_data.get('provider'):
            notes_lines.append(wan1_data['provider'])
        if wan1_data.get('speed'):
            notes_lines.append(wan1_data['speed'])
    
    # WAN2 formatting
    if wan2_data.get('provider') or wan2_data.get('speed'):
        notes_lines.append("WAN 2")
        if wan2_data.get('provider'):
            notes_lines.append(wan2_data['provider'])
        if wan2_data.get('speed'):
            notes_lines.append(wan2_data['speed'])
    
    return "\n".join(notes_lines) if notes_lines else ""

def main():
    """Main processing function"""
    print("🔄 Generating Corrected Notes JSON")
    print("=" * 60)
    
    # Validate input file
    if not os.path.exists(ENRICHED_JSON_FILE):
        print(f"❌ Enriched JSON file not found: {ENRICHED_JSON_FILE}")
        return
    
    # Load enriched data
    print(f"📊 Loading enriched data from: {ENRICHED_JSON_FILE}")
    with open(ENRICHED_JSON_FILE, 'r') as f:
        enriched_data = json.load(f)
    
    print(f"📊 Loaded {len(enriched_data)} sites")
    
    # Generate corrected notes for each site
    corrected_notes_data = []
    
    for site_data in enriched_data:
        network_name = site_data.get('network_name', '').strip()
        
        if not network_name:
            continue
        
        # Format the corrected notes
        wan1_data = site_data.get('wan1', {})
        wan2_data = site_data.get('wan2', {})
        corrected_notes = format_circuit_notes(wan1_data, wan2_data)
        
        # Create notes entry
        notes_entry = {
            "network_name": network_name,
            "corrected_notes": corrected_notes,
            "wan1": {
                "provider": wan1_data.get('provider', ''),
                "speed": wan1_data.get('speed', ''),
                "confirmed": wan1_data.get('confirmed', False)
            },
            "wan2": {
                "provider": wan2_data.get('provider', ''),
                "speed": wan2_data.get('speed', ''),
                "confirmed": wan2_data.get('confirmed', False)
            },
            "source": site_data.get('source', ''),
            "processed_at": datetime.now().isoformat()
        }
        
        corrected_notes_data.append(notes_entry)
    
    # Write output file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(corrected_notes_data, f, indent=2)
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"   Total sites processed: {len(corrected_notes_data)}")
    print(f"   Output written to: {OUTPUT_FILE}")
    
    # Show some examples
    print(f"\n📝 Sample corrected notes:")
    for i, entry in enumerate(corrected_notes_data[:5]):
        network_name = entry['network_name']
        notes = entry['corrected_notes']
        if notes:
            print(f"   {network_name}: {repr(notes)}")
        else:
            print(f"   {network_name}: (empty notes)")
    
    # Count sites with notes vs empty
    sites_with_notes = sum(1 for entry in corrected_notes_data if entry['corrected_notes'])
    sites_without_notes = len(corrected_notes_data) - sites_with_notes
    
    print(f"\n📊 Notes Statistics:")
    print(f"   Sites with corrected notes: {sites_with_notes}")
    print(f"   Sites with empty notes: {sites_without_notes}")
    
    print(f"\n✅ Corrected notes JSON generated successfully!")

if __name__ == "__main__":
    main()