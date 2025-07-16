#!/usr/bin/env python3
"""
Test the modal endpoint to see what data is returned
"""

import requests
import json

def main():
    """Test modal endpoint"""
    print("🔍 Testing Modal Endpoint for AZP 08")
    print("=" * 60)
    
    # The modal endpoint from dsrcircuits.py
    url = "http://localhost:5052/api/circuit-details"
    
    # Simulate the AJAX request the modal makes
    data = {
        'site_name': 'AZP 08'
    }
    
    print(f"📡 Making request to: {url}")
    print(f"   Data: {data}")
    
    try:
        response = requests.post(url, json=data)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print("\n📝 Full Response:")
            print(json.dumps(response_data, indent=2))
            
            # Focus on the raw_notes field
            if 'raw_notes' in response_data:
                raw_notes = response_data['raw_notes']
                print("\n🔍 Raw Notes Field:")
                print("   Display:")
                print("   " + "-" * 40)
                print(raw_notes)
                print("   " + "-" * 40)
                print(f"\n   Repr: {repr(raw_notes)}")
                
                # Check for issues
                if '\\n' in raw_notes:
                    print("\n   ⚠️  LITERAL \\n FOUND IN RESPONSE!")
                elif '\n' not in raw_notes and raw_notes:
                    print("\n   ⚠️  NO NEWLINES FOUND!")
                else:
                    print("\n   ✅ Proper newlines found")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    main()