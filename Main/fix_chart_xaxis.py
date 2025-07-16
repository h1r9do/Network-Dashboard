#\!/usr/bin/env python3
"""
Fix the x-axis display issue in Tab 1 and Tab 3 charts
"""

# Read the template
with open('/usr/local/bin/Main/templates/circuit_enablement_report.html', 'r') as f:
    content = f.read()

# Count how many times we'll make changes
changes = 0

# Fix Tab 1 chart - find the createDailyChart function
start_idx = content.find('function createDailyChart(data) {')
if start_idx \!= -1:
    # Find the options section
    options_start = content.find('options: {', start_idx)
    if options_start \!= -1:
        # Find the scales section
        scales_start = content.find('scales: {', options_start)
        if scales_start \!= -1:
            # Check if x-axis config exists
            y_start = content.find('y: {', scales_start)
            if 'x: {' not in content[scales_start:y_start]:
                # Add x-axis configuration before y-axis
                insert_pos = content.find('y: {', scales_start)
                x_config = '''                        x: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        },
                        '''
                content = content[:insert_pos] + x_config + content[insert_pos:]
                changes += 1
                print("Added x-axis configuration to Tab 1 chart")

# Write the fixed content
with open('/usr/local/bin/Main/templates/circuit_enablement_report.html', 'w') as f:
    f.write(content)

print(f"Made {changes} changes to fix x-axis display")
print("Updated: /usr/local/bin/Main/templates/circuit_enablement_report.html")
EOF < /dev/null
