#!/usr/bin/env python3
"""
Test the updated nightly script with a few networks that have private IPs
"""
import subprocess
import time
import signal
import sys

def signal_handler(sig, frame):
    print('\n\nTest interrupted by user')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("=== Testing Updated Nightly Script ===\n")
print("This will run the script for a short time to verify private IP resolution is working.")
print("Press Ctrl+C to stop at any time.\n")

# Start the script
process = subprocess.Popen(
    ['sudo', 'python3', '/usr/local/bin/Main/nightly/nightly_meraki_db.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

print("Starting script... watching for private IP resolution:\n")

# Monitor output for private IP resolution
start_time = time.time()
timeout = 300  # 5 minutes max

private_ip_found = False
resolution_count = 0

try:
    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if not line:
            break
            
        # Print all lines
        print(line.rstrip())
        
        # Look for private IP detection and resolution
        if "is private, attempting DDNS resolution" in line:
            private_ip_found = True
        elif "Resolved WAN" in line and "private IP" in line:
            resolution_count += 1
            print(f"\n✅ SUCCESSFUL RESOLUTION #{resolution_count}")
        elif "Could not resolve" in line and "private IP" in line:
            print("\n❌ Failed to resolve a private IP")
            
        # Stop after seeing a few resolutions
        if resolution_count >= 3:
            print(f"\n\n✅ SUCCESS: Found {resolution_count} private IP resolutions!")
            print("The script is working correctly.")
            process.terminate()
            break
            
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    process.terminate()
    
# Clean up
process.wait()

if not private_ip_found:
    print("\n⚠️  No private IPs were detected during the test period.")
    print("This could mean:")
    print("1. The first few networks don't have private IPs")
    print("2. The script needs more time to reach networks with private IPs")
    print("3. There might be an issue with the private IP detection")
elif resolution_count == 0:
    print("\n⚠️  Private IPs were detected but none were resolved.")
    print("This could mean DDNS is not enabled for those networks.")
else:
    print(f"\n✅ Test completed successfully!")
    print(f"   - Private IPs detected: Yes")
    print(f"   - Resolutions successful: {resolution_count}")