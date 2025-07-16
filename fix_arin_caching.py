#!/usr/bin/env python3
"""
Fix the ARIN caching issue in nightly_meraki_db.py
"""

def show_fix():
    print("""
=== FIX FOR ARIN CACHING ISSUE ===

The problem is in the get_provider_for_ip function (line 602-633).

Current behavior:
1. If fetch_json returns None (API failure), it caches "Unknown"
2. These failed lookups are never retried

RECOMMENDED FIX:

Replace lines 625-630 in nightly_meraki_db.py:

CURRENT CODE:
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    
FIXED CODE:
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        # Don't cache failed lookups - return Unknown without caching
        logger.warning(f"RDAP lookup failed for {ip}, not caching")
        return "Unknown"

Then move the cache storage (line 632) inside an else block:

    provider = parse_arin_response(rdap_data)
    if provider != "Unknown":  # Only cache successful lookups
        cache[ip] = provider
    return provider

ALTERNATIVE FIX - Add retry logic:

In the main() function, modify the cache loading (lines 1014-1019) to skip Unknown entries older than 7 days:

    cursor.execute('''
        SELECT ip_address, provider_name 
        FROM rdap_cache
        WHERE provider_name != 'Unknown' 
           OR last_queried > NOW() - INTERVAL '7 days'
    ''')

This would retry Unknown lookups after a week.
""")

if __name__ == "__main__":
    show_fix()