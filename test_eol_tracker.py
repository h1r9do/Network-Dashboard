#!/usr/bin/env python3
"""
Test script for EOL tracker - Run this to verify everything is working
"""

import os
import sys
import subprocess

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = ['PyPDF2', 'beautifulsoup4', 'requests', 'psycopg2']
    
    print("Checking dependencies...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is not installed. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {package}: {e}")
                return False
    
    return True

def test_eol_database():
    """Test EOL database functionality"""
    try:
        from meraki_eol_tracker import get_db_connection, create_eol_table
        
        print("\nTesting database connection...")
        conn = get_db_connection()
        print("✓ Database connection successful")
        
        print("\nCreating EOL tables...")
        create_eol_table(conn)
        print("✓ EOL tables created/verified")
        
        # Check if we can query the table
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meraki_eol")
        count = cursor.fetchone()[0]
        print(f"✓ EOL table exists with {count} records")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_eol_tracker():
    """Run a quick test of the EOL tracker"""
    try:
        print("\nRunning EOL tracker test...")
        
        # Import and run specific functions
        from meraki_eol_tracker import (
            get_db_connection, 
            process_eol_csv, 
            generate_eol_summary
        )
        
        conn = get_db_connection()
        
        print("\nProcessing EOL CSV...")
        result = process_eol_csv(conn)
        if result:
            print("✓ CSV processing successful")
        else:
            print("✓ CSV unchanged or already processed")
        
        print("\nGenerating summary...")
        generate_eol_summary(conn)
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ EOL tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("EOL Tracker Test Suite")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n✗ Dependency check failed")
        return 1
    
    # Test database
    if not test_eol_database():
        print("\n✗ Database test failed")
        return 1
    
    # Test EOL tracker
    if not test_eol_tracker():
        print("\n✗ EOL tracker test failed")
        return 1
    
    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("\nYou can now run the full EOL tracker with:")
    print("  python3 /usr/local/bin/Main/meraki_eol_tracker.py")
    print("\nAnd the enhanced inventory script with:")
    print("  python3 /usr/local/bin/Main/nightly_inventory_db_enhanced.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())