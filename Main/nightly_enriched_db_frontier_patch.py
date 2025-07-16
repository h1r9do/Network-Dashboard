#!/usr/bin/env python3
"""
Patch to add Frontier fuzzy matching to nightly_enriched_db.py
"""

import sys
import os

def apply_frontier_patch():
    """Apply the Frontier fuzzy matching patch"""
    
    nightly_file = '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
    
    # Read the current file
    with open(nightly_file, 'r') as f:
        content = f.read()
    
    # Check if patch is already applied
    if 'def is_frontier_provider' in content:
        print("✓ Frontier patch already applied!")
        return
    
    # Find the providers_match_for_sync function and replace it
    old_function = '''def providers_match_for_sync(dsr_provider, arin_provider):
    """Check if DSR and ARIN providers match well enough to sync DSR data"""
    if not dsr_provider or not arin_provider:
        return False
    
    dsr_norm = normalize_provider_for_arin_match(dsr_provider)
    arin_norm = normalize_provider_for_arin_match(arin_provider)
    
    return dsr_norm == arin_norm'''
    
    new_function = '''def is_frontier_provider(provider_name):
    """Check if a provider name is a Frontier variant"""
    if not provider_name:
        return False
    return 'frontier' in provider_name.lower()

def providers_match_for_sync(dsr_provider, arin_provider):
    """Check if DSR and ARIN providers match well enough to sync DSR data"""
    if not dsr_provider or not arin_provider:
        return False
    
    # Special handling for Frontier variants
    if is_frontier_provider(dsr_provider) and is_frontier_provider(arin_provider):
        logger.debug(f"Frontier variant match: DSR '{dsr_provider}' matches ARIN '{arin_provider}'")
        return True
    
    dsr_norm = normalize_provider_for_arin_match(dsr_provider)
    arin_norm = normalize_provider_for_arin_match(arin_provider)
    
    return dsr_norm == arin_norm'''
    
    if old_function in content:
        # Apply the patch
        new_content = content.replace(old_function, new_function)
        
        # Write the updated file
        with open(nightly_file, 'w') as f:
            f.write(new_content)
        
        print("✓ Frontier fuzzy matching patch applied successfully!")
        print("  - Added is_frontier_provider() function")
        print("  - Updated providers_match_for_sync() with Frontier logic")
        
    else:
        print("✗ Could not find the target function to patch")
        print("The file may have been modified or the function signature changed")

if __name__ == "__main__":
    apply_frontier_patch()