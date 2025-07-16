#!/usr/bin/env python3
"""Debug tag modal functionality"""

import subprocess
import sys

# Run as postgres user
def run_query(query):
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-c', query],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Check ALB 01 device
query = """
SELECT device_serial, device_name, device_tags, network_name
FROM meraki_inventory
WHERE network_name = 'ALB 01'
"""

result = run_query(query)
if result:
    lines = result.split('|')
    if len(lines) >= 4:
        print("ALB 01 Device Info:")
        print(f"  Serial: {lines[0].strip()}")
        print(f"  Name: {lines[1].strip()}")
        print(f"  Tags: {lines[2].strip()}")
        print(f"  Network: {lines[3].strip()}")
else:
    print("ALB 01 not found")

print("\nTo test the tag modal:")
print("1. Go to http://localhost:5052/dsrcircuits")
print("2. Find ALB 01 and click Confirm")
print("3. In the modal, click 'Edit Tags'")
print("4. Add a tag and click 'Save Tags'")
print("5. Check browser console for errors (F12)")
print("\nIf it fails, check:")
print("- Is deviceSerial set? Run in console: $('#confirmModal').data('deviceSerial')")
print("- Are there console errors when clicking Save?")
print("- Check network tab for the API request/response")