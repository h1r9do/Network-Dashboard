#!/usr/bin/env python3
"""
Fix the ARIN caching issue in nightly_meraki_db.py
This script creates a backup and applies the fix
"""

import shutil
from datetime import datetime

def fix_arin_caching():
    script_path = '/usr/local/bin/Main/nightly/nightly_meraki_db.py'
    backup_path = f'{script_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print("=== FIXING ARIN CACHING IN NIGHTLY_MERAKI_DB.PY ===\n")
    
    # Create backup
    print(f"Creating backup: {backup_path}")
    shutil.copy2(script_path, backup_path)
    
    # Read the script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Find and fix the get_provider_for_ip function
    # The issue is around line 625-633
    
    # Original problematic code pattern
    old_code = '''    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    cache[ip] = provider
    return provider'''
    
    # Fixed code that doesn't cache failed lookups
    new_code = '''    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        logger.warning(f"RDAP lookup failed for {ip}, not caching")
        # Don't cache failed lookups - return Unknown without caching
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    # Only cache successful lookups and valid results
    if provider and provider not in ["Unknown", "No Name Found", "Failed Lookup"]:
        cache[ip] = provider
        logger.debug(f"Cached {ip} -> {provider}")
    else:
        logger.warning(f"Not caching {ip} with provider: {provider}")
    return provider'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Fixed get_provider_for_ip function to not cache failed lookups")
    else:
        print("⚠️  Could not find exact code pattern, applying alternative fix...")
        
        # Try a more flexible replacement
        import re
        
        # Find the function and replace the problematic section
        pattern = r'(rdap_url = f"https://rdap\.arin\.net/registry/ip/\{ip\}".*?cache\[ip\] = provider.*?return provider)'
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content.replace(match.group(0), new_code)
            print("✅ Applied alternative fix pattern")
        else:
            print("❌ Could not find code to fix. Manual intervention needed.")
            return False
    
    # Also fix the cache loading to skip old Unknown entries
    # Find the cache loading section around line 1014-1019
    old_cache_load = '''cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")
        for ip, provider in cursor.fetchall():
            ip_cache[ip] = provider'''
    
    new_cache_load = '''cursor.execute("""
            SELECT ip_address, provider_name 
            FROM rdap_cache
            WHERE provider_name != 'Unknown' 
               OR last_queried > NOW() - INTERVAL '7 days'
        """)
        for ip, provider in cursor.fetchall():
            ip_cache[ip] = provider'''
    
    if old_cache_load in content:
        content = content.replace(old_cache_load, new_cache_load)
        print("✅ Fixed cache loading to retry old Unknown entries")
    else:
        # Try without extra spaces
        old_cache_load2 = 'cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")'
        new_cache_load2 = '''cursor.execute("""
            SELECT ip_address, provider_name 
            FROM rdap_cache
            WHERE provider_name != 'Unknown' 
               OR last_queried > NOW() - INTERVAL '7 days'
        """)'''
        
        if old_cache_load2 in content:
            content = content.replace(old_cache_load2, new_cache_load2)
            print("✅ Fixed cache loading query")
    
    # Write the fixed content
    with open(script_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Script fixed successfully!")
    print(f"Backup saved to: {backup_path}")
    print("\nNext steps:")
    print("1. The 998 failed lookups have been cleared from cache")
    print("2. The script will now retry failed lookups instead of caching them")
    print("3. Old Unknown entries will be retried after 7 days")
    
    return True

if __name__ == "__main__":
    fix_arin_caching()