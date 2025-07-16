#!/usr/bin/env python3
"""
Update the nightly_inventory_db.py to use the enhanced EOL table
This replaces the fetch_eol_data() function with database lookups
"""

import os
import shutil
from datetime import datetime

# Backup the original file
original_file = "/usr/local/bin/Main/nightly_inventory_db.py"
backup_file = f"{original_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print(f"Creating backup: {backup_file}")
shutil.copy2(original_file, backup_file)

# Read the original file
with open(original_file, 'r') as f:
    content = f.read()

# Replace the fetch_eol_data function with one that uses the database
new_fetch_eol = '''def fetch_eol_data():
    """Fetch End-of-Life data from enhanced EOL table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all EOL data from enhanced table
        cursor.execute("""
            SELECT model, announcement_date, end_of_sale, end_of_support
            FROM meraki_eol_enhanced
            ORDER BY model
        """)
        
        eol_lookup = {}
        for model, ann_date, eos_date, eol_date in cursor.fetchall():
            eol_lookup[model] = {
                "Announcement Date": ann_date.strftime('%B %d, %Y') if ann_date else "",
                "End-of-Sale Date": eos_date.strftime('%B %d, %Y') if eos_date else "",
                "End-of-Support Date": eol_date.strftime('%B %d, %Y') if eol_date else ""
            }
        
        cursor.close()
        conn.close()
        
        logger.info(f"Loaded EOL data for {len(eol_lookup)} models from database")
        return eol_lookup
        
    except Exception as e:
        logger.error(f"Error fetching EOL data from database: {e}")
        # Fall back to HTML parsing if database fails
        return fetch_eol_data_html()

def fetch_eol_data_html():
    """Original HTML-based EOL data fetching as fallback"""'''

# Find the start of the fetch_eol_data function
start_idx = content.find("def fetch_eol_data():")
if start_idx == -1:
    print("Error: Could not find fetch_eol_data function")
    exit(1)

# Find the end of the function (next def at the same indentation level)
end_idx = content.find("\ndef ", start_idx + 1)
if end_idx == -1:
    # If no next function, take to end of file
    end_idx = len(content)

# Extract the original function
original_func = content[start_idx:end_idx]

# Replace the function
new_content = content[:start_idx] + new_fetch_eol + original_func.replace("def fetch_eol_data():", "def fetch_eol_data_html():") + content[end_idx:]

# Also update the get_eol function to handle base model matching
new_get_eol = '''def get_eol(model, field, eol_lookup):
    """Get EOL data for a model with enhanced matching"""
    model = normalize_model(model)
    
    # Direct match
    if model in eol_lookup:
        return eol_lookup[model].get(field, "")
    
    # For MS220 variants, use base model
    if model.startswith("MS220-"):
        # Extract base model (MS220-8P -> MS220-8)
        base_match = re.match(r'(MS220-\d+)', model)
        if base_match:
            base_model = base_match.group(1)
            if base_model in eol_lookup:
                return eol_lookup[base_model].get(field, "")
    
    # Check if model starts with any known EOL model
    for key in eol_lookup:
        if model.startswith(key):
            return eol_lookup[key].get(field, "")
    
    return ""'''

# Find and replace get_eol function
get_eol_start = new_content.find("def get_eol(")
if get_eol_start != -1:
    get_eol_end = new_content.find("\ndef ", get_eol_start + 1)
    if get_eol_end == -1:
        get_eol_end = len(new_content)
    new_content = new_content[:get_eol_start] + new_get_eol + new_content[get_eol_end:]

# Write the updated file
with open(original_file, 'w') as f:
    f.write(new_content)

print("Updated nightly_inventory_db.py to use enhanced EOL data from database")
print("\nKey changes:")
print("1. fetch_eol_data() now reads from meraki_eol_enhanced table")
print("2. Original HTML parsing kept as fetch_eol_data_html() fallback")
print("3. get_eol() function enhanced to handle MS220 base model matching")
print("\nTo run the enhanced EOL tracking:")
print("  python3 /usr/local/bin/Main/enhanced_eol_tracker.py")
print("\nTo run inventory update:")
print("  python3 /usr/local/bin/Main/nightly_inventory_db.py")