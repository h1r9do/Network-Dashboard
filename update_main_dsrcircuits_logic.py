#!/usr/bin/env python3
"""
Update the main dsrcircuits route to use the improved provider-based matching logic
"""

import re

def update_main_dsrcircuits():
    # Read the current blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
        content = f.read()
    
    # First, add the improved provider matching import at the top
    import_section = '''from dsrcircuits_beta_combined import ProviderMatcher, assign_costs_improved'''
    
    # Find where imports end and add the new import
    import_end = content.find('from models import')
    if import_end != -1:
        import_line_end = content.find('\n', import_end) + 1
        content = content[:import_line_end] + import_section + '\n' + content[import_line_end:]
    
    # Now replace the main dsrcircuits function with the improved version
    function_start = content.find('@dsrcircuits_bp.route(\'/dsrcircuits\')')
    if function_start == -1:
        print("❌ Could not find dsrcircuits route")
        return
    
    # Find the end of the function by looking for the next @route or end of file
    next_route = content.find('@dsrcircuits_bp.route(', function_start + 1)
    if next_route == -1:
        next_route = len(content)
    
    # Find the actual end of the function (next function definition)
    function_end = content.find('\n@', function_start + 1)
    if function_end == -1 or function_end > next_route:
        function_end = next_route
    
    # Create the new improved function
    new_function = '''@dsrcircuits_bp.route('/dsrcircuits')
def dsrcircuits():
    """
    IMPROVED: Main circuits data table page with provider-based cost matching
    
    Uses improved provider matching logic to accurately assign costs
    from Non-DSR circuits and other circuit records.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Get enriched circuits data (same as beta)
        enriched_circuits = EnrichedCircuit.query.filter(
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
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
        
        # Use the updated template (now without role columns)
        return render_template('dsrcircuits.html', grouped_data=grouped_data)
        
    except Exception as e:
        logger.error(f"Error in main dsrcircuits: {e}")
        return render_template('dsrcircuits.html', error=f"Error: {e}")

'''
    
    # Replace the old function with the new one
    content = content[:function_start] + new_function + content[function_end:]
    
    # Add necessary imports at the top if not already present
    if 'from sqlalchemy import func' not in content:
        # Find the models import line and add func import
        models_import = content.find('from models import')
        if models_import != -1:
            models_line_end = content.find('\n', models_import)
            content = content[:models_line_end] + '\nfrom sqlalchemy import func' + content[models_line_end:]
    
    if 'from models import' in content and 'EnrichedCircuit' not in content:
        # Add EnrichedCircuit to the models import
        models_import_start = content.find('from models import')
        models_import_end = content.find('\n', models_import_start)
        models_line = content[models_import_start:models_import_end]
        if 'EnrichedCircuit' not in models_line:
            new_models_line = models_line.replace('from models import', 'from models import EnrichedCircuit,')
            content = content[:models_import_start] + new_models_line + content[models_import_end:]
    
    # Save the updated blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated main dsrcircuits route with improved provider-based matching logic")

if __name__ == "__main__":
    update_main_dsrcircuits()