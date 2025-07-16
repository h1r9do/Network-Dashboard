#!/usr/bin/env python3
"""
Analyze inventory display format differences between:
1. CSV file (inventory_ultimate_final.csv)
2. Database (inventory_web_format table)
3. API response (/api/inventory-datacenter)
4. Web page display
"""
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

def analyze_csv():
    """Analyze CSV file structure"""
    print("=== CSV FILE ANALYSIS ===")
    csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        # Get headers
        headers = reader.fieldnames
        print(f"CSV Headers: {headers}")
        
        # Analyze first 10 rows
        print("\nFirst 10 rows:")
        for i, row in enumerate(reader):
            if i >= 10:
                break
            print(f"\nRow {i+1}:")
            for key, value in row.items():
                if value:  # Only show non-empty values
                    print(f"  {key}: {value}")

def analyze_database():
    """Analyze database structure"""
    print("\n\n=== DATABASE ANALYSIS ===")
    
    db_config = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'dsruser'
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'inventory_web_format'
        ORDER BY ordinal_position
    """)
    
    print("Database columns:")
    for col in cursor.fetchall():
        print(f"  {col['column_name']}: {col['data_type']}")
    
    # Check sample data
    cursor.execute("""
        SELECT * FROM inventory_web_format 
        WHERE hostname LIKE 'AL-%' OR parent_hostname LIKE 'AL-%'
        LIMIT 10
    """)
    
    print("\nSample database records:")
    for i, row in enumerate(cursor.fetchall()):
        print(f"\nRecord {i+1}:")
        for key, value in row.items():
            if value and key not in ['id', 'created_at', 'updated_at']:
                print(f"  {key}: {value}")
    
    cursor.close()
    conn.close()

def analyze_api():
    """Analyze API response"""
    print("\n\n=== API RESPONSE ANALYSIS ===")
    
    response = requests.get('http://localhost:5052/api/inventory-datacenter')
    data = response.json()
    
    if 'inventory' in data:
        print(f"Total items: {len(data['inventory'])}")
        
        # Find items with actual data
        items_with_data = [item for item in data['inventory'] if any(v for k, v in item.items() if v and k != 'vendor')]
        
        print(f"Items with data: {len(items_with_data)}")
        
        # Show first few items with data
        print("\nFirst 5 items with data:")
        for i, item in enumerate(items_with_data[:5]):
            print(f"\nItem {i+1}:")
            for key, value in item.items():
                if value:
                    print(f"  {key}: {value}")

def compare_mappings():
    """Compare field mappings between sources"""
    print("\n\n=== FIELD MAPPING ANALYSIS ===")
    
    # Read CSV to understand structure
    csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Get a parent and child row
        parent_row = None
        child_row = None
        
        for row in reader:
            if row[0]:  # Has hostname
                parent_row = dict(zip(headers, row))
            elif not row[0] and parent_row:  # No hostname (child)
                child_row = dict(zip(headers, row))
                break
    
    print("CSV Parent Device:")
    for k, v in parent_row.items():
        if v:
            print(f"  {k}: {v}")
    
    print("\nCSV Child Component:")
    for k, v in child_row.items():
        if v:
            print(f"  {k}: {v}")
    
    # Check how this maps to the web display
    print("\n\nWEB DISPLAY COLUMNS (from template):")
    print("  1. Site")
    print("  2. Hostname")
    print("  3. Relationship")
    print("  4. IP Address")
    print("  5. Position")
    print("  6. Model")
    print("  7. Serial Number")
    print("  8. Port Location")
    print("  9. Vendor")
    print("  10. Notes")
    print("  11. End of Sale")
    print("  12. End of Life")
    
    print("\n\nKEY FINDINGS:")
    print("1. CSV has model data in 'model' column")
    print("2. Database is missing model data (empty model column)")
    print("3. Port location in CSV should map to database port_location")
    print("4. Parent-child relationship determined by hostname presence")
    print("5. Components (children) have empty hostname but have parent_hostname")

def check_import_issue():
    """Check the specific import issue"""
    print("\n\n=== IMPORT ISSUE ANALYSIS ===")
    
    print("Issue found in import_ultimate_final_inventory_to_db.py:")
    print("  Line 82: port_location is hardcoded as empty string ''")
    print("  Should be: port_location from CSV row")
    print("\nThis explains why port_location is empty in the database!")
    
    # Check if model data is properly imported
    db_config = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'dsruser'
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM inventory_web_format WHERE model != ''")
    model_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory_web_format")
    total_count = cursor.fetchone()[0]
    
    print(f"\nDatabase model field status:")
    print(f"  Total records: {total_count}")
    print(f"  Records with model data: {model_count}")
    print(f"  Records missing model: {total_count - model_count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_csv()
    analyze_database()
    analyze_api()
    compare_mappings()
    check_import_issue()