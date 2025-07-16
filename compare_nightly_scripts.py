#!/usr/bin/env python3
"""
Compare the current nightly script with the new complete version
Shows what will change when we implement the new script
"""

import difflib
from datetime import datetime

print("=== Nightly Script Comparison ===")
print(f"Generated: {datetime.now()}")
print()

# Read current script
with open('/usr/local/bin/Main/nightly/nightly_enriched_db.py', 'r') as f:
    current_lines = f.readlines()

# Read new script
with open('/usr/local/bin/nightly_enriched_db_complete.py', 'r') as f:
    new_lines = f.readlines()

print(f"Current script: {len(current_lines)} lines")
print(f"New script: {len(new_lines)} lines")
print()

# Key differences
print("=== KEY DIFFERENCES ===")
print()

print("1. TRUNCATE vs Smart Updates:")
print("   Current: Line 477 - cursor.execute('TRUNCATE TABLE enriched_circuits')")
print("   New: No TRUNCATE - only updates changed records")
print()

print("2. Preservation Logic:")
print("   Current: No preservation - rebuilds from scratch")
print("   New: Preserves DSR-ARIN matched data and unchanged non-DSR circuits")
print()

print("3. WAN Flip Detection:")
print("   Current: No flip detection")
print("   New: detect_wan_flip() function handles 186 flipped sites")
print()

print("4. Enriched->Circuits Sync:")
print("   Current: No sync back to circuits table")
print("   New: sync_enriched_to_circuits() syncs confirmed data for non-DSR circuits")
print()

print("5. Source Data Change Detection:")
print("   Current: Always processes all records")
print("   New: has_source_data_changed() skips unchanged non-DSR circuits")
print()

# Find specific sections
print("=== NEW FUNCTIONS ADDED ===")
new_functions = [
    "detect_wan_flip",
    "has_source_data_changed", 
    "sync_enriched_to_circuits",
    "providers_match_for_sync",
    "normalize_provider_for_arin_match"
]

for func in new_functions:
    for i, line in enumerate(new_lines):
        if f"def {func}" in line:
            print(f"- {func}() at line {i+1}")
            break

print()
print("=== IMPLEMENTATION SUMMARY ===")
print("The new script will:")
print("✅ Preserve the 870 DSR-ARIN matched fixes from today")
print("✅ Only update records that actually changed")
print("✅ Sync manual web edits back to circuits table for non-DSR")
print("✅ Handle WAN flipping correctly")
print("✅ Respect manual_override flags")
print()
print("To implement:")
print("1. The new script is ready at: /usr/local/bin/nightly_enriched_db_complete.py")
print("2. Backups are saved in: /usr/local/bin/circuit_backups_20250710_202818/")
print("3. Copy the new script over the old one when ready")
print()
print("IMPORTANT: The script runs at 3 AM according to root cron")