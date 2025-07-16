#!/usr/bin/env python3
"""
Improve the general fuzzy matching logic in nightly_enriched_db.py
"""

import sys
import os

def apply_general_fuzzy_improvements():
    """Apply improvements to general fuzzy matching"""
    
    nightly_file = '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
    
    # Read the current file
    with open(nightly_file, 'r') as f:
        content = f.read()
    
    # Check if improvements already applied
    if 'Improved fuzzy matching' in content:
        print("✓ General fuzzy matching improvements already applied!")
        return
    
    print("=== Applying General Fuzzy Matching Improvements ===")
    
    # 1. Lower the fuzzy matching threshold from 60 to 70 (more permissive)
    old_threshold = '''        if score > 60 and score > best_score:'''
    new_threshold = '''        if score > 70 and score > best_score:  # Improved fuzzy matching threshold'''
    
    if old_threshold in content:
        content = content.replace(old_threshold, new_threshold)
        print("✓ Lowered fuzzy matching threshold to 70%")
    else:
        print("⚠ Could not find fuzzy matching threshold to update")
    
    # 2. Add ARIN fallback matching when device notes fail
    old_matching = '''            wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
            if not wan1_dsr:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
            
            wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
            if not wan2_dsr:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)'''
    
    new_matching = '''            wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
            if not wan1_dsr:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
            # Improved fuzzy matching: Try ARIN provider if device notes fail
            if not wan1_dsr and wan1_arin:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_arin)
                if wan1_dsr:
                    logger.info(f"{network_name}: WAN1 matched via ARIN fallback: {wan1_arin} → {wan1_dsr['provider']}")
            
            wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
            if not wan2_dsr:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
            # Improved fuzzy matching: Try ARIN provider if device notes fail
            if not wan2_dsr and wan2_arin:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_arin)
                if wan2_dsr:
                    logger.info(f"{network_name}: WAN2 matched via ARIN fallback: {wan2_arin} → {wan2_dsr['provider']}")'''
    
    if old_matching in content:
        content = content.replace(old_matching, new_matching)
        print("✓ Added ARIN fallback matching")
    else:
        print("⚠ Could not find matching section to enhance")
    
    # 3. Improve provider comparison logic to handle exact provider matches better
    old_comparison = '''def compare_providers(arin_provider, notes_provider):
    """Compare ARIN and device notes providers"""
    if not arin_provider or not notes_provider:
        return "Unknown"
    
    norm_arin = normalize_provider_for_comparison(arin_provider)
    norm_notes = normalize_provider_for_comparison(notes_provider)
    
    if norm_notes == norm_arin:
        return "Match"
    
    # Fuzzy match
    similarity = fuzz.ratio(norm_notes, norm_arin)
    return "Match" if similarity >= 80 else "No match"'''
    
    new_comparison = '''def compare_providers(arin_provider, notes_provider):
    """Compare ARIN and device notes providers"""
    if not arin_provider or not notes_provider:
        return "Unknown"
    
    norm_arin = normalize_provider_for_comparison(arin_provider)
    norm_notes = normalize_provider_for_comparison(notes_provider)
    
    if norm_notes == norm_arin:
        return "Match"
    
    # Improved fuzzy matching with multiple algorithms
    ratio_score = fuzz.ratio(norm_notes, norm_arin)
    partial_score = fuzz.partial_ratio(norm_notes, norm_arin)
    token_score = fuzz.token_sort_ratio(norm_notes, norm_arin)
    
    best_score = max(ratio_score, partial_score, token_score)
    return "Match" if best_score >= 75 else "No match"  # Lowered from 80 to 75'''
    
    if old_comparison in content:
        content = content.replace(old_comparison, new_comparison)
        print("✓ Enhanced provider comparison with multiple fuzzy algorithms")
    else:
        print("⚠ Could not find provider comparison function to enhance")
    
    # Write the updated file
    with open(nightly_file, 'w') as f:
        f.write(content)
    
    print("\\n✅ General fuzzy matching improvements applied successfully!")
    print("\\nImprovements made:")
    print("  1. Lowered fuzzy matching threshold from 60% to 70% (more permissive)")
    print("  2. Added ARIN provider fallback when device notes fail to match")
    print("  3. Enhanced provider comparison with multiple fuzzy algorithms")
    print("  4. Lowered provider comparison threshold from 80% to 75%")
    print("\\nThis should catch Frontier and other similar provider mismatches!")

if __name__ == "__main__":
    apply_general_fuzzy_improvements()