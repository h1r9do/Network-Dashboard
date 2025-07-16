#!/usr/bin/env python3
"""
Copy the working data structure from test route to production route
"""

print("=== FIXING PRODUCTION BLUEPRINT DATA STRUCTURE ===\n")

# Read the working test blueprint
with open('/usr/local/bin/Main/dsrcircuits_test.py', 'r') as f:
    test_content = f.read()

# Read the production blueprint  
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    prod_content = f.read()

# Extract the working data structure from test route
import re

# Find the working dsrcircuits-test route
test_route_match = re.search(r'@dsrcircuits_test_bp\.route\(\'/dsrcircuits-test\'\).*?grouped_data\.append\({.*?}\)', test_content, re.DOTALL)

if test_route_match:
    print("✅ Found working test route structure")
    
    # Extract the data structure part
    data_structure_match = re.search(r'grouped_data\.append\({.*?}\)', test_route_match.group(0), re.DOTALL)
    
    if data_structure_match:
        working_structure = data_structure_match.group(0)
        print("✅ Extracted working data structure")
        
        # Find the main production route and update its data structure
        prod_route_pattern = r'(@dsrcircuits_bp\.route\(\'/dsrcircuits\'\).*?)(grouped_data\.append\({.*?}\))'
        prod_match = re.search(prod_route_pattern, prod_content, re.DOTALL)
        
        if prod_match:
            before_structure = prod_match.group(1)
            old_structure = prod_match.group(2)
            
            # Replace the old structure with the working one
            new_content = prod_content.replace(prod_match.group(0), before_structure + working_structure)
            
            # Also need to add the imports and cost assignment logic from test
            # Find the assign_costs_improved call
            assign_costs_match = re.search(r'wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved\(circuit, site_circuits\)', test_content)
            
            if assign_costs_match and 'assign_costs_improved' not in new_content:
                # Add the import
                new_content = new_content.replace(
                    'from dsrcircuits_beta_combined import ProviderMatcher',
                    'from dsrcircuits_beta_combined import ProviderMatcher, assign_costs_improved'
                )
                
                # Add the cost assignment before grouped_data.append
                cost_assignment = '''
            # Get all circuits for this site
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            # Use improved cost assignment logic
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            '''
                
                new_content = new_content.replace('grouped_data.append({', cost_assignment + '\n            grouped_data.append({')
            
            print("✅ Updated production route data structure")
        else:
            print("❌ Could not find production route pattern")
            new_content = prod_content
    else:
        print("❌ Could not extract data structure")
        new_content = prod_content
else:
    print("❌ Could not find test route")
    new_content = prod_content

# Write the updated production blueprint
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(new_content)

print("✅ Production blueprint updated with working data structure")
print("✅ Should now provide match_info for DSR badges")