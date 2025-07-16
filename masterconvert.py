import openpyxl
import json
import os

# Path to your Excel file
file_path = '/usr/local/bin/Discount Tire Master Circuit List.xlsx'

# Define the output JSON file path
json_file_path = '/var/www/html/circuitinfo/master_list_data.json'

# Load the Excel workbook
wb = openpyxl.load_workbook(file_path)

# Select the Master List sheet
master_list_sheet = wb['Master List']

# List to store the formatted data
master_list_data = []

# Define column indices based on your data layout
# Adjust based on your actual sheet's columns
store_col = 1  # Column A - Store
vision_status_col = 7  # Column G - Vision Status
store_type_col = 5  # Column E - Store Category Current
region_col = 3  # Column C - Region
contract_signed_col = 12  # Column L - Circuit Contract Signed

# Iterate over rows in the sheet, skipping the header row (row 1)
for row in master_list_sheet.iter_rows(min_row=2, values_only=True):
    store_info = {
        'store': row[store_col - 1],  # Adjusted for 0-indexed tuple
        'vision_status': row[vision_status_col - 1],
        'store_type': row[store_type_col - 1],
        'region': row[region_col - 1],
        'contract_signed': row[contract_signed_col - 1] if row[contract_signed_col - 1] else False
    }
    master_list_data.append(store_info)

# Save the data to the JSON file
try:
    with open(json_file_path, 'w') as json_file:
        json.dump(master_list_data, json_file, indent=4)
    print(f"Master List data successfully saved to {json_file_path}")
except Exception as e:
    print(f"Error saving Master List data: {e}")

# Close the workbook
wb.close()
