#!/usr/bin/env python3
"""
Comprehensive verification that web page matches CSV exactly
"""
import csv
import requests
from bs4 import BeautifulSoup
import sys

def extract_web_data():
    """Extract table data from web page"""
    url = "http://neamsatcor1ld01.trtc.com:5053/final/inventory-summary"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the datacenter table
    table = soup.find('table', {'id': 'datacenterTable'})
    if not table:
        print("ERROR: Could not find datacenterTable")
        return []
    
    # Extract all rows
    rows = []
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            row_data = []
            for td in tr.find_all('td'):
                text = td.get_text(strip=True)
                row_data.append(text)
            if row_data:  # Skip empty rows
                rows.append(row_data)
    
    return rows

def read_csv_data():
    """Read CSV file data"""
    csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
    rows = []
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            rows.append(row)
    
    return rows

def compare_data():
    """Compare CSV and web data line by line"""
    print("Reading CSV data...")
    csv_rows = read_csv_data()
    print(f"CSV rows: {len(csv_rows)}")
    
    print("\nExtracting web page data...")
    web_rows = extract_web_data()
    print(f"Web rows: {len(web_rows)}")
    
    if len(csv_rows) != len(web_rows):
        print(f"\nERROR: Row count mismatch! CSV: {len(csv_rows)}, Web: {len(web_rows)}")
        return False
    
    print("\nComparing data line by line...")
    mismatches = 0
    
    for i, (csv_row, web_row) in enumerate(zip(csv_rows, web_rows)):
        # Compare each field
        if len(csv_row) != len(web_row):
            print(f"\nRow {i+1}: Column count mismatch! CSV: {len(csv_row)}, Web: {len(web_row)}")
            mismatches += 1
            continue
        
        for j, (csv_val, web_val) in enumerate(zip(csv_row, web_row)):
            if csv_val != web_val:
                print(f"\nRow {i+1}, Column {j+1} mismatch:")
                print(f"  CSV: '{csv_val}'")
                print(f"  Web: '{web_val}'")
                mismatches += 1
                
                # Show context
                if i < 5:
                    print(f"  Full CSV row: {csv_row}")
                    print(f"  Full Web row: {web_row}")
    
    if mismatches == 0:
        print("\n✓ PERFECT MATCH! All data matches exactly.")
        
        # Additional verification
        print("\nAdditional checks:")
        
        # Check specific examples
        print("\nChecking specific devices:")
        for device in ['AL-3130-R16-Enc1-A', 'MDF-3130-I9-StackA', 'FEX-105']:
            csv_found = any(device in str(row) for row in csv_rows)
            web_found = any(device in str(row) for row in web_rows)
            print(f"  {device}: CSV={csv_found}, Web={web_found}")
        
        # Count empty cells in first two columns
        csv_empty = sum(1 for row in csv_rows if row[0] == '' and row[1] == '')
        web_empty = sum(1 for row in web_rows if row[0] == '' and row[1] == '')
        print(f"\nEmpty hostname/IP rows: CSV={csv_empty}, Web={web_empty}")
        
        return True
    else:
        print(f"\n✗ MISMATCH! Found {mismatches} differences.")
        return False

if __name__ == "__main__":
    print("=== CSV vs Web Page Verification ===\n")
    result = compare_data()
    sys.exit(0 if result else 1)