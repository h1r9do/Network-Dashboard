import os
import requests
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Initialize a session to persist cookies and headers
session = requests.Session()

# Step 1: Make a GET request to the login page to get the CSRF token and cookies
login_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
response = session.get(login_url)

# Check if the page loaded successfully
if response.status_code != 200:
    print(f"Failed to load login page, status code {response.status_code}")
    exit()

# Step 2: Parse the HTML to extract the CSRF token
soup = BeautifulSoup(response.text, 'html.parser')

# Find the CSRF token
csrf_token = soup.find('input', {'name': '_token'})['value'] if soup.find('input', {'name': '_token'}) else None

if not csrf_token:
    print("CSRF token not found!")
    exit()

print(f"CSRF Token: {csrf_token}")

# Step 3: Prepare login data with email, password, and CSRF token
email = "mike.bambic@discounttire.com"
password = "Aud!o!987202078"

# Prepare the data to send in the POST request
login_data = {
    'email': email,
    'password': password,
    '_token': csrf_token
}

# Step 4: Submit the login form via a POST request with the email, password, and CSRF token
login_post_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
login_response = session.post(login_post_url, data=login_data)

# Step 5: Check the login response and ensure we are redirected successfully
if login_response.status_code == 200:
    print("Login successful!")
    # Step 6: Go to the tracking page after login and request the CSV directly
    target_url = "https://discounttire.dsrglobal.net/tracking/overview.php?search_filter_term=none&search_display_term=all_orders&output=csvfile"
    tracking_page_response = session.get(target_url)

    if tracking_page_response.status_code == 200:
        print("Successfully navigated to the tracking overview page and downloaded the CSV.")
        
        # Step 7: Save the CSV content to a file
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get the current date in YYYY-MM-DD format
        csv_filename = f"/var/www/html/circuitinfo/tracking_data_{current_date}.csv"
        
        with open(csv_filename, mode='wb') as file:  # Use 'wb' mode to write the binary response
            file.write(tracking_page_response.content)
        
        print(f"Data exported to {csv_filename}")

        # Step 8: Modify the file permissions and ownership
        os.chmod(csv_filename, 0o755)  # rwx for owner, rx for group and others
        os.chown(csv_filename, 65534, 65534)  # 'nobody' user and group, UID and GID may vary on your system
        
        print(f"Permissions and ownership set for {csv_filename}")

        # Step 9: Update the CSV file using the logic from updatevalues.py
        try:
            df = pd.read_csv(csv_filename, encoding='ISO-8859-1', low_memory=False)
        except UnicodeDecodeError:
            # If a UnicodeDecodeError occurs, try with a different encoding
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

        print("CSV file updated successfully.")

    else:
        print(f"Failed to reach the target page, status code: {tracking_page_response.status_code}")
else:
    print(f"Login failed, status code {login_response.status_code}")
