#!/usr/bin/env python3
"""
Reduce site name by 50% and split that space between the two provider columns
"""

import re

def adjust_column_widths_v4():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Calculate new widths:
    # Current: Site Name = 13.125%
    # Reduce by 50%: 13.125% * 0.5 = 6.5625%
    # Space freed up: 13.125% - 6.5625% = 6.5625%
    # Split between providers: 6.5625% / 2 = 3.28125% each
    # 
    # New widths:
    # Site Name: 6.5625% (reduced by 50%)
    # WAN1 Provider: 29.0625% + 3.28125% = 32.34375%
    # WAN1 Speed: 6.25% (unchanged)
    # WAN1 Cost: 6.5625% (unchanged)
    # WAN2 Provider: 29.0625% + 3.28125% = 32.34375%
    # WAN2 Speed: 6.25% (unchanged)
    # WAN2 Cost: 6.5625% (unchanged)
    # Action: 3.125% (unchanged)
    # Total: 6.5625 + 32.34375 + 6.25 + 6.5625 + 32.34375 + 6.25 + 6.5625 + 3.125 = 100%
    
    # Update Site Name widths
    content = re.sub(
        r'width: 13\.125%; }  /\* Site Name \*/',
        'width: 6.5625%; }  /* Site Name */',
        content
    )
    
    # Update WAN1 Provider widths
    content = re.sub(
        r'width: 29\.0625%; }   /\* WAN1 Provider \*/',
        'width: 32.34375%; }   /* WAN1 Provider */',
        content
    )
    
    # Update WAN2 Provider widths
    content = re.sub(
        r'width: 29\.0625%; }   /\* WAN2 Provider \*/',
        'width: 32.34375%; }   /* WAN2 Provider */',
        content
    )
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Updated column widths:")
    print("   Site Name: 6.5625% (reduced by 50%)")
    print("   WAN1 Provider: 32.34375% (gained more space)")
    print("   WAN1 Speed: 6.25% (unchanged)")
    print("   WAN1 Cost: 6.5625% (unchanged)")
    print("   WAN2 Provider: 32.34375% (gained more space)")
    print("   WAN2 Speed: 6.25% (unchanged)")
    print("   WAN2 Cost: 6.5625% (unchanged)")
    print("   Action: 3.125% (unchanged)")

if __name__ == "__main__":
    adjust_column_widths_v4()