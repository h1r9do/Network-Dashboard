#!/usr/bin/env python3
"""
Patch to add ARIN = Device Notes matching logic to nightly_enriched_db.py
"""

import sys
import os

def apply_arin_notes_patch():
    """Apply the ARIN = Device Notes matching patch"""
    
    nightly_file = '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
    
    # Read the current file
    with open(nightly_file, 'r') as f:
        content = f.read()
    
    # Check if patch is already applied
    if 'ARIN equals device notes' in content:
        print("✓ ARIN = Device Notes patch already applied!")
        return
    
    # Find the normal matching section and add our logic
    old_section = '''            # Normal matching - WAN1 to Primary, WAN2 to Secondary
            wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
            if not wan1_dsr:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
            
            wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
            if not wan2_dsr:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)'''
    
    new_section = '''            # Normal matching - WAN1 to Primary, WAN2 to Secondary
            wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
            if not wan1_dsr:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
            
            # Enhanced matching: If ARIN equals device notes, try fuzzy matching against all circuits
            if not wan1_dsr and wan1_notes and wan1_arin:
                if wan1_notes.lower().strip() == wan1_arin.lower().strip():
                    logger.debug(f"{network_name}: WAN1 ARIN equals device notes ({wan1_arin}), trying fuzzy match")
                    for circuit in dsr_circuits:
                        if providers_match_for_sync(circuit['provider'], wan1_arin):
                            wan1_dsr = circuit
                            logger.info(f"{network_name}: WAN1 matched via ARIN=Notes logic: {wan1_arin} → {circuit['provider']}")
                            break
            
            wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
            if not wan2_dsr:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
            
            # Enhanced matching: If ARIN equals device notes, try fuzzy matching against all circuits
            if not wan2_dsr and wan2_notes and wan2_arin:
                if wan2_notes.lower().strip() == wan2_arin.lower().strip():
                    logger.debug(f"{network_name}: WAN2 ARIN equals device notes ({wan2_arin}), trying fuzzy match")
                    for circuit in dsr_circuits:
                        if providers_match_for_sync(circuit['provider'], wan2_arin):
                            wan2_dsr = circuit
                            logger.info(f"{network_name}: WAN2 matched via ARIN=Notes logic: {wan2_arin} → {circuit['provider']}")
                            break'''
    
    if old_section in content:
        # Apply the patch
        new_content = content.replace(old_section, new_section)
        
        # Write the updated file
        with open(nightly_file, 'w') as f:
            f.write(new_content)
        
        print("✓ ARIN = Device Notes matching patch applied successfully!")
        print("  - Added enhanced matching logic when ARIN equals device notes")
        print("  - Uses Frontier fuzzy matching for provider comparison")
        
    else:
        print("✗ Could not find the target section to patch")
        print("The file may have been modified or the matching logic changed")

if __name__ == "__main__":
    apply_arin_notes_patch()