import requests
import pandas as pd
import re
from datetime import datetime
import os
import difflib
from bs4 import BeautifulSoup

# --- Pull data using the dsr-pull.py logic ---

# Initialize a session to persist cookies and headers
session = requests.Session()

login_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
response = session.get(login_url)

if response.status_code != 200:
    print(f"Failed to load login page, status code {response.status_code}")
    exit()

# Extract CSRF token
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': '_token'})['value'] if soup.find('input', {'name': '_token'}) else None

if not csrf_token:
    print("CSRF token not found!")
    exit()

email = "mike.bambic@discounttire.com"
password = "Aud!o!987202078"

login_data = {'email': email, 'password': password, '_token': csrf_token}
login_post_url = "https://login.dsrglobal.net/auth/login/eW91bGwgbmV2ZXIgc2VlIHRoaXMgY29taW5nMTE0"
login_response = session.post(login_post_url, data=login_data)

if login_response.status_code == 200:
    target_url = "https://discounttire.dsrglobal.net/tracking/overview.php?search_filter_term=none&search_display_term=all_orders&output=csvfile"
    tracking_page_response = session.get(target_url)

    if tracking_page_response.status_code == 200:
        current_date = datetime.now().strftime('%Y-%m-%d')
        csv_filename = f"/var/www/html/circuitinfo/tracking_data_{current_date}.csv"

        with open(csv_filename, mode='wb') as file:
            file.write(tracking_page_response.content)
        print(f"Data exported to {csv_filename}")
    else:
        print(f"Failed to reach the target page, status code: {tracking_page_response.status_code}")
else:
    print(f"Login failed, status code {login_response.status_code}")

# --- Clean the Data ---

# File path for today's CSV
today_date = datetime.now().strftime('%Y-%m-%d')
csv_file_path = f'/var/www/html/circuitinfo/tracking_data_{today_date}.csv'

# Read the CSV file
df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')

def convert_g_to_m(value):
    value = str(value)
    if 'G' in value:
        value = re.sub(r'(\d+(\.\d+)?)G', lambda m: f"{float(m.group(1)) * 1000:.1f}M", value)
    return value

columns_to_process = ['details_service_speed', 'details_ordered_service_speed']
for column in columns_to_process:
    if column in df.columns:
        df[column] = df[column].apply(convert_g_to_m)

# Save the cleaned data back to the same CSV
df.to_csv(csv_file_path, index=False)

print("CSV file updated successfully.")

# --- Create Diff File ---

# Compare with the previous day's file
previous_day_date = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
previous_csv_path = f'/var/www/html/circuitinfo/tracking_data_{previous_day_date}.csv'

if os.path.exists(previous_csv_path):
    prev_df = pd.read_csv(previous_csv_path, encoding='ISO-8859-1')
    
    diff = difflib.unified_diff(
        prev_df.to_string().splitlines(),
        df.to_string().splitlines(),
        fromfile=previous_csv_path,
        tofile=csv_file_path,
    )

    # Save the diff to a file
    diff_file_path = f"/var/www/html/circuitinfo/diff_{today_date}.txt"
    with open(diff_file_path, 'w') as diff_file:
        diff_file.writelines(diff)

    print(f"Diff file created at {diff_file_path}")
else:
    print(f"No previous data to compare with for {previous_day_date}")

# --- Web Page Updates (dsrhistory.html) ---

# Example of adding a new page `dsrhistory.html` for viewing the diffs
html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Historical Data Comparison</title>
</head>
<body>
    <h1>Data Changes History</h1>
    <h3>Select a Date for Comparison</h3>
    <form action="dsrhistory.html" method="get">
        <input type="date" name="date" />
        <input type="submit" value="Compare" />
    </form>
    <div id="diffContent">
        <!-- Diff content will be shown here -->
        {% if diff_file %}
        <pre>{{ diff_file }}</pre>
        {% else %}
        <p>No changes found for the selected date.</p>
        {% endif %}
    </div>
</body>
</html>
'''

# Save this content to `dsrhistory.html` for serving
with open('/var/www/html/dsrhistory.html', 'w') as file:
    file.write(html_content)

print("dsrhistory.html page created successfully.")
