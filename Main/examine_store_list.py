#!/usr/bin/env python3
"""
Examine the store list CSV file to understand its structure
"""
import pandas as pd
import sys

def examine_store_list():
    """Examine the store list CSV file"""
    file_path = "/var/www/html/meraki-data/store-list (4).csv"
    
    print(f"Examining: {file_path}\n")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n")
        
        print("Columns in the CSV file:")
        print("-" * 50)
        for i, col in enumerate(df.columns, 1):
            # Show column name and first non-null value
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample = non_null.iloc[0]
                # Truncate long values
                if isinstance(sample, str) and len(sample) > 50:
                    sample = sample[:50] + "..."
            else:
                sample = "All values are null"
            print(f"{i}. {col}")
            print(f"   Sample value: {sample}")
            print(f"   Non-null count: {len(non_null)}/{len(df)}")
            print()
        
        # Show first 5 rows
        print("\nFirst 5 rows:")
        print("=" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        print(df.head())
        
        # Look for store ID/site name column
        print("\n\nLooking for Store ID/Site Name column:")
        print("-" * 50)
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['store', 'site', 'id', 'number']):
                print(f"Found potential match: '{col}'")
                # Show some sample values
                samples = df[col].dropna().head(5).tolist()
                print(f"  Sample values: {samples}")
        
        # Look for address columns
        print("\n\nLooking for Address-related columns:")
        print("-" * 50)
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['address', 'street', 'city', 'state', 'zip', 'postal']):
                print(f"Found: '{col}'")
                non_null_count = df[col].notna().sum()
                print(f"  Non-null values: {non_null_count}/{len(df)}")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_store_list()