import pandas as pd
import re
from datetime import datetime

# Get today's date in YYYY-MM-DD format for the file path
today_date = datetime.now().strftime('%Y-%m-%d')

# Define the path to the CSV file
csv_file_path = f'/var/www/html/circuitinfo/tracking_data_{today_date}.csv'

# Attempt to read the CSV file with a different encoding
try:
    df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')
except UnicodeDecodeError:
    # If a UnicodeDecodeError occurs, try with a different encoding
    df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')

# Function to convert G to M by multiplying the number by 1000
def convert_g_to_m(value):
    # Ensure the value is a string
    value = str(value)
    
    # Check if the value contains 'G'
    if 'G' in value:
        # Extract the numeric part before the 'G' and multiply by 1000
        value = re.sub(r'(\d+(\.\d+)?)G', lambda m: f"{float(m.group(1)) * 1000:.1f}M", value)
    return value

# Only process the two specific columns
columns_to_process = ['details_service_speed', 'details_ordered_service_speed']

# Apply the conversion function to the relevant columns
for column in columns_to_process:
    if column in df.columns:
        df[column] = df[column].apply(convert_g_to_m)

# Write the updated DataFrame back to the same CSV file
df.to_csv(csv_file_path, index=False)

print("CSV file updated successfully.")
