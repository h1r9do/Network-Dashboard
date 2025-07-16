#!/usr/bin/env python3
"""
Simple fix for nightly_meraki_db.py to prevent caching failed ARIN lookups
"""

# Read the script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'r') as f:
    lines = f.readlines()

print("=== FIXING ARIN CACHING IN NIGHTLY_MERAKI_DB.PY ===\n")

# Find the line with "cache[ip] = provider" and add a condition
fixed = False
for i, line in enumerate(lines):
    if line.strip() == 'cache[ip] = provider':
        # Replace this line with conditional caching
        lines[i] = '    # Only cache successful lookups\n'
        lines.insert(i+1, '    if provider and provider not in ["Unknown", "Failed Lookup", "No Name Found"]:\n')
        lines.insert(i+2, '        cache[ip] = provider\n')
        lines.insert(i+3, '        logger.debug(f"Cached {ip} -> {provider}")\n')
        lines.insert(i+4, '    else:\n')
        lines.insert(i+5, '        logger.warning(f"Not caching {ip} with provider: {provider}")\n')
        fixed = True
        print(f"✅ Fixed caching logic at line {i+1}")
        break

if not fixed:
    print("❌ Could not find the cache[ip] = provider line")
    exit(1)

# Also fix the cache loading to skip old Unknown entries
cache_fixed = False
for i, line in enumerate(lines):
    if 'SELECT ip_address, provider_name FROM rdap_cache' in line:
        # Replace the query
        lines[i] = '        cursor.execute("""\n'
        lines.insert(i+1, '            SELECT ip_address, provider_name \n')
        lines.insert(i+2, '            FROM rdap_cache\n')
        lines.insert(i+3, "            WHERE provider_name != 'Unknown' \n")
        lines.insert(i+4, "               OR last_queried > NOW() - INTERVAL '7 days'\n")
        lines.insert(i+5, '        """)\n')
        cache_fixed = True
        print(f"✅ Fixed cache loading query at line {i+1}")
        break

if cache_fixed:
    print("\n✅ Both fixes applied successfully!")
else:
    print("⚠️  Cache loading fix not applied, but main fix is in place")

# Write the fixed script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'w') as f:
    f.writelines(lines)

print("\nThe nightly script has been fixed to:")
print("1. Only cache successful ARIN lookups")
print("2. Retry Unknown entries older than 7 days")
print("\nThe ongoing ARIN update will continue running in the background.")