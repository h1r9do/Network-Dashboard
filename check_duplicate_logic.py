#!/usr/bin/env python3
"""
Check and remove duplicate wireless badge logic from main route
"""

print("=== CHECKING FOR DUPLICATE WIRELESS LOGIC ===\n")

with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Count occurrences of wireless badge logic
wireless_count = content.count("# Check WAN1 for wireless")
starlink_count = content.count("wan1_wireless_badge = 'STARLINK'")

print(f"Found {wireless_count} instances of wireless badge logic")
print(f"Found {starlink_count} instances of Starlink badge assignment")

# Check if main route has wireless logic (it shouldn't)
import re

# Find main route content
main_route_match = re.search(r'@dsrcircuits_bp\.route\(\'/dsrcircuits\'\)\s*\ndef dsrcircuits\(\):.*?@dsrcircuits_bp\.route', content, re.DOTALL)

if main_route_match:
    main_route_content = main_route_match.group(0)
    if "wireless_badge" in main_route_content:
        print("\n⚠️ Found wireless_badge logic in main route - this causes double counting!")
        
        # Remove wireless logic from main route
        # The main route should NOT have wireless badge logic
        lines = content.split('\n')
        in_main_route = False
        in_test_route = False
        new_lines = []
        skip_wireless = False
        
        for i, line in enumerate(lines):
            if '@dsrcircuits_bp.route(\'/dsrcircuits\')' in line and i < 150:
                in_main_route = True
                in_test_route = False
            elif '@dsrcircuits_bp.route(\'/dsrcircuits-test\')' in line:
                in_main_route = False
                in_test_route = True
            elif '@dsrcircuits_bp.route' in line:
                in_main_route = False
                in_test_route = False
                
            # Skip wireless logic in main route
            if in_main_route and '# Check for wireless badges' in line:
                skip_wireless = True
                continue
            elif in_main_route and skip_wireless and 'grouped_data.append({' in line:
                skip_wireless = False
                # Fall through to append the line
                
            if not (in_main_route and skip_wireless):
                new_lines.append(line)
        
        # Write cleaned content
        with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
            f.write('\n'.join(new_lines))
            
        print("✅ Removed wireless badge logic from main route")
        print("   (Wireless badges should only be in test route)")
else:
    print("❌ Could not find main route content")

print("\nWireless badges should now only be counted once in the test route!")