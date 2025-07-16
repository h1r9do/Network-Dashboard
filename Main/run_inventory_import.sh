#!/bin/bash
# Script to run the inventory import process

echo "=== Inventory Import Process ==="
echo

# Step 1: Clean database (optional)
read -p "Do you want to clean the existing inventory data? (yes/no): " clean_db
if [ "$clean_db" == "yes" ]; then
    echo "Cleaning database..."
    python3 /usr/local/bin/Main/clean_inventory_database.py
    echo
fi

# Step 2: Generate consolidated data if needed
if [ ! -f "/usr/local/bin/Main/physical_inventory_consolidated.json" ]; then
    echo "Generating consolidated inventory data..."
    python3 /usr/local/bin/Main/consolidate_vdc_devices.py
    echo
fi

# Step 3: Generate final CSV if needed
if [ ! -f "/usr/local/bin/Main/inventory_ultimate_final.csv" ]; then
    echo "Generating final CSV..."
    python3 /usr/local/bin/Main/generate_ultimate_final_csv.py
    echo
fi

# Step 4: Import to database
echo "Importing consolidated inventory to database..."
python3 /usr/local/bin/Main/import_consolidated_inventory.py

echo
echo "=== Import Complete ==="
echo
echo "The nightly script is ready to use:"
echo "  /usr/local/bin/Main/nightly_snmp_inventory_consolidated.py"
echo
echo "To test the nightly script on a few devices:"
echo "  python3 /usr/local/bin/Main/nightly_snmp_inventory_consolidated.py --test"