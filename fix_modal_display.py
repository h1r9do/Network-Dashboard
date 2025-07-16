#!/usr/bin/env python3
"""
Fix the modal display issue for Meraki MX Notes
This updates the JavaScript to properly display newlines
"""

import os
from datetime import datetime

def main():
    """Fix modal display in dsrcircuits.html"""
    print("🔧 Fixing Modal Display for Meraki MX Notes")
    print("=" * 60)
    
    template_file = "/usr/local/bin/templates/dsrcircuits.html"
    
    # Read the current template
    with open(template_file, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file = f"{template_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✅ Created backup: {backup_file}")
    
    # Find and replace the problematic line
    old_line = "$('#modalRawNotes').text(response.raw_notes || 'No Meraki notes available');"
    
    # Two possible fixes:
    # Option 1: Use html() with br tags
    new_line_html = """var notes = response.raw_notes || 'No Meraki notes available';
                    // Replace newlines with <br> for proper display
                    var formattedNotes = notes.replace(/\\n/g, '<br>');
                    $('#modalRawNotes').html(formattedNotes);"""
    
    # Option 2: Use CSS white-space
    new_line_css = """$('#modalRawNotes').css('white-space', 'pre-wrap').text(response.raw_notes || 'No Meraki notes available');"""
    
    # Let's use Option 2 (CSS) as it's safer (no HTML injection risk)
    if old_line in content:
        content = content.replace(old_line, new_line_css)
        print("✅ Updated JavaScript to use white-space: pre-wrap")
        
        # Write the updated content
        with open(template_file, 'w') as f:
            f.write(content)
        print("✅ Updated dsrcircuits.html")
    else:
        print("⚠️  Could not find the exact line to replace")
        print("   Searching for alternative patterns...")
        
        # Try a more flexible search
        import re
        pattern = r"\$\('#modalRawNotes'\)\.text\([^)]+\);"
        matches = re.findall(pattern, content)
        if matches:
            print(f"   Found: {matches[0]}")
            content = re.sub(pattern, new_line_css, content)
            with open(template_file, 'w') as f:
                f.write(content)
            print("✅ Updated dsrcircuits.html with regex replacement")
        else:
            print("❌ Could not find modalRawNotes assignment")
    
    print("\n📝 The modal will now properly display newlines in the notes!")
    print("   Users may need to refresh their browser (Ctrl+F5) to see the change.")

if __name__ == "__main__":
    main()