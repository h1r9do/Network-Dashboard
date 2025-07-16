#!/usr/bin/env python3
"""
Apply the provider mappings to the database and test the results
"""

import os
import sys
import subprocess
from datetime import datetime

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def run_sql_file(sql_file):
    """Execute SQL file against the database"""
    # Parse database URL
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    # Create .pgpass file for authentication
    pgpass_path = os.path.expanduser('~/.pgpass')
    pgpass_line = f"{host}:{port}:{database}:{user}:{password}\n"
    
    # Check if line already exists
    pgpass_exists = False
    if os.path.exists(pgpass_path):
        with open(pgpass_path, 'r') as f:
            if pgpass_line in f.read():
                pgpass_exists = True
    
    if not pgpass_exists:
        with open(pgpass_path, 'a') as f:
            f.write(pgpass_line)
        os.chmod(pgpass_path, 0o600)
    
    # Run psql command
    cmd = [
        'psql',
        '-h', host,
        '-p', port,
        '-U', user,
        '-d', database,
        '-f', sql_file
    ]
    
    print(f"Executing SQL file: {sql_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error executing SQL: {result.stderr}")
        return False
    
    print("SQL executed successfully!")
    return True

def main():
    print("=== Provider Mapping System Setup ===\n")
    
    # Step 1: Apply SQL schema
    sql_file = os.path.join(os.path.dirname(__file__), 'create_provider_mapping_table.sql')
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    print("Step 1: Creating provider_mappings table...")
    if not run_sql_file(sql_file):
        print("❌ Failed to create table")
        return
    
    print("✅ Table created successfully!\n")
    
    # Step 2: Test the enhanced matching
    print("Step 2: Testing enhanced provider matching...")
    
    # Import and run the enhanced matcher
    try:
        from enhanced_provider_matching import EnhancedProviderMatcher
        
        matcher = EnhancedProviderMatcher()
        matches, no_matches = matcher.test_matching()
        
        if not no_matches:
            print("\n🎉 SUCCESS! 100% provider matching achieved!")
        else:
            print(f"\n⚠️  Still have {len(no_matches)} unmatched providers")
            print("Review the suggestions above and add them to the mapping table")
            
    except Exception as e:
        print(f"❌ Error running enhanced matching: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Review any remaining no-match cases")
    print("2. Update the enrichment scripts to use the mapping table")
    print("3. Update the modal UI to use the mapping logic")
    print("\nMapping table documentation: PROVIDER_MAPPING_SYSTEM.md")

if __name__ == "__main__":
    main()