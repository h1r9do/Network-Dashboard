#!/usr/bin/env python3
"""
Analyze Meraki HAR file to understand traceroute implementation
"""

import json
import re
from urllib.parse import urlparse, parse_qs

# Load the HAR file
har_file = '/var/www/html/meraki-data/n734.meraki.com.har'

with open(har_file, 'r') as f:
    har_data = json.load(f)

print("Meraki Dashboard Traceroute Analysis")
print("=" * 80)

# Find traceroute-related requests
traceroute_requests = []
interesting_requests = []

for entry in har_data['log']['entries']:
    request = entry['request']
    response = entry['response']
    url = request['url']
    
    # Look for traceroute-related endpoints
    if any(term in url.lower() for term in ['traceroute', 'trace', 'route', 'ping', 'diagnostic', 'tool']):
        traceroute_requests.append(entry)
    
    # Also look for device-specific calls that might be related
    if 'Q2KY-FBAF-VTHH' in url or 'devices' in url:
        interesting_requests.append(entry)

# Analyze traceroute requests
if traceroute_requests:
    print(f"\nFound {len(traceroute_requests)} traceroute-related requests:")
    print("-" * 80)
    
    for entry in traceroute_requests:
        request = entry['request']
        response = entry['response']
        
        print(f"\n{request['method']} {request['url']}")
        print(f"Status: {response['status']}")
        
        # Show headers
        auth_headers = {}
        for header in request['headers']:
            if header['name'].lower() in ['authorization', 'x-cisco-meraki-api-key', 'cookie', 'x-csrf-token']:
                auth_headers[header['name']] = header['value'][:50] + '...' if len(header['value']) > 50 else header['value']
        
        if auth_headers:
            print("Auth headers:")
            for name, value in auth_headers.items():
                print(f"  {name}: {value}")
        
        # Show request body
        if request.get('postData'):
            print(f"Request body: {request['postData'].get('text', '')[:200]}")
        
        # Show response
        if response.get('content') and response['content'].get('text'):
            try:
                resp_data = json.loads(response['content']['text'])
                print(f"Response preview: {json.dumps(resp_data, indent=2)[:500]}")
            except:
                print(f"Response: {response['content']['text'][:200]}")

# Look for any diagnostic tool usage
print(f"\n\nOther interesting requests ({len(interesting_requests)} found):")
print("-" * 80)

# Filter for unique endpoints
unique_endpoints = {}
for entry in interesting_requests:
    url = entry['request']['url']
    parsed = urlparse(url)
    path = parsed.path
    
    # Skip static assets
    if any(ext in path for ext in ['.js', '.css', '.png', '.jpg', '.gif', '.woff']):
        continue
        
    # Group by endpoint pattern
    endpoint = re.sub(r'/[0-9a-fA-F-]+', '/{id}', path)
    endpoint = re.sub(r'/L_[0-9]+', '/L_{id}', endpoint)
    endpoint = re.sub(r'/N_[0-9]+', '/N_{id}', endpoint)
    
    if endpoint not in unique_endpoints:
        unique_endpoints[endpoint] = []
    unique_endpoints[endpoint].append(entry)

# Show unique endpoints
for endpoint, entries in sorted(unique_endpoints.items()):
    if any(term in endpoint.lower() for term in ['device', 'appliance', 'tool', 'diagnostic', 'status']):
        print(f"\n{endpoint} ({len(entries)} requests)")
        
        # Show first example
        entry = entries[0]
        request = entry['request']
        print(f"  Method: {request['method']}")
        print(f"  Example URL: {request['url'][:100]}...")
        
        if request['method'] == 'POST' and request.get('postData'):
            print(f"  Body: {request['postData'].get('text', '')[:100]}")

# Look for WebSocket connections
websocket_entries = [e for e in har_data['log']['entries'] if 'websocket' in e['request']['url'].lower()]
if websocket_entries:
    print(f"\n\nWebSocket connections found: {len(websocket_entries)}")
    for entry in websocket_entries[:3]:
        print(f"  {entry['request']['url']}")

print("\n\nSummary:")
print("-" * 80)
print(f"Total requests in HAR: {len(har_data['log']['entries'])}")
print(f"Traceroute requests: {len(traceroute_requests)}")
print(f"Device-related requests: {len(interesting_requests)}")