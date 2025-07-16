#!/usr/bin/env python3
"""
Enhanced version of nightly_enriched_db.py that uses provider_mappings table
This is a patch that shows the key changes needed
"""

# Add this import at the top of nightly_enriched_db.py
from enhanced_provider_matching_integration import ProviderMatcher

# In the main() function, after getting the database connection, add:
def initialize_provider_matcher(conn):
    """Initialize the enhanced provider matcher"""
    try:
        provider_matcher = ProviderMatcher(conn)
        return provider_matcher
    except Exception as e:
        logger.warning(f"Could not initialize provider matcher: {e}")
        return None

# Replace the existing fuzzy_match_providers function with:
def enhanced_match_circuit(circuit_data, meraki_data, provider_matcher=None):
    """
    Enhanced circuit matching using provider mapping table
    """
    dsr_ip = circuit_data.get('ip_address_start')
    dsr_provider = circuit_data.get('provider_name')
    circuit_purpose = circuit_data.get('circuit_purpose', 'Primary')
    
    if not meraki_data:
        return None
    
    wan1_ip = meraki_data.get('wan1_ip')
    wan2_ip = meraki_data.get('wan2_ip')
    wan1_provider = meraki_data.get('wan1_arin_provider')
    wan2_provider = meraki_data.get('wan2_arin_provider')
    
    # Direct IP match
    if dsr_ip == wan1_ip:
        if provider_matcher and wan1_provider:
            is_match, confidence, reason = provider_matcher.match_providers(
                dsr_provider, wan1_provider, circuit_purpose
            )
            if is_match:
                return {
                    'wan_port': 'WAN1',
                    'matched_ip': wan1_ip,
                    'arin_provider': wan1_provider,
                    'match_confidence': confidence,
                    'match_reason': reason
                }
        else:
            # Fallback to simple match
            return {
                'wan_port': 'WAN1',
                'matched_ip': wan1_ip,
                'arin_provider': wan1_provider,
                'match_confidence': 100,
                'match_reason': 'IP match'
            }
    
    elif dsr_ip == wan2_ip:
        if provider_matcher and wan2_provider:
            is_match, confidence, reason = provider_matcher.match_providers(
                dsr_provider, wan2_provider, circuit_purpose
            )
            if is_match:
                return {
                    'wan_port': 'WAN2',
                    'matched_ip': wan2_ip,
                    'arin_provider': wan2_provider,
                    'match_confidence': confidence,
                    'match_reason': reason
                }
        else:
            return {
                'wan_port': 'WAN2',
                'matched_ip': wan2_ip,
                'arin_provider': wan2_provider,
                'match_confidence': 100,
                'match_reason': 'IP match'
            }
    
    # No direct IP match, try provider matching
    if provider_matcher and dsr_provider:
        # Try WAN1
        if wan1_provider:
            is_match, confidence, reason = provider_matcher.match_providers(
                dsr_provider, wan1_provider, circuit_purpose
            )
            if is_match and confidence >= 70:
                return {
                    'wan_port': 'WAN1',
                    'matched_ip': wan1_ip,
                    'arin_provider': wan1_provider,
                    'match_confidence': confidence,
                    'match_reason': f'Provider match: {reason}'
                }
        
        # Try WAN2
        if wan2_provider:
            is_match, confidence, reason = provider_matcher.match_providers(
                dsr_provider, wan2_provider, circuit_purpose
            )
            if is_match and confidence >= 70:
                return {
                    'wan_port': 'WAN2',
                    'matched_ip': wan2_ip,
                    'arin_provider': wan2_provider,
                    'match_confidence': confidence,
                    'match_reason': f'Provider match: {reason}'
                }
    
    return None

# In the process_enrichment function, update the matching logic:
def process_enrichment_with_mappings(conn, provider_matcher):
    """
    Modified enrichment process using provider mappings
    """
    cursor = conn.cursor()
    
    # Get circuits that need enrichment
    cursor.execute("""
        SELECT 
            site_id,
            site_name,
            circuit_purpose,
            provider_name,
            ip_address_start,
            details_ordered_service_speed,
            billing_monthly_cost
        FROM circuits
        WHERE status = 'Enabled'
        ORDER BY site_name, circuit_purpose
    """)
    
    circuits = cursor.fetchall()
    enriched_count = 0
    
    for circuit in circuits:
        site_id = circuit[0]
        site_name = circuit[1]
        circuit_purpose = circuit[2]
        dsr_provider = circuit[3]
        
        # Get Meraki data for this site
        cursor.execute("""
            SELECT 
                wan1_ip, wan1_arin_provider, wan1_provider_label,
                wan2_ip, wan2_arin_provider, wan2_provider_label,
                device_notes
            FROM meraki_inventory
            WHERE network_name = %s
            AND device_model LIKE 'MX%'
            ORDER BY last_updated DESC
            LIMIT 1
        """, (site_name,))
        
        meraki_row = cursor.fetchone()
        if not meraki_row:
            continue
        
        meraki_data = {
            'wan1_ip': meraki_row[0],
            'wan1_arin_provider': meraki_row[1],
            'wan1_provider_label': meraki_row[2],
            'wan2_ip': meraki_row[3],
            'wan2_arin_provider': meraki_row[4],
            'wan2_provider_label': meraki_row[5],
            'device_notes': meraki_row[6]
        }
        
        circuit_data = {
            'ip_address_start': circuit[4],
            'provider_name': dsr_provider,
            'circuit_purpose': circuit_purpose
        }
        
        # Use enhanced matching
        match_result = enhanced_match_circuit(circuit_data, meraki_data, provider_matcher)
        
        if match_result:
            # Update enriched_circuits table
            cursor.execute("""
                INSERT INTO enriched_circuits (
                    site_id, circuit_purpose, dsr_provider, 
                    arin_provider, wan_port, match_confidence,
                    match_reason, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (site_id, circuit_purpose) DO UPDATE SET
                    dsr_provider = EXCLUDED.dsr_provider,
                    arin_provider = EXCLUDED.arin_provider,
                    wan_port = EXCLUDED.wan_port,
                    match_confidence = EXCLUDED.match_confidence,
                    match_reason = EXCLUDED.match_reason,
                    last_updated = NOW()
            """, (
                site_id, circuit_purpose, dsr_provider,
                match_result['arin_provider'], match_result['wan_port'],
                match_result['match_confidence'], match_result['match_reason']
            ))
            
            enriched_count += 1
    
    conn.commit()
    logger.info(f"Enriched {enriched_count} circuits using provider mappings")
    
    return enriched_count

# Example of how to integrate into existing nightly_enriched_db.py:
"""
# In the main() function of nightly_enriched_db.py, add:

def main():
    # ... existing setup code ...
    
    # Initialize provider matcher
    provider_matcher = initialize_provider_matcher(conn)
    if provider_matcher:
        logger.info("Using enhanced provider matching with mappings table")
    else:
        logger.info("Provider mappings not available, using standard matching")
    
    # ... existing processing code ...
    
    # When doing enrichment, pass the provider_matcher:
    if provider_matcher:
        enriched_count = process_enrichment_with_mappings(conn, provider_matcher)
    else:
        # Fall back to original logic
        enriched_count = process_enrichment_original(conn)
    
    # ... rest of the function ...
"""