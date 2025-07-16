#!/bin/bash

echo "=== Testing AZC 01 Confirmation Dialog Submission ==="

# Test the exact scenario you described:
# 1. WAN1: OK for DSR data
# 2. WAN2: Custom with "Digi" provider and "Cell" speed

# First, let's check the current state of AZC 01
echo "Current state of AZC 01:"
curl -s "http://localhost:5052/confirm/AZC%2001" \
  -H "Content-Type: application/json" \
  -X POST | jq .

echo -e "\n=== Testing confirmation submission ==="

# Submit the confirmation data
curl -v "http://localhost:5052/confirm/AZC%2001/submit" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "wan1": {
      "provider": "Cox Business/BOI",
      "speed": "300.0M x 30.0M",
      "monthly_cost": "$0.00",
      "circuit_role": "Primary"
    },
    "wan2": {
      "provider": "Digi",
      "speed": "Cell",
      "monthly_cost": "$0.00",
      "circuit_role": "Secondary"
    }
  }' | jq .

echo -e "\n=== Verification: Check if data was saved ==="

# Check the current enriched circuits data for AZC 01
psql -U dsradmin -d dsrcircuits -c "
SELECT network_name, wan1_provider, wan1_speed, wan1_confirmed, 
       wan2_provider, wan2_speed, wan2_confirmed, last_updated
FROM enriched_circuits 
WHERE network_name = 'AZC 01';
"

echo -e "\n=== Test Complete ==="