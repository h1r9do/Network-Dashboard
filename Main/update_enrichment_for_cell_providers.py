#!/usr/bin/env python3
"""
Update the nightly enrichment script to better handle Cell/Satellite provider matching
"""

import re

def get_updated_matching_logic():
    """Return the improved provider matching logic for enrichment"""
    
    return '''
def normalize_provider_for_matching(provider):
    """Normalize provider names for better matching"""
    if not provider:
        return ""
    
    # Common cellular provider normalizations
    provider_lower = provider.lower().strip()
    
    # Cell provider mappings
    if 'vzw' in provider_lower or 'verizon' in provider_lower:
        return 'verizon'
    elif 'at&t' in provider_lower or 'att' in provider_lower or 'digi' in provider_lower:
        return 'at&t'
    elif 'starlink' in provider_lower or 'spacex' in provider_lower:
        return 'spacex'
    elif 'firstnet' in provider_lower or 'first digital' in provider_lower:
        return 'firstnet'
    elif 't-mobile' in provider_lower or 'tmobile' in provider_lower:
        return 't-mobile'
    
    # Remove common suffixes
    cleaned = re.sub(r'\s*(cell|wireless|broadband|fiber|dedicated|communications).*$', '', provider_lower)
    
    return cleaned.strip()

def match_dsr_circuit_by_provider(dsr_circuits, provider_name, network_name=None):
    """
    Match DSR circuit by provider name using improved fuzzy matching.
    """
    if not provider_name:
        return None
    
    # Normalize the provider for matching
    normalized_provider = normalize_provider_for_matching(provider_name)
    
    best_match = None
    best_score = 0
    
    for circuit in dsr_circuits:
        if circuit['site_name'] != network_name:
            continue
        
        # Normalize circuit provider
        circuit_provider_normalized = normalize_provider_for_matching(circuit['provider_name'])
        
        # First try exact match on normalized names
        if normalized_provider == circuit_provider_normalized:
            # Prefer exact matches
            return circuit
        
        # Then try fuzzy matching
        score = max(
            fuzz.ratio(provider_name.lower(), circuit['provider_name'].lower()),
            fuzz.partial_ratio(provider_name.lower(), circuit['provider_name'].lower()),
            fuzz.ratio(normalized_provider, circuit_provider_normalized) * 1.2  # Boost normalized matches
        )
        
        # Lower threshold to 70% and prefer normalized matches
        if score > 70 and score > best_score:
            best_match = circuit
            best_score = score
    
    # Log the best match found
    if best_match and network_name:
        logger.info(f"{network_name}: Matched '{provider_name}' to '{best_match['provider_name']}' (score: {best_score:.1f}%)")
    
    return best_match
'''

def main():
    """Show the updated enrichment logic"""
    
    print("=== Updated Enrichment Logic for Cell/Satellite Providers ===\n")
    print("This logic should be added to nightly_enriched_db.py:\n")
    print(get_updated_matching_logic())
    
    print("\n\n=== Key Improvements ===")
    print("1. Normalizes cellular providers (VZW Cell → verizon, AT&T Cell → at&t)")
    print("2. Removes common suffixes (Cell, Wireless, Communications)")
    print("3. Boosts scores for normalized matches (x1.2)")
    print("4. Logs successful matches for visibility")
    print("\n=== Expected Results ===")
    print("- 'VZW Cell' will match 'Verizon' circuits")
    print("- 'AT&T Cell' will match 'AT&T' circuits")
    print("- 'Digi' will match 'AT&T' circuits")
    print("- 'Starlink' will match 'SpaceX' circuits")

if __name__ == "__main__":
    main()