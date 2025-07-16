#!/usr/bin/env python3
"""
Detailed analysis of Meraki HAR file
"""

import json
import re
from urllib.parse import urlparse

# Load the HAR file
har_file = '/var/www/html/meraki-data/n734.meraki.com.har'

with open(har_file, 'r') as f:
    har_data = json.load(f)

print("Detailed HAR Analysis - Looking for Traceroute")
print("=" * 80)

# Look for all POST requests and API calls
api_requests = []
post_requests = []

for entry in har_data['log']['entries']:
    request = entry['request']
    url = request['url']
    method = request['method']
    
    # Skip static assets
    if any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.gif', '.woff', '.ico']):
        continue
    
    # Look for API patterns
    if '/api/' in url or method in ['POST', 'PUT', 'DELETE']:
        api_requests.append(entry)
    
    if method == 'POST':
        post_requests.append(entry)

print(f"\nFound {len(api_requests)} API requests")
print(f"Found {len(post_requests)} POST requests")

# Analyze POST requests
print("\n\nPOST Requests:")
print("-" * 80)

for i, entry in enumerate(post_requests[:20]):  # First 20 POST requests
    request = entry['request']
    response = entry['response']
    url = request['url']
    
    # Parse URL
    parsed = urlparse(url)
    path = parsed.path
    
    print(f"\n{i+1}. POST {path}")
    print(f"   Full URL: {url[:100]}...")
    print(f"   Status: {response['status']}")
    
    # Show request body
    if request.get('postData'):
        body = request['postData'].get('text', '')
        print(f"   Body: {body[:200]}...")
        
        # Look for interesting parameters
        if any(term in body.lower() for term in ['8.8.8.8', 'trace', 'ping', 'wan', '192.168']):
            print("   *** INTERESTING - Contains relevant terms!")
    
    # Show response preview
    if response.get('content') and response['content'].get('text'):
        resp_text = response['content']['text'][:200]
        print(f"   Response: {resp_text}...")

# Look for WebSocket or XHR patterns
print("\n\nLooking for real-time updates (WebSocket/XHR):")
print("-" * 80)

xhr_requests = []
for entry in har_data['log']['entries']:
    request = entry['request']
    
    # Check if it's an XHR request
    for header in request['headers']:
        if header['name'].lower() == 'x-requested-with' and header['value'] == 'XMLHttpRequest':
            xhr_requests.append(entry)
            break

print(f"Found {len(xhr_requests)} XHR requests")

# Show unique XHR endpoints
xhr_endpoints = {}
for entry in xhr_requests:
    url = entry['request']['url']
    parsed = urlparse(url)
    path = re.sub(r'/[0-9a-fA-F-]+', '/{id}', parsed.path)
    path = re.sub(r'/L_[0-9]+', '/L_{id}', path)
    
    if path not in xhr_endpoints:
        xhr_endpoints[path] = []
    xhr_endpoints[path].append(entry)

for endpoint, entries in sorted(xhr_endpoints.items())[:10]:
    print(f"\n{endpoint} ({len(entries)} requests)")
    
    # Show example
    entry = entries[0]
    if entry['request'].get('postData'):
        print(f"  Example body: {entry['request']['postData'].get('text', '')[:100]}")

# Search for specific patterns in all requests
print("\n\nSearching for specific patterns:")
print("-" * 80)

patterns = ['8.8.8.8', '192.168.0', 'wan2', 'traceroute', 'diagnostic', 'tool']
pattern_matches = []

for entry in har_data['log']['entries']:
    request = entry['request']
    url = request['url']
    
    # Check URL
    for pattern in patterns:
        if pattern in url.lower():
            pattern_matches.append(('URL', pattern, entry))
    
    # Check request body
    if request.get('postData') and request['postData'].get('text'):
        body = request['postData']['text']
        for pattern in patterns:
            if pattern in body.lower():
                pattern_matches.append(('BODY', pattern, entry))

print(f"\nFound {len(pattern_matches)} pattern matches")
for match_type, pattern, entry in pattern_matches[:10]:
    url = entry['request']['url']
    parsed = urlparse(url)
    print(f"\n{match_type} contains '{pattern}': {parsed.path}")
    if match_type == 'BODY':
        print(f"  Body: {entry['request']['postData']['text'][:100]}...")