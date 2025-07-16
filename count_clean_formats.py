#!/usr/bin/env python3
"""
Count how many sites had clean simplified format
"""

def count_formats():
    """Count different note formats from push log"""
    
    # Read all lines
    with open('/tmp/push_output.log', 'r') as f:
        content = f.read()
    
    # Split by processing entries
    entries = content.split('[')[1:]  # Skip first empty part
    
    clean_dual_wan = 0  # WAN 1 + provider + speed + WAN 2 + provider + speed
    clean_single_wan = 0  # Only WAN 1 with provider and speed
    wan_with_cell = 0  # Has "Cell" as the speed
    other_format = 0
    
    for entry in entries:
        if 'Notes format:' not in entry:
            continue
            
        # Extract notes section
        notes_start = entry.find('Notes format:')
        notes_end = entry.find('✓ Successfully') if '✓ Successfully' in entry else entry.find('✗ Failed')
        
        if notes_start == -1 or notes_end == -1:
            continue
            
        notes_section = entry[notes_start:notes_end].strip()
        lines = [line.strip() for line in notes_section.split('\n') if line.strip() and line.strip() != 'Notes format:']
        
        # Analyze format
        has_wan1 = 'WAN 1' in lines
        has_wan2 = 'WAN 2' in lines
        has_cell = 'Cell' in lines
        
        # Count lines per WAN
        if has_wan1 and has_wan2:
            # Dual WAN - should have 6 lines total (3 per WAN)
            if len(lines) == 6:
                if has_cell:
                    wan_with_cell += 1
                else:
                    clean_dual_wan += 1
            else:
                other_format += 1
        elif has_wan1 or has_wan2:
            # Single WAN - should have 3 lines
            if len(lines) == 3:
                if has_cell:
                    wan_with_cell += 1
                else:
                    clean_single_wan += 1
            else:
                other_format += 1
        else:
            other_format += 1
    
    total = clean_dual_wan + clean_single_wan + wan_with_cell + other_format
    
    print("=== Clean Format Analysis ===")
    print(f"Total sites analyzed: {total}")
    print(f"\nBreakdown:")
    print(f"Clean dual WAN format: {clean_dual_wan} ({clean_dual_wan/total*100:.1f}%)")
    print(f"Clean single WAN format: {clean_single_wan} ({clean_single_wan/total*100:.1f}%)")
    print(f"WAN with Cell: {wan_with_cell} ({wan_with_cell/total*100:.1f}%)")
    print(f"Other formats: {other_format} ({other_format/total*100:.1f}%)")
    
    clean_total = clean_dual_wan + clean_single_wan
    print(f"\n✅ Total clean simplified format: {clean_total} sites ({clean_total/total*100:.1f}%)")
    print(f"📱 Cell format: {wan_with_cell} sites ({wan_with_cell/total*100:.1f}%)")
    
    # Show some examples
    print("\nExample formats found:")
    for i, entry in enumerate(entries[:5]):
        if 'Notes format:' in entry:
            print(f"\nSite {i+1}:")
            notes_start = entry.find('Notes format:')
            notes_end = entry.find('✓ Successfully') if '✓ Successfully' in entry else entry.find('✗ Failed')
            if notes_start != -1 and notes_end != -1:
                notes = entry[notes_start:notes_end].strip()
                for line in notes.split('\n')[1:]:  # Skip "Notes format:"
                    if line.strip():
                        print(f"  {line.strip()}")

if __name__ == "__main__":
    count_formats()