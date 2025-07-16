#!/usr/bin/env python3
"""
Parse Discount Tire Master Circuit List Excel file
Extract columns A, Q, R, S, T, U, V, W, X
Convert to JSON using row 1 headers as field names
"""

import pandas as pd
import json
import os
from datetime import datetime

# File paths
EXCEL_FILE = "/var/www/html/circuitinfo/Discount Tire Master Circuit List.xlsx"
OUTPUT_JSON = f"/var/www/html/circuitinfo/master_circuit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def main():
    print(f"\n{'='*80}")
    print(f"Parsing Master Circuit List - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Read Excel file - specifically the "Master List" sheet
        print(f"Reading Excel file: {EXCEL_FILE}")
        df = pd.read_excel(EXCEL_FILE, sheet_name="Master List")
        
        # Get column letters A, Q-X (0, 16-23 in 0-based index)
        columns_to_extract = [0] + list(range(16, 24))  # A=0, Q=16, R=17...X=23
        
        # Get column names from row 1 (which is row 0 in pandas)
        selected_columns = df.columns[columns_to_extract].tolist()
        
        print(f"\nExtracted columns:")
        for i, col in enumerate(selected_columns):
            col_letter = 'A' if i == 0 else chr(ord('Q') + i - 1)
            print(f"  Column {col_letter}: {col}")
        
        # Extract only the selected columns
        df_selected = df.iloc[:, columns_to_extract]
        
        # Convert to records (list of dicts)
        records = df_selected.to_dict('records')
        
        # Clean up the data - convert NaN to None for better JSON
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = None
                elif isinstance(value, pd.Timestamp):
                    cleaned_record[key] = value.strftime('%Y-%m-%d')
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        
        # Write to JSON file
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(cleaned_records, f, indent=2)
        
        print(f"\n✅ Successfully created JSON file:")
        print(f"   {OUTPUT_JSON}")
        print(f"   Total records: {len(cleaned_records)}")
        
        # Show sample of first record
        if cleaned_records:
            print(f"\nSample record:")
            sample = cleaned_records[0]
            for key, value in sample.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)