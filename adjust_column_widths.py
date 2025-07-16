#!/usr/bin/env python3
"""
Adjust column widths: reduce site name by 75%, reduce speeds by 50%, give extra space to providers
"""

import re

def adjust_column_widths():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Calculate new widths:
    # Original: 12.5% each (100% / 8 = 12.5%)
    # Site Name: 12.5% * 0.25 = 3.125% (reduced by 75%)
    # WAN1 Provider: 12.5% + (12.5% * 0.75) = 21.875% (gets site name's space)
    # WAN1 Speed: 12.5% * 0.5 = 6.25% (reduced by 50%)
    # WAN1 Cost: 12.5% + (12.5% * 0.5) = 18.75% (gets speed's space)
    # WAN2 Provider: 21.875% (same as WAN1 Provider)
    # WAN2 Speed: 6.25% (same as WAN1 Speed)
    # WAN2 Cost: 18.75% (same as WAN1 Cost)
    # Action: 3.125% (same as Site Name)
    
    # Remove the generic width rule and add specific column widths
    table_css = r'\.circuit-table\s*\{[^}]*\}\s*\.circuit-table\s+th,\s*\.circuit-table\s+td\s*\{[^}]*\}'
    new_table_css = '''        .circuit-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .circuit-table th, .circuit-table td {
            text-align: left;
            padding: 8px;
            border: 1px solid #ddd;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .circuit-table th:nth-child(1), .circuit-table td:nth-child(1) { width: 3.125%; }   /* Site Name */
        .circuit-table th:nth-child(2), .circuit-table td:nth-child(2) { width: 21.875%; }  /* WAN1 Provider */
        .circuit-table th:nth-child(3), .circuit-table td:nth-child(3) { width: 6.25%; }    /* WAN1 Speed */
        .circuit-table th:nth-child(4), .circuit-table td:nth-child(4) { width: 18.75%; }   /* WAN1 Cost */
        .circuit-table th:nth-child(5), .circuit-table td:nth-child(5) { width: 21.875%; }  /* WAN2 Provider */
        .circuit-table th:nth-child(6), .circuit-table td:nth-child(6) { width: 6.25%; }    /* WAN2 Speed */
        .circuit-table th:nth-child(7), .circuit-table td:nth-child(7) { width: 18.75%; }   /* WAN2 Cost */
        .circuit-table th:nth-child(8), .circuit-table td:nth-child(8) { width: 3.125%; }   /* Action */'''
    
    content = re.sub(table_css, new_table_css, content, flags=re.DOTALL)
    
    # Update filter-control CSS to match the same widths
    filter_control_css = r'\.filter-control\s*\{[^}]*\}'
    new_filter_control_css = '''        .filter-control {
            display: table-cell;
            padding: 5px;
            border-right: 1px solid #ddd;
            vertical-align: top;
        }
        .filter-control:nth-child(1) { width: 3.125%; }   /* Site Name */
        .filter-control:nth-child(2) { width: 21.875%; }  /* WAN1 Provider */
        .filter-control:nth-child(3) { width: 6.25%; }    /* WAN1 Speed */
        .filter-control:nth-child(4) { width: 18.75%; }   /* WAN1 Cost */
        .filter-control:nth-child(5) { width: 21.875%; }  /* WAN2 Provider */
        .filter-control:nth-child(6) { width: 6.25%; }    /* WAN2 Speed */
        .filter-control:nth-child(7) { width: 18.75%; }   /* WAN2 Cost */
        .filter-control:nth-child(8) { width: 3.125%; }   /* Action */'''
    
    content = re.sub(filter_control_css, new_filter_control_css, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Updated column widths:")
    print("   Site Name: 3.125% (reduced by 75%)")
    print("   WAN1 Provider: 21.875% (gained extra space)")
    print("   WAN1 Speed: 6.25% (reduced by 50%)")
    print("   WAN1 Cost: 18.75% (gained extra space)")
    print("   WAN2 Provider: 21.875% (gained extra space)")
    print("   WAN2 Speed: 6.25% (reduced by 50%)")
    print("   WAN2 Cost: 18.75% (gained extra space)")
    print("   Action: 3.125% (same as Site Name)")

if __name__ == "__main__":
    adjust_column_widths()