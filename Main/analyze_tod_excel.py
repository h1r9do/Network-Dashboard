#!/usr/bin/env python3
"""
Analyze the Targeted Opening Dates Excel file to understand its structure
"""
import pandas as pd
import sys

def analyze_excel(file_path):
    """Analyze Excel file structure"""
    print(f"Analyzing: {file_path}\n")
    
    try:
        # Read Excel file - the headers are in row 4 (0-indexed row 3)
        df = pd.read_excel(file_path, skiprows=3)
        
        # The first row contains the actual headers, so let's set them
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)
        
        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n")
        
        print("Columns in the Excel file:")
        print("-" * 50)
        for i, col in enumerate(df.columns, 1):
            # Show column name and first non-null value
            non_null = df[col].dropna()
            sample = non_null.iloc[0] if len(non_null) > 0 else "All values are null"
            print(f"{i}. {col}")
            print(f"   Sample value: {sample}")
            print(f"   Non-null count: {len(non_null)}/{len(df)}")
            print()
        
        # Show first 5 rows
        print("\nFirst 5 rows:")
        print("=" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 20)
        print(df.head())
        
        # Check for specific expected columns based on user's list
        expected_columns = [
            'Store #', 'SAP #', 'DBA', 'Region', 'Address', 
            'City', 'State', 'Zip', 'Project Status', 'TOD', 
            'Store Concept', 'Unit Capacity'
        ]
        
        print("\n\nChecking for expected columns:")
        print("-" * 50)
        for expected in expected_columns:
            found = False
            for col in df.columns:
                if expected.lower() in col.lower():
                    print(f"✓ {expected} → found as '{col}'")
                    found = True
                    break
            if not found:
                print(f"✗ {expected} → NOT FOUND")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

if __name__ == "__main__":
    file_path = "/var/www/html/meraki-data/RE - Targeted Opening Dates - 20250702.xlsx"
    analyze_excel(file_path)