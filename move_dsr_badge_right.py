#!/usr/bin/env python3
"""
Move DSR badge to the far right of provider cells
"""

import re

def move_dsr_badge_right():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Update the CSS for the badge to float right
    old_badge_css = r'\.dsr-badge \{[^}]*\}'
    new_badge_css = '''.dsr-badge {
            display: inline-flex;
            align-items: center;
            background: #2ecc71;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            border: 1px solid #27ae60;
            vertical-align: middle;
            float: right;
            margin-right: 5px;
        }'''
    
    content = re.sub(old_badge_css, new_badge_css, content, flags=re.DOTALL)
    
    # Add CSS for provider cells to handle the float properly
    style_end = content.find('</style>')
    if style_end != -1:
        additional_css = '''
        /* Provider cell styling for badge alignment */
        .provider-cell {
            position: relative;
            overflow: hidden;
        }
        
        .provider-text {
            display: inline-block;
            max-width: calc(100% - 50px);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        '''
        content = content[:style_end] + additional_css + '\n    ' + content[style_end:]
    
    # Update WAN1 provider cell structure
    wan1_pattern = r'<td>\s*{{ entry\.wan1\.provider if entry\.wan1\.provider else \'N/A\' }}\s*{% if entry\.wan1\.match_info and entry\.wan1\.match_info\.dsr_verified %}\s*<span class="dsr-badge">DSR</span>\s*{% endif %}\s*</td>'
    wan1_replacement = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''
    
    content = re.sub(wan1_pattern, wan1_replacement, content, flags=re.DOTALL)
    
    # Update WAN2 provider cell structure
    wan2_pattern = r'<td>\s*{{ entry\.wan2\.provider if entry\.wan2\.provider else \'N/A\' }}\s*{% if entry\.wan2\.match_info and entry\.wan2\.match_info\.dsr_verified %}\s*<span class="dsr-badge">DSR</span>\s*{% endif %}\s*</td>'
    wan2_replacement = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''
    
    content = re.sub(wan2_pattern, wan2_replacement, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Moved DSR badge to the right side of provider cells")

if __name__ == "__main__":
    move_dsr_badge_right()