#!/usr/bin/env python3
"""
Enhanced Nightly DSR Pull Script with Manual Override Support
Downloads tracking data from DSR Global and updates database while respecting manual overrides
"""

import os
import sys
import requests
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# from update_circuits_from_tracking_with_override import update_circuits_from_csv
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dsr-pull-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_dsr_data():
    """Download tracking data from DSR Global portal"""
    logger.info("Starting DSR Global data download")
    
    # Initialize a session to persist cookies and headers
    session = requests.Session()
    
    try:
        # Step 1: Make a GET request to the login page to get the CSRF token and cookies
        login_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
        response = session.get(login_url)
        
        # Check if the page loaded successfully
        if response.status_code != 200:
            logger.error(f"Failed to load login page, status code {response.status_code}")
            return None
        
        # Step 2: Parse the HTML to extract the CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the CSRF token
        csrf_token = soup.find('input', {'name': '_token'})['value'] if soup.find('input', {'name': '_token'}) else None
        
        if not csrf_token:
            logger.error("CSRF token not found!")
            return None
        
        logger.info(f"CSRF Token obtained: {csrf_token[:10]}...")
        
        # Step 3: Prepare login data with email, password, and CSRF token
        email = "mike.bambic@discounttire.com"
        password = "Aud!o!987202078"
        
        # Prepare the data to send in the POST request
        login_data = {
            'email': email,
            'password': password,
            '_token': csrf_token
        }
        
        # Step 4: Submit the login form via a POST request
        login_post_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
        login_response = session.post(login_post_url, data=login_data)
        
        # Step 5: Check the login response and ensure we are redirected successfully
        if login_response.status_code == 200:
            logger.info("Login successful!")
            
            # Step 6: Go to the tracking page after login and request the CSV directly
            target_url = "https://discounttire.dsrglobal.net/tracking/overview.php?search_filter_term=none&search_display_term=all_orders&output=csvfile"
            tracking_page_response = session.get(target_url)
            
            if tracking_page_response.status_code == 200:
                logger.info("Successfully downloaded CSV data")
                
                # Step 7: Save the CSV content to a file
                current_date = datetime.now().strftime('%Y-%m-%d')
                csv_filename = f"/var/www/html/circuitinfo/tracking_data_{current_date}.csv"
                
                with open(csv_filename, mode='wb') as file:
                    file.write(tracking_page_response.content)
                
                logger.info(f"Data exported to {csv_filename}")
                
                # Step 8: Modify the file permissions and ownership
                os.chmod(csv_filename, 0o755)  # rwx for owner, rx for group and others
                os.chown(csv_filename, 65534, 65534)  # 'nobody' user and group
                
                logger.info(f"Permissions and ownership set for {csv_filename}")
                
                # Step 9: Update the CSV file - convert G to M
                try:
                    df = pd.read_csv(csv_filename, encoding='ISO-8859-1', low_memory=False)
                except UnicodeDecodeError:
                    df = pd.read_csv(csv_filename, encoding='ISO-8859-1')
                
                # Function to convert G to M by multiplying the number by 1000
                def convert_g_to_m(value):
                    value = str(value)
                    if 'G' in value:
                        value = re.sub(r'(\d+(\.\d+)?)G', lambda m: f"{float(m.group(1)) * 1000:.1f}M", value)
                    return value
                
                # Columns to process
                columns_to_process = ['details_service_speed', 'details_ordered_service_speed']
                
                # Apply the conversion function to the relevant columns
                for column in columns_to_process:
                    if column in df.columns:
                        df[column] = df[column].apply(convert_g_to_m)
                
                # Write the updated DataFrame back to the same CSV file
                df.to_csv(csv_filename, index=False)
                
                logger.info("CSV file updated successfully (G to M conversion)")
                
                return csv_filename
                
            else:
                logger.error(f"Failed to reach the target page, status code: {tracking_page_response.status_code}")
                return None
        else:
            logger.error(f"Login failed, status code: {login_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error during DSR data download: {e}")
        return None

def main():
    """Main function for nightly DSR pull with manual override support"""
    logger.info("=" * 60)
    logger.info("Starting nightly DSR pull with manual override support")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # Download DSR data
        csv_file = download_dsr_data()
        
        if csv_file:
            logger.info(f"Successfully downloaded DSR data to {csv_file}")
            
            # Update database with manual override protection
            logger.info("Updating database with manual override protection...")
            # Use subprocess to run the working update script
            result = subprocess.run(["python3", "/usr/local/bin/Main/nightly/update_circuits_from_tracking_with_logging.py", csv_file], capture_output=True, text=True)
            success = result.returncode == 0
            if not success:
                logger.error(f"Update script failed: {result.stderr}")
            
            if success:
                logger.info("Database update completed successfully")
                logger.info("Manual override protected circuits were not modified")
                
                # Verify all enabled circuits from CSV are in database
                logger.info("Verifying all enabled circuits were imported...")
                
                # Count enabled in CSV
                csv_count_cmd = f"grep -i ',enabled,' {csv_file} | wc -l"
                csv_count_result = subprocess.run(csv_count_cmd, shell=True, capture_output=True, text=True)
                csv_enabled_count = int(csv_count_result.stdout.strip()) if csv_count_result.returncode == 0 else 0
                
                # Count enabled in database
                db_count_cmd = "psql -U dsruser -d dsrcircuits -t -c \"SELECT COUNT(*) FROM circuits WHERE status = 'Enabled';\""
                db_count_result = subprocess.run(db_count_cmd, shell=True, capture_output=True, text=True)
                db_enabled_count = int(db_count_result.stdout.strip()) if db_count_result.returncode == 0 else 0
                
                logger.info(f"CSV enabled circuits: {csv_enabled_count}")
                logger.info(f"Database enabled circuits: {db_enabled_count}")
                
                if csv_enabled_count > db_enabled_count:
                    logger.warning(f"WARNING: Missing {csv_enabled_count - db_enabled_count} circuits in database!")
                    logger.warning("Some circuits from CSV were not imported. Please investigate.")
                    
                    # Check for sites with >2 circuits
                    check_cmd = """psql -U dsruser -d dsrcircuits -t -c "SELECT site_name || ': ' || COUNT(*) FROM circuits WHERE status = 'Enabled' GROUP BY site_name HAVING COUNT(*) > 2 ORDER BY COUNT(*) DESC;" """
                    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                    if check_result.returncode == 0 and check_result.stdout.strip():
                        logger.warning("Sites with >2 enabled circuits:")
                        logger.warning(check_result.stdout)
                else:
                    logger.info("✅ All circuits appear to be imported correctly")
                    
            else:
                logger.error("Database update failed")
                sys.exit(1)
        else:
            logger.error("Failed to download DSR data")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in nightly DSR pull: {e}")
        sys.exit(1)
    
    logger.info("Nightly DSR pull completed successfully")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()