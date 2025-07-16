#!/usr/bin/env python3
"""
Test fix on just a few sites first
"""

import os
import json
import requests
import psycopg2
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
LIVE_DATA_FILE = "/tmp/live_meraki_all_except_55.json"

# Import functions from main script
from fix_all_notes_and_arin import normalize_provider, reformat_speed, is_valid_arin_provider, determine_final_provider_and_speed, format_notes_with_newlines

def main():
    """Test fix on AZP 08 and a few other sites"""
    print("🧪 Testing Fix on Few Sites")
    print("=" * 60)
    
    # Load live data
    with open(LIVE_DATA_FILE, 'r') as f:
        live_data = json.load(f)
    
    # Test sites
    test_sites = ['AZP 08', 'TXS 31', 'TNK 03']  # Include a Starlink site
    test_data = [site for site in live_data if site['network_name'] in test_sites]
    
    if not test_data:
        print("❌ Test sites not found in live data")
        return
    
    print(f"📊 Testing on {len(test_data)} sites")
    
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    for site_data in test_data:
        network_name = site_data['network_name']
        print(f"\n🔄 Processing {network_name}:")
        
        # Determine providers and speeds
        wan1_data = site_data['wan1']
        wan2_data = site_data['wan2']
        
        wan1_provider, wan1_speed = determine_final_provider_and_speed(
            wan1_data.get('dsr_match'),
            wan1_data.get('arin_provider')
        )
        
        wan2_provider, wan2_speed = determine_final_provider_and_speed(
            wan2_data.get('dsr_match'),
            wan2_data.get('arin_provider')
        )
        
        # Format notes
        corrected_notes = format_notes_with_newlines(wan1_provider, wan1_speed, wan2_provider, wan2_speed)
        
        print(f"   WAN1: {wan1_provider} / {wan1_speed}")
        print(f"   WAN2: {wan2_provider} / {wan2_speed}")
        print(f"\n   Notes to apply:")
        print("   " + "-" * 40)
        print(corrected_notes)
        print("   " + "-" * 40)
        print(f"   Raw: {repr(corrected_notes)}")
        
        # Update database only
        cursor.execute("""
            UPDATE meraki_inventory 
            SET device_notes = %s,
                wan1_arin_provider = %s,
                wan2_arin_provider = %s,
                last_updated = %s
            WHERE network_name = %s
        """, (
            corrected_notes,
            wan1_data.get('arin_provider', 'Unknown'),
            wan2_data.get('arin_provider', 'Unknown'),
            datetime.now(),
            network_name
        ))
        
        print(f"   ✅ Updated database")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Test completed on {len(test_data)} sites")
    print("\n📝 Next step: Run full fix script if test looks good")

if __name__ == "__main__":
    main()