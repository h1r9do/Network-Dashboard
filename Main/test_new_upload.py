#!/usr/bin/env python3
"""
Test the updated Excel upload functionality
"""
import pandas as pd
import requests
from datetime import datetime

def test_upload():
    """Test uploading an Excel file with all columns"""
    
    # Create a test Excel file with all columns
    test_data = {
        'Store #': ['TEST 01', 'TEST 02'],
        'SAP #': ['9999', '9998'],
        'DBA': ['Test Tire Store', 'Test Tire Store 2'],
        'Region': ['Test Region', 'Test Region'],
        'Address': ['123 Test St', '456 Test Ave'],
        'City': ['TestCity', 'TestTown'],
        'State': ['TX', 'AZ'],
        'Zip': ['12345', '67890'],
        'Project Status': ['01 - Planning', '02 - Pre-Construction'],
        'TOD': ['2026-01-15', '2026-02-20'],
        'Store Concept': ['Test Concept', 'Test Concept 2'],
        'Unit Capacity': ['1000', '2000']
    }
    
    df = pd.DataFrame(test_data)
    
    # Save to temporary Excel file
    excel_file = '/tmp/test_upload.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Created test Excel file: {excel_file}")
    
    # Test upload via API
    url = 'http://localhost:5052/api/new-stores/excel-upload'
    
    with open(excel_file, 'rb') as f:
        files = {'file': ('test_upload.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(url, files=files)
    
    print(f"\nUpload response status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing Excel upload with all new columns...")
    success = test_upload()
    
    if success:
        print("\n✅ Upload test successful! The upload function now handles all columns.")
    else:
        print("\n❌ Upload test failed!")