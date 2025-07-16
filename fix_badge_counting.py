#!/usr/bin/env python3
"""
Fix badge counting logic - match_info is a dict, not object
"""

print("=== FIXING BADGE COUNTING LOGIC ===\n")

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Find and fix the badge counting logic
old_counting = '''        for entry in grouped_data:
            # Count DSR badges
            if entry['wan1']['match_info'] and entry['wan1']['match_info'].dsr_verified:
                dsr_count += 1
            if entry['wan2']['match_info'] and entry['wan2']['match_info'].dsr_verified:
                dsr_count += 1'''

new_counting = '''        for entry in grouped_data:
            # Count DSR badges - check if match_info is dict or object
            wan1_info = entry['wan1']['match_info']
            if wan1_info:
                if hasattr(wan1_info, 'dsr_verified'):
                    if wan1_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan1_info, dict) and wan1_info.get('dsr_verified'):
                    dsr_count += 1
                    
            wan2_info = entry['wan2']['match_info']
            if wan2_info:
                if hasattr(wan2_info, 'dsr_verified'):
                    if wan2_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan2_info, dict) and wan2_info.get('dsr_verified'):
                    dsr_count += 1'''

if old_counting in content:
    content = content.replace(old_counting, new_counting)
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
    print("✅ Fixed badge counting logic to handle dict match_info")
else:
    print("❌ Could not find badge counting logic")

print("\nBadge counting should now work with both dict and object match_info!")