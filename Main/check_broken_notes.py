#!/usr/bin/env python3
"""
Check Meraki device notes for sites pushed in the past 24 hours
"""
import os
import json
import requests
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
DATABASE_URI = 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits'

# Sites identified from logs
SITES_TO_CHECK = [
    'ALB 01', 'AZK 01', 'AZN 06', 'AZP_00', 'AZP 05', 'AZP 44', 'AZP 63',
    'CAL 29', 'CAN 22', 'COD 22', 'COD 28', 'FLT 01', 'ILC 31', 'ILP 01',
    'MNM 01', 'MNM 31', 'NMA 05', 'PAP 02', 'WYO 03'
]

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def get_device_notes():
    """Get device notes for all sites"""
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    results = []
    
    for site in SITES_TO_CHECK:
        # Get device serial from database
        cursor.execute("""
            SELECT device_serial, device_model, network_name
            FROM meraki_inventory
            WHERE LOWER(network_name) = LOWER(%s)
            AND device_model LIKE 'MX%%'
            LIMIT 1
        """, (site,))
        
        device = cursor.fetchone()
        if not device:
            results.append({
                'site': site,
                'error': 'No MX device found',
                'notes': None,
                'has_broken_format': None
            })
            continue
        
        # Get device details from Meraki API
        try:
            url = f"{BASE_URL}/devices/{device[0]}"
            response = requests.get(url, headers=get_headers(), timeout=30)
            response.raise_for_status()
            device_data = response.json()
            
            notes = device_data.get('notes', '')
            # Check if notes have literal \n
            has_broken_format = '\\n' in notes if notes else False
                
            results.append({
                'site': site,
                'serial': device[0],
                'model': device[1],
                'notes': notes,
                'has_broken_format': has_broken_format,
                'notes_preview': notes.replace('\\n', ' | ') if notes else '',
                'error': None
            })
                
            print(f"✓ {site}: {'BROKEN' if has_broken_format else 'OK'}")
            
        except Exception as e:
            results.append({
                'site': site,
                'serial': device[0] if device else None,
                'error': str(e),
                'notes': None,
                'has_broken_format': None
            })
            print(f"✗ {site}: Error - {e}")
    
    cursor.close()
    conn.close()
    
    return results

def main():
    """Main function"""
    print("Checking Meraki device notes for sites pushed in past 24 hours...")
    print(f"Total sites to check: {len(SITES_TO_CHECK)}")
    print("-" * 50)
    
    # Get all device notes
    results = get_device_notes()
    
    # Count broken vs fixed
    broken_count = sum(1 for r in results if r.get('has_broken_format') == True)
    fixed_count = sum(1 for r in results if r.get('has_broken_format') == False)
    error_count = sum(1 for r in results if r.get('error') and 'No MX device' not in r.get('error', ''))
    no_device_count = sum(1 for r in results if r.get('error') and 'No MX device' in r.get('error'))
    
    # Save to JSON file
    output_file = '/usr/local/bin/Main/meraki_notes_check_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_sites': len(SITES_TO_CHECK),
                'broken_format': broken_count,
                'correct_format': fixed_count,
                'errors': error_count,
                'no_mx_device': no_device_count
            },
            'sites': results
        }, f, indent=2)
    
    print("-" * 50)
    print(f"Summary:")
    print(f"  - Total sites checked: {len(SITES_TO_CHECK)}")
    print(f"  - Broken format (has \\n): {broken_count}")
    print(f"  - Correct format: {fixed_count}")
    print(f"  - API errors: {error_count}")
    print(f"  - No MX device: {no_device_count}")
    print(f"\nResults saved to: {output_file}")
    
    # Show broken sites
    if broken_count > 0:
        print(f"\nSites with broken formatting:")
        for r in results:
            if r.get('has_broken_format'):
                print(f"  - {r['site']}: {r.get('notes_preview', '')}")

if __name__ == "__main__":
    main()