#!/usr/bin/env python3
"""
Add test route to dsrcircuits_blueprint.py
"""

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Find where to insert the test route (after the main dsrcircuits route)
insert_point = content.find("@dsrcircuits_bp.route('/api/circuits/data')")

if insert_point == -1:
    print("Could not find insertion point")
    exit(1)

# The test route code
test_route = '''
@dsrcircuits_bp.route('/dsrcircuits-test')
def dsrcircuits_test():
    """
    TEST VERSION: Copy of production dsrcircuits for development
    
    Identical to production but serves on /dsrcircuits-test route
    for safe development and testing.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Get enriched circuits data (same as production)
        enriched_circuits = db.session.query(EnrichedCircuit).join(
            MerakiInventory,
            EnrichedCircuit.network_name == MerakiInventory.network_name
        ).filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
            )
        ).filter(
            # Exclude sites without any IP addresses in Meraki (not live)
            ~(
                ((MerakiInventory.wan1_ip.is_(None)) | (MerakiInventory.wan1_ip == '') | (MerakiInventory.wan1_ip == 'None')) &
                ((MerakiInventory.wan2_ip.is_(None)) | (MerakiInventory.wan2_ip == '') | (MerakiInventory.wan2_ip == 'None'))
            )
        ).order_by(EnrichedCircuit.network_name).all()
        
        grouped_data = []
        
        for circuit in enriched_circuits:
            # Get all circuits for this site
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            # Use improved cost assignment logic
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info
                }
            })
        
        # Use the same template as production
        return render_template('dsrcircuits.html', grouped_data=grouped_data)
        
    except Exception as e:
        logger.error(f"Error in test dsrcircuits: {e}")
        return render_template('dsrcircuits.html', error=f"Error: {e}")


'''

# Insert the test route before the API route
new_content = content[:insert_point] + test_route + content[insert_point:]

# Write back
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(new_content)

print("✅ Added /dsrcircuits-test route")
print("Test URL: http://neamsatcor1ld01.trtc.com:5052/dsrcircuits-test")