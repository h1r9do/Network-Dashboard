#!/usr/bin/env python3
"""Script to standardize navigation buttons across all HTML templates"""

import re
import os

# Define the standardized navigation HTML
STANDARD_NAV = """        <!-- Standardized Navigation Buttons -->
        <div class="nav-buttons">
            <button onclick="window.location.href='/dsrcircuits'">🏠 Home</button>
            <button onclick="window.location.href='/dsrdashboard'">📊 Status Dashboard</button>
            <button onclick="window.location.href='/dsrhistorical'">📈 Historical Data</button>
            <button onclick="window.location.href='/circuit-enablement-report'">📊 Daily Enablement Report</button>
            <button onclick="window.location.href='/new-stores'">🏗️ New Stores</button>
            <button onclick="window.open('/inventory-summary', '_blank')">📦 Inventory Summary</button>
            <button onclick="window.open('/inventory-details', '_blank')">📋 Inventory Details</button>
        </div>"""

# Define the standard CSS for navigation buttons
STANDARD_NAV_CSS = """        .nav-buttons {
            margin-bottom: 20px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .nav-buttons button {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .nav-buttons button:hover {
            background: #2980b9;
        }
        
        .nav-buttons button.active {
            background: #27ae60;
        }"""

# Map of pages to their active button
PAGE_ACTIVE_BUTTON = {
    'dsrcircuits.html': '🏠 Home',
    'dsrdashboard.html': '📊 Status Dashboard',
    'dsrhistorical.html': '📈 Historical Data',
    'circuit_enablement_report.html': '📊 Daily Enablement Report',
    'new_stores.html': '🏗️ New Stores',
    'inventory_summary.html': '📦 Inventory Summary',
    'inventory_details.html': '📋 Inventory Details'
}

def update_navigation(file_path, active_button):
    """Update navigation in a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Get the page-specific navigation with active class
        nav_html = STANDARD_NAV
        if active_button:
            nav_html = nav_html.replace(f'>{active_button}</button>', f' class="active">{active_button}</button>')
        
        # Pattern to find existing navigation sections
        patterns = [
            r'<div class="export-buttons">.*?</div>',
            r'<div class="nav-buttons">.*?</div>',
            r'<!-- Navigation Buttons -->.*?</div>'
        ]
        
        # Replace existing navigation
        replaced = False
        for pattern in patterns:
            if re.search(pattern, content, re.DOTALL):
                # Special handling for dsrcircuits.html which has a more complex layout
                if 'dsrcircuits.html' in file_path:
                    # Find the export-buttons div with left side buttons
                    export_match = re.search(r'<div class="export-buttons">(.*?)</div>\s*</div>', content, re.DOTALL)
                    if export_match:
                        # Replace just the navigation part, keep other buttons
                        new_nav = f"""<div class="export-buttons">
        <!-- Left side buttons -->
        <div style="display: flex; gap: 8px; align-items: center;">
            <button onclick="window.location.href='/dsrdashboard'">📊 Status Dashboard</button>
            <button onclick="window.location.href='/dsrhistorical'">📈 Historical Data</button>
            <button onclick="window.location.href='/circuit-enablement-report'">📊 Daily Enablement Report</button>
            <button onclick="window.location.href='/new-stores'">🏗️ New Stores</button>
            <button onclick="window.open('/inventory-summary', '_blank')">📦 Inventory Summary</button>
            <button onclick="window.open('/inventory-details', '_blank')">📋 Inventory Details</button>"""
                        content = re.sub(r'<div class="export-buttons">.*?<button onclick="window\.open\(\'/inventory-details\'[^>]+>[^<]+</button>', 
                                       new_nav, content, count=1, flags=re.DOTALL)
                        replaced = True
                else:
                    content = re.sub(pattern, nav_html, content, count=1, flags=re.DOTALL)
                    replaced = True
                break
        
        # If no navigation found, try to insert after container div
        if not replaced:
            container_match = re.search(r'<div class="container">[\s\n]*', content)
            if container_match:
                insert_pos = container_match.end()
                content = content[:insert_pos] + nav_html + '\n\n' + content[insert_pos:]
                replaced = True
        
        # Update or add CSS if needed
        if '.nav-buttons' not in content and 'nav-buttons' in nav_html:
            # Find where to insert CSS
            style_end = content.rfind('</style>')
            if style_end != -1:
                content = content[:style_end] + '\n' + STANDARD_NAV_CSS + '\n    </style>' + content[style_end+8:]
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated navigation in {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update navigation in all template files"""
    template_dir = '/usr/local/bin/templates'
    
    # Files to update
    files_to_update = [
        'dsrcircuits.html',
        'dsrdashboard.html', 
        'dsrhistorical.html',
        'circuit_enablement_report.html',
        'inventory_summary.html',
        'inventory_details.html'
    ]
    
    print("🔧 Standardizing navigation buttons across all pages...")
    
    for filename in files_to_update:
        file_path = os.path.join(template_dir, filename)
        if os.path.exists(file_path):
            active_button = PAGE_ACTIVE_BUTTON.get(filename)
            update_navigation(file_path, active_button)
        else:
            print(f"⚠️  File not found: {filename}")
    
    print("\n✨ Navigation standardization complete!")

if __name__ == "__main__":
    main()