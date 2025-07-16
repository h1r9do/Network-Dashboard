#!/usr/bin/env python3
"""
Reduce cost columns by another 30% and add that space to provider columns
"""

import re

def adjust_column_widths_v3():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Calculate new widths:
    # Current: WAN1 Cost = 9.375%, WAN2 Cost = 9.375%
    # Reduce by 30%: 9.375% * 0.7 = 6.5625%
    # Space freed up: (9.375% - 6.5625%) * 2 = 5.625% total
    # Add to providers: 5.625% / 2 = 2.8125% each
    # 
    # New widths:
    # Site Name: 13.125% (unchanged)
    # WAN1 Provider: 26.25% + 2.8125% = 29.0625%
    # WAN1 Speed: 6.25% (unchanged)
    # WAN1 Cost: 6.5625% (reduced by 30%)
    # WAN2 Provider: 26.25% + 2.8125% = 29.0625%
    # WAN2 Speed: 6.25% (unchanged)
    # WAN2 Cost: 6.5625% (reduced by 30%)
    # Action: 3.125% (unchanged)
    # Total: 13.125 + 29.0625 + 6.25 + 6.5625 + 29.0625 + 6.25 + 6.5625 + 3.125 = 100%
    
    # Update WAN1 Provider widths
    content = re.sub(
        r'width: 26\.25%; }   /\* WAN1 Provider \*/',
        'width: 29.0625%; }   /* WAN1 Provider */',
        content
    )
    
    # Update WAN1 Cost widths
    content = re.sub(
        r'width: 9\.375%; }   /\* WAN1 Cost \*/',
        'width: 6.5625%; }   /* WAN1 Cost */',
        content
    )
    
    # Update WAN2 Provider widths
    content = re.sub(
        r'width: 26\.25%; }   /\* WAN2 Provider \*/',
        'width: 29.0625%; }   /* WAN2 Provider */',
        content
    )
    
    # Update WAN2 Cost widths
    content = re.sub(
        r'width: 9\.375%; }   /\* WAN2 Cost \*/',
        'width: 6.5625%; }   /* WAN2 Cost */',
        content
    )
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Updated column widths:")
    print("   Site Name: 13.125% (unchanged)")
    print("   WAN1 Provider: 29.0625% (gained more space)")
    print("   WAN1 Speed: 6.25% (unchanged)")
    print("   WAN1 Cost: 6.5625% (reduced by 30%)")
    print("   WAN2 Provider: 29.0625% (gained more space)")
    print("   WAN2 Speed: 6.25% (unchanged)")
    print("   WAN2 Cost: 6.5625% (reduced by 30%)")
    print("   Action: 3.125% (unchanged)")

if __name__ == "__main__":
    adjust_column_widths_v3()