#!/usr/bin/env python3
"""
Add DSR badge to beta template
"""

import re

def add_dsr_badge():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Add CSS for the badge at the end of the style section
    style_end = content.find('</style>')
    if style_end != -1:
        badge_css = '''
        /* DSR Verified Badge */
        .dsr-badge {
            display: inline-flex;
            align-items: center;
            background: #2ecc71;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
            border: 1px solid #27ae60;
            vertical-align: middle;
        }
        
        .dsr-badge::after {
            content: "✓";
            margin-left: 4px;
            font-size: 12px;
        }
        '''
        content = content[:style_end] + badge_css + '\n    ' + content[style_end:]
    
    # Find where WAN1 provider is displayed in the table
    wan1_provider_pattern = r'<td>{{ entry\.wan1\.provider if entry\.wan1\.provider else \'N/A\' }}</td>'
    wan1_replacement = '''<td>
                            {{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''
    
    content = re.sub(wan1_provider_pattern, wan1_replacement, content)
    
    # Find where WAN2 provider is displayed in the table
    wan2_provider_pattern = r'<td>{{ entry\.wan2\.provider if entry\.wan2\.provider else \'N/A\' }}</td>'
    wan2_replacement = '''<td>
                            {{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''
    
    content = re.sub(wan2_provider_pattern, wan2_replacement, content)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Added DSR badge to beta template")

if __name__ == "__main__":
    add_dsr_badge()