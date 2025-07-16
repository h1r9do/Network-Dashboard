#!/usr/bin/env python3
"""
Deeper analysis of Meraki HAR file
"""

import json
import re
from urllib.parse import urlparse

# Load the HAR file
har_file = '/var/www/html/meraki-data/n734.meraki.com.har'

with open(har_file, 'r') as f:
    har_data = json.load(f)

print("Meraki HAR Deep Analysis")
print("=" * 80)

# Group requests by type
api_calls = []
xhr_calls = []
post_requests = []

for entry in har_data['log']['entries']:
    request = entry['request']
    url = request['url']
    
    # Skip static assets
    if any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.gif', '.woff', '.ico']):
        continue
    
    # Look for API calls
    if '/api/' in url or request['method'] in ['POST', 'PUT', 'DELETE']:
        api_calls.append(entry)
    
    # Check if it's XHR
    for header in request['headers']:
        if header['name'].lower() == 'x-requested-with' and header['value'] == 'XMLHttpRequest':
            xhr_calls.append(entry)
            break
    
    # All POST requests
    if request['method'] == 'POST':
        post_requests.append(entry)

# Show API calls
print(f"\nAPI/AJAX Calls ({len(api_calls)}):")
print("-" * 80)

for entry in api_calls[:20]:  # First 20
    request = entry['request']
    response = entry['response']
    url = request['url']
    
    # Parse URL
    parsed = urlparse(url)
    
    print(f"\n{request['method']} {parsed.path}")
    print(f"Status: {response['status']}")
    
    # Show POST data
    if request.get('postData'):
        data = request['postData'].get('text', '')
        if data:
            print(f"Request data: {data[:200]}")
    
    # Show response
    if response.get('content') and response['content'].get('text'):
        text = response['content']['text']
        if text and len(text) < 1000:  # Only show small responses
            try:
                resp_json = json.loads(text)
                print(f"Response: {json.dumps(resp_json, indent=2)[:300]}")
            except:
                print(f"Response: {text[:200]}")

# Look for specific patterns
print("\n\nLooking for diagnostic/tool patterns...")
print("-" * 80)

diagnostic_patterns = [
    'diagnostic', 'tool', 'trace', 'ping', 'route', 'test',
    'live', 'monitor', 'status', 'uplink', 'wan'
]

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    if any(pattern in url.lower() for pattern in diagnostic_patterns):
        if not any(ext in url for ext in ['.js', '.css', '.png']):
            print(f"\n{entry['request']['method']} {url}")
            if entry['response']['status'] == 200:
                print("  ✓ Success")
                
# Look for WebSocket
print("\n\nWebSocket Analysis:")
print("-" * 80)

for entry in har_data['log']['entries']:
    request = entry['request']
    
    # Check for WebSocket upgrade headers
    upgrade_header = None
    for header in request['headers']:
        if header['name'].lower() == 'upgrade':
            upgrade_header = header['value']
            break
    
    if upgrade_header == 'websocket':
        print(f"\nWebSocket connection: {request['url']}")
        
        # Show key headers
        for header in request['headers']:
            if header['name'].lower() in ['sec-websocket-key', 'sec-websocket-version']:
                print(f"  {header['name']}: {header['value']}")

# Summary of domains
print("\n\nDomains accessed:")
print("-" * 80)

domains = {}
for entry in har_data['log']['entries']:
    parsed = urlparse(entry['request']['url'])
    domain = parsed.netloc
    if domain:
        domains[domain] = domains.get(domain, 0) + 1

for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {domain}: {count} requests")