#!/usr/bin/env python3
"""
Adjust column widths: increase site name by 10%, reduce cost columns by 50%, add that space to providers
"""

import re

def adjust_column_widths_v2():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Calculate new widths:
    # Current: Site=3.125%, WAN1Prov=21.875%, WAN1Speed=6.25%, WAN1Cost=18.75%, WAN2Prov=21.875%, WAN2Speed=6.25%, WAN2Cost=18.75%, Action=3.125%
    # 
    # Site Name: 3.125% + 10% = 13.125% (increased by 10%)
    # WAN1 Cost: 18.75% * 0.5 = 9.375% (reduced by 50%)
    # WAN2 Cost: 18.75% * 0.5 = 9.375% (reduced by 50%)
    # 
    # Space freed up: (18.75% - 9.375%) * 2 = 18.75% total
    # Plus site name needs: 13.125% - 3.125% = 10%
    # Remaining for providers: 18.75% - 10% = 8.75%
    # 
    # WAN1 Provider: 21.875% + 4.375% = 26.25%
    # WAN2 Provider: 21.875% + 4.375% = 26.25%
    # 
    # Final widths:
    # Site: 13.125%, WAN1Prov: 26.25%, WAN1Speed: 6.25%, WAN1Cost: 9.375%, WAN2Prov: 26.25%, WAN2Speed: 6.25%, WAN2Cost: 9.375%, Action: 3.125%
    # Total: 13.125 + 26.25 + 6.25 + 9.375 + 26.25 + 6.25 + 9.375 + 3.125 = 100%
    
    # Update table CSS with new widths
    table_css = r'\.circuit-table\s*\{[^}]*\}\s*\.circuit-table\s+th,\s*\.circuit-table\s+td\s*\{[^}]*\}\s*\.circuit-table\s+th:nth-child\(1\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(2\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(3\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(4\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(5\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(6\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(7\)[^}]*\}\s*\.circuit-table\s+th:nth-child\(8\)[^}]*\}'
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
        .circuit-table th:nth-child(1), .circuit-table td:nth-child(1) { width: 13.125%; }  /* Site Name */
        .circuit-table th:nth-child(2), .circuit-table td:nth-child(2) { width: 26.25%; }   /* WAN1 Provider */
        .circuit-table th:nth-child(3), .circuit-table td:nth-child(3) { width: 6.25%; }    /* WAN1 Speed */
        .circuit-table th:nth-child(4), .circuit-table td:nth-child(4) { width: 9.375%; }   /* WAN1 Cost */
        .circuit-table th:nth-child(5), .circuit-table td:nth-child(5) { width: 26.25%; }   /* WAN2 Provider */
        .circuit-table th:nth-child(6), .circuit-table td:nth-child(6) { width: 6.25%; }    /* WAN2 Speed */
        .circuit-table th:nth-child(7), .circuit-table td:nth-child(7) { width: 9.375%; }   /* WAN2 Cost */
        .circuit-table th:nth-child(8), .circuit-table td:nth-child(8) { width: 3.125%; }   /* Action */'''
    
    content = re.sub(table_css, new_table_css, content, flags=re.DOTALL)
    
    # Update filter-control CSS to match the same widths
    filter_css = r'\.filter-control\s*\{[^}]*\}\s*\.filter-control:nth-child\(1\)[^}]*\}\s*\.filter-control:nth-child\(2\)[^}]*\}\s*\.filter-control:nth-child\(3\)[^}]*\}\s*\.filter-control:nth-child\(4\)[^}]*\}\s*\.filter-control:nth-child\(5\)[^}]*\}\s*\.filter-control:nth-child\(6\)[^}]*\}\s*\.filter-control:nth-child\(7\)[^}]*\}\s*\.filter-control:nth-child\(8\)[^}]*\}'
    new_filter_css = '''        .filter-control {
            display: table-cell;
            padding: 5px;
            border-right: 1px solid #ddd;
            vertical-align: top;
        }
        .filter-control:nth-child(1) { width: 13.125%; }  /* Site Name */
        .filter-control:nth-child(2) { width: 26.25%; }   /* WAN1 Provider */
        .filter-control:nth-child(3) { width: 6.25%; }    /* WAN1 Speed */
        .filter-control:nth-child(4) { width: 9.375%; }   /* WAN1 Cost */
        .filter-control:nth-child(5) { width: 26.25%; }   /* WAN2 Provider */
        .filter-control:nth-child(6) { width: 6.25%; }    /* WAN2 Speed */
        .filter-control:nth-child(7) { width: 9.375%; }   /* WAN2 Cost */
        .filter-control:nth-child(8) { width: 3.125%; }   /* Action */'''
    
    content = re.sub(filter_css, new_filter_css, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Updated column widths:")
    print("   Site Name: 13.125% (increased by 10%)")
    print("   WAN1 Provider: 26.25% (gained extra space)")
    print("   WAN1 Speed: 6.25% (unchanged)")
    print("   WAN1 Cost: 9.375% (reduced by 50%)")
    print("   WAN2 Provider: 26.25% (gained extra space)")
    print("   WAN2 Speed: 6.25% (unchanged)")
    print("   WAN2 Cost: 9.375% (reduced by 50%)")
    print("   Action: 3.125% (unchanged)")

if __name__ == "__main__":
    adjust_column_widths_v2()