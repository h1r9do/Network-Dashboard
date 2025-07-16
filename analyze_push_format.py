#!/usr/bin/env python3
"""
Analyze the push output log to count clean vs non-clean formats
"""

def analyze_push_log():
    """Analyze which sites had clean simplified format"""
    
    clean_format_count = 0
    cell_only_count = 0
    single_wan_count = 0
    total_sites = 0
    
    current_site = None
    current_notes = []
    
    with open('/tmp/push_output.log', 'r') as f:
        for line in f:
            line = line.strip()
            
            # New site
            if line.startswith('[') and '] Processing' in line:
                # Process previous site if exists
                if current_site and current_notes:
                    total_sites += 1
                    notes_text = '\n'.join(current_notes)
                    
                    # Count different formats
                    if 'Cell' in notes_text and len(current_notes) == 3:
                        # Single WAN with Cell (e.g., "WAN 2\nDigi\nCell")
                        cell_only_count += 1
                    elif len(current_notes) == 3:
                        # Single WAN clean format (e.g., "WAN 1\nProvider\nSpeed")
                        single_wan_count += 1
                    elif len(current_notes) == 6:
                        # Dual WAN clean format (e.g., "WAN 1\nProvider\nSpeed\nWAN 2\nProvider\nSpeed")
                        clean_format_count += 1
                    elif 'Cell' in notes_text and len(current_notes) == 6:
                        # Dual WAN with one being Cell
                        clean_format_count += 1
                
                # Reset for new site
                current_site = line
                current_notes = []
            
            # Collect notes lines (indented with spaces)
            elif line.startswith('  ') and line not in ['  Notes format:', '  ✓ Successfully updated', '  ✗ Failed to update'] and not line.startswith('  ✓') and not line.startswith('  ✗'):
                if line.strip():  # Only add non-empty lines
                    current_notes.append(line.strip())
        
        # Process last site
        if current_site and current_notes:
            total_sites += 1
            notes_text = '\n'.join(current_notes)
            
            if 'Cell' in notes_text and len(current_notes) == 3:
                cell_only_count += 1
            elif len(current_notes) == 3:
                single_wan_count += 1
            elif len(current_notes) == 6:
                clean_format_count += 1
            elif 'Cell' in notes_text and len(current_notes) == 6:
                clean_format_count += 1
    
    print("=== Push Format Analysis ===")
    print(f"Total sites pushed: {total_sites}")
    print(f"\nFormat breakdown:")
    print(f"Clean dual WAN format (6 lines): {clean_format_count}")
    print(f"Single WAN format (3 lines): {single_wan_count}")
    print(f"Cell-only format (3 lines): {cell_only_count}")
    print(f"Other formats: {total_sites - clean_format_count - single_wan_count - cell_only_count}")
    
    if total_sites > 0:
        print(f"\nClean simplified format: {clean_format_count + single_wan_count} sites ({(clean_format_count + single_wan_count)/total_sites*100:.1f}%)")
        print(f"Cell-only format: {cell_only_count} sites ({cell_only_count/total_sites*100:.1f}%)")
    else:
        print("\nNo sites found in log file")

if __name__ == "__main__":
    analyze_push_log()