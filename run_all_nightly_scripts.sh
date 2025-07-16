#!/bin/bash
# Run all nightly scripts in order

echo "Starting all nightly scripts at $(date)"
echo "========================================"

# 1. DSR Pull (Midnight)
echo -e "\n[1/6] Running DSR Pull with Override Protection..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_dsr_pull_db_with_override.py
echo "Completed at: $(date)"

# 2. Meraki Inventory Collection (1 AM)
echo -e "\n[2/6] Running Meraki Inventory Collection..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_meraki_db.py
echo "Completed at: $(date)"

# 3. Meraki Enrichment (1 AM)
echo -e "\n[3/6] Running Meraki Enrichment..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_meraki_enriched_db.py
echo "Completed at: $(date)"

# 4. Inventory Summary (3 AM)
echo -e "\n[4/6] Running Inventory Summary..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_inventory_db.py
echo "Completed at: $(date)"

# 5. Enablement Tracking (4 AM)
echo -e "\n[5/6] Running Enablement Tracking..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_enablement_db.py
echo "Completed at: $(date)"

# 6. Circuit History (4:30 AM)
echo -e "\n[6/6] Running Circuit History..."
echo "Start time: $(date)"
/usr/bin/python3 /usr/local/bin/Main/nightly_circuit_history.py
echo "Completed at: $(date)"

echo -e "\n========================================"
echo "All nightly scripts completed at $(date)"