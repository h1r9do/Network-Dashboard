#!/usr/bin/env python3
"""
Create SVG badge for DSR verified providers
"""

# SVG content for the DSR badge
dsr_badge_svg = '''<svg width="40" height="20" viewBox="0 0 40 20" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect x="0" y="0" width="40" height="20" rx="3" fill="#2ecc71" stroke="#27ae60" stroke-width="1"/>
  
  <!-- DSR Text -->
  <text x="8" y="14" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white">DSR</text>
  
  <!-- Checkmark -->
  <path d="M 28 6 L 31 9 L 36 4" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  
  <!-- Circle around checkmark -->
  <circle cx="32" cy="10" r="7" fill="none" stroke="white" stroke-width="1.5"/>
</svg>'''

# Save as static file
with open('/usr/local/bin/static/dsr-badge.svg', 'w') as f:
    f.write(dsr_badge_svg)

print("✅ Created DSR badge SVG")

# Also create CSS for inline badge
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
}

.dsr-badge::after {
    content: "✓";
    margin-left: 4px;
    font-size: 12px;
}

.dsr-badge-wan1 {
    /* Specific styling for WAN1 if needed */
}

.dsr-badge-wan2 {
    /* Specific styling for WAN2 if needed */
}
'''

print("\nCSS for badge styling:")
print(badge_css)