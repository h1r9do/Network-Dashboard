#!/bin/bash
# Setup script for provider matching test environment

echo "Setting up Provider Matching Test Environment..."

# 1. Create the test database table
echo "Creating test database table..."
psql -h 10.0.145.130 -U meraki_user -d meraki_dashboard -f create_test_enriched_table.sql

# 2. Create the provider mappings table if it doesn't exist
echo "Creating provider mappings table..."
psql -h 10.0.145.130 -U meraki_user -d meraki_dashboard -f create_provider_mapping_table.sql
psql -h 10.0.145.130 -U meraki_user -d meraki_dashboard -f final_provider_mappings.sql

# 3. Run the test enrichment
echo "Running test provider enrichment..."
python3 test_provider_enrichment.py

# 4. Check the results
echo "Checking test results..."
psql -h 10.0.145.130 -U meraki_user -d meraki_dashboard -c "SELECT * FROM provider_match_test_statistics;"

echo "Setup complete! You can now:"
echo "1. Add the routes from dsrcircuits_test_route.py to dsrcircuits.py"
echo "2. Copy the template files to templates/ directory"
echo "3. Visit http://neamsatcor1ld01.trtc.com:5052/dsrcircuits-test"

echo ""
echo "Sample test query:"
echo "SELECT site_name, dsr_provider, arin_provider, provider_match_status, provider_match_confidence"
echo "FROM enriched_circuits_test"
echo "WHERE provider_match_status = 'matched'"
echo "ORDER BY provider_match_confidence DESC"
echo "LIMIT 10;"