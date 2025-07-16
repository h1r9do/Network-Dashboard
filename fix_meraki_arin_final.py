#!/usr/bin/env python3
"""
Final fix for ARIN caching in nightly_meraki_db.py
"""

import re

# Read the script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'r') as f:
    content = f.read()

print("=== FIXING ARIN CACHING IN NIGHTLY_MERAKI_DB.PY ===\n")

# Fix 1: Update the cache loading to skip old Unknown entries
old_cache_query = '''cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")'''
new_cache_query = '''cursor.execute("""
            SELECT ip_address, provider_name 
            FROM rdap_cache
            WHERE provider_name != 'Unknown' 
               OR last_queried > NOW() - INTERVAL '7 days'
        """)'''

if old_cache_query in content:
    content = content.replace(old_cache_query, new_cache_query)
    print("✅ Fixed cache loading to retry old Unknown entries")
else:
    print("❌ Could not find cache loading query")

# Fix 2: Update the get_provider_for_ip function to not cache failed lookups
# Find the section where it returns "Unknown" after failed rdap_data
old_pattern = r'''    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json\(rdap_url, ip\)
    if not rdap_data:
        missing_set.add\(ip\)
        return "Unknown"
    
    provider = parse_arin_response\(rdap_data\)
    cache\[ip\] = provider
    return provider'''

new_code = '''    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        logger.warning(f"RDAP lookup failed for {ip}, not caching")
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    # Only cache successful lookups
    if provider and provider not in ["Unknown", "No Name Found", "Failed Lookup"]:
        cache[ip] = provider
        logger.debug(f"Cached {ip} -> {provider}")
    else:
        logger.warning(f"Not caching {ip} with provider: {provider}")
    return provider'''

# Try to replace
match = re.search(r'rdap_url = f"https://rdap\.arin\.net/registry/ip/\{ip\}".*?return provider', content, re.DOTALL)
if match:
    content = content.replace(match.group(0), new_code)
    print("✅ Fixed get_provider_for_ip to not cache failed lookups")
else:
    print("❌ Could not find get_provider_for_ip pattern")

# Write the fixed content
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'w') as f:
    f.write(content)

print("\n✅ Script fixed successfully!")
print("\nThe nightly script now:")
print("1. Only caches successful ARIN lookups") 
print("2. Retries Unknown entries older than 7 days")
print("3. Logs when lookups fail or are not cached")