import openpyxl
import json

# Paths to your files
json_file_path = '/var/www/html/circuitinfo/master_list_data.json'  # JSON file path from the uploaded data
excel_file_path = '/usr/local/bin/Discount Tire Master Circuit List.xlsx'  # Excel file path

# Load the JSON data
with open(json_file_path, 'r') as json_file:
    json_data = json.load(json_file)

# Load the Excel workbook and select the Master List sheet
wb = openpyxl.load_workbook(excel_file_path)
master_list_sheet = wb['Master List']

# Define the column indices for easy reference
store_col = 1  # Column A - Store
vision_status_col = 7  # Column G - Vision Status
store_type_col = 5  # Column E - Store Category Current
region_col = 3  # Column C - Region
contract_signed_col = 12  # Column L - Circuit Contract Signed

# Extract the data from the Excel sheet into a list of dictionaries
excel_data = []

# Iterate over rows in the sheet, skipping the header row (row 1)
for row in master_list_sheet.iter_rows(min_row=2, values_only=True):
    store_info = {
        'store': row[store_col - 1],
        'vision_status': row[vision_status_col - 1],
        'store_type': row[store_type_col - 1],
        'region': row[region_col - 1],
        'contract_signed': row[contract_signed_col - 1] if row[contract_signed_col - 1] else False
    }
    excel_data.append(store_info)

# Compare the JSON and Excel data
discrepancies = []

# Compare data row by row
for json_store in json_data:
    matched = False
    for excel_store in excel_data:
        if json_store['store'] == excel_store['store']:
            # Check for discrepancies in the fields
            if json_store['vision_status'] != excel_store['vision_status']:
                discrepancies.append(f"Vision Status mismatch for {json_store['store']}: JSON='{json_store['vision_status']}', Excel='{excel_store['vision_status']}'")
            if json_store['store_type'] != excel_store['store_type']:
                discrepancies.append(f"Store Type mismatch for {json_store['store']}: JSON='{json_store['store_type']}', Excel='{excel_store['store_type']}'")
            if json_store['region'] != excel_store['region']:
                discrepancies.append(f"Region mismatch for {json_store['store']}: JSON='{json_store['region']}', Excel='{excel_store['region']}'")
            if json_store['contract_signed'] != excel_store['contract_signed']:
                discrepancies.append(f"Contract Signed mismatch for {json_store['store']}: JSON='{json_store['contract_signed']}', Excel='{excel_store['contract_signed']}'")
            matched = True
            break
    
    if not matched:
        discrepancies.append(f"Store not found in Excel: {json_store['store']}")

# Identify stores in the Excel data that are not in the JSON
for excel_store in excel_data:
    matched = False
    for json_store in json_data:
        if excel_store['store'] == json_store['store']:
            matched = True
            break
    if not matched:
        discrepancies.append(f"Store not found in JSON: {excel_store['store']}")

# Print out discrepancies
if discrepancies:
    print("Discrepancies found:")
    for discrepancy in discrepancies:
        print(discrepancy)
else:
    print("No discrepancies found!")

# Close the workbook
wb.close()
