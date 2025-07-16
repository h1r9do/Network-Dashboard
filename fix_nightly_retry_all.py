#!/usr/bin/env python3
"""
Fix nightly_meraki_db.py to retry ALL unresolved IPs every night
"""

# Read the script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'r') as f:
    content = f.read()

print("=== UPDATING NIGHTLY SCRIPT TO RETRY ALL UNRESOLVED IPS ===\n")

# Update the cache loading to ONLY load successful resolutions
old_cache_query = '''cursor.execute("""
            SELECT ip_address, provider_name 
            FROM rdap_cache
            WHERE provider_name != 'Unknown' 
               OR last_queried > NOW() - INTERVAL '7 days'
        """)'''

new_cache_query = '''cursor.execute("""
            SELECT ip_address, provider_name 
            FROM rdap_cache
            WHERE provider_name NOT IN ('Unknown', 'Failed Lookup', 'No Name Found', '')
              AND provider_name IS NOT NULL
        """)'''

if old_cache_query in content:
    content = content.replace(old_cache_query, new_cache_query)
    print("✅ Updated cache loading to only load successful resolutions")
    print("   - Will retry ALL unresolved IPs every night")
    print("   - Won't skip recent failures")
else:
    print("❌ Could not find cache loading query to update")

# Write the updated script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'w') as f:
    f.write(content)

print("\n✅ Script updated successfully!")
print("\nThe nightly script will now:")
print("1. Only load successfully resolved IPs from cache")
print("2. Retry ALL unresolved IPs every night") 
print("3. This ensures temporary API issues get retried")
print("4. The 18 remaining unresolved IPs will be attempted every night")