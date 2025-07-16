#!/usr/bin/env python3
"""
Simplified integration for nightly_enriched_db.py
This shows the key changes to add provider mapping directly in the database
"""

# Add this to the enriched_circuits table if not already there:
"""
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_match_status VARCHAR(50);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_match_confidence INTEGER;
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_canonical VARCHAR(255);
"""

# In the nightly_enriched_db.py, modify the enrichment logic:

def enrich_circuit_with_mapping(circuit_data, meraki_data, conn):
    """
    Enrich circuit data and determine provider match status
    Store the match result directly in the database
    """
    cursor = conn.cursor()
    
    site_id = circuit_data['site_id']
    circuit_purpose = circuit_data['circuit_purpose']
    dsr_provider = circuit_data['provider_name']
    dsr_ip = circuit_data['ip_address_start']
    
    # Initialize match variables
    match_status = 'no_match'
    match_confidence = 0
    canonical_provider = dsr_provider
    matched_wan = None
    arin_provider = None
    
    # Check WAN1
    if dsr_ip == meraki_data.get('wan1_ip'):
        matched_wan = 'WAN1'
        arin_provider = meraki_data.get('wan1_arin_provider')
    elif dsr_ip == meraki_data.get('wan2_ip'):
        matched_wan = 'WAN2'
        arin_provider = meraki_data.get('wan2_arin_provider')
    
    # If no IP match, try provider matching
    if not matched_wan and dsr_provider:
        # Check against both WANs
        wan1_result = check_provider_match_db(dsr_provider, meraki_data.get('wan1_arin_provider'), circuit_purpose, cursor)
        wan2_result = check_provider_match_db(dsr_provider, meraki_data.get('wan2_arin_provider'), circuit_purpose, cursor)
        
        # Use the best match
        if wan1_result['confidence'] >= wan2_result['confidence'] and wan1_result['confidence'] >= 70:
            matched_wan = 'WAN1'
            arin_provider = meraki_data.get('wan1_arin_provider')
            match_status = wan1_result['status']
            match_confidence = wan1_result['confidence']
            canonical_provider = wan1_result['canonical']
        elif wan2_result['confidence'] >= 70:
            matched_wan = 'WAN2'
            arin_provider = meraki_data.get('wan2_arin_provider')
            match_status = wan2_result['status']
            match_confidence = wan2_result['confidence']
            canonical_provider = wan2_result['canonical']
    else:
        # We have IP match, check provider match
        if arin_provider:
            result = check_provider_match_db(dsr_provider, arin_provider, circuit_purpose, cursor)
            match_status = result['status']
            match_confidence = result['confidence']
            canonical_provider = result['canonical']
    
    # Update the enriched_circuits table with ALL the match information
    cursor.execute("""
        INSERT INTO enriched_circuits (
            site_id, 
            site_name,
            circuit_purpose,
            dsr_provider,
            arin_provider,
            wan_port,
            provider_match_status,
            provider_match_confidence,
            provider_canonical,
            dsr_ip,
            matched_ip,
            speed,
            cost,
            last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (site_id, circuit_purpose) DO UPDATE SET
            dsr_provider = EXCLUDED.dsr_provider,
            arin_provider = EXCLUDED.arin_provider,
            wan_port = EXCLUDED.wan_port,
            provider_match_status = EXCLUDED.provider_match_status,
            provider_match_confidence = EXCLUDED.provider_match_confidence,
            provider_canonical = EXCLUDED.provider_canonical,
            dsr_ip = EXCLUDED.dsr_ip,
            matched_ip = EXCLUDED.matched_ip,
            speed = EXCLUDED.speed,
            cost = EXCLUDED.cost,
            last_updated = EXCLUDED.last_updated
    """, (
        site_id,
        circuit_data['site_name'],
        circuit_purpose,
        dsr_provider,
        arin_provider,
        matched_wan,
        match_status,
        match_confidence,
        canonical_provider,
        dsr_ip,
        meraki_data.get(f'{matched_wan.lower()}_ip') if matched_wan else None,
        circuit_data.get('speed'),
        circuit_data.get('cost'),
    ))
    
    return {
        'matched': match_status == 'matched',
        'confidence': match_confidence,
        'wan_port': matched_wan
    }

def check_provider_match_db(dsr_provider, arin_provider, circuit_purpose, cursor):
    """
    Check provider match using database mappings
    Returns dict with status, confidence, and canonical provider
    """
    if not dsr_provider or not arin_provider:
        return {'status': 'no_data', 'confidence': 0, 'canonical': dsr_provider}
    
    # Direct match
    if dsr_provider.lower().strip() == arin_provider.lower().strip():
        return {'status': 'matched', 'confidence': 100, 'canonical': arin_provider}
    
    # Check mapping table
    cursor.execute("""
        SELECT arin_provider, confidence_score, mapping_type
        FROM provider_mappings
        WHERE LOWER(dsr_provider) = LOWER(%s)
        AND LOWER(arin_provider) = LOWER(%s)
        AND mapping_type != 'ignore'
        ORDER BY confidence_score DESC
        LIMIT 1
    """, (dsr_provider, arin_provider))
    
    mapping = cursor.fetchone()
    if mapping:
        return {
            'status': 'matched',
            'confidence': mapping[1],
            'canonical': mapping[0]  # Use ARIN provider as canonical
        }
    
    # Check for any mapping for this DSR provider
    cursor.execute("""
        SELECT arin_provider, confidence_score
        FROM provider_mappings
        WHERE LOWER(dsr_provider) = LOWER(%s)
        ORDER BY confidence_score DESC
        LIMIT 1
    """, (dsr_provider,))
    
    any_mapping = cursor.fetchone()
    if any_mapping:
        canonical = any_mapping[0]
    else:
        canonical = dsr_provider
    
    # Handle secondary circuit conflicts
    if circuit_purpose == 'Secondary':
        dsr_lower = dsr_provider.lower()
        if 'comcast' in dsr_lower and arin_provider == 'AT&T':
            return {'status': 'matched', 'confidence': 70, 'canonical': canonical}
        if 'cox' in dsr_lower and arin_provider in ['AT&T', 'Verizon']:
            return {'status': 'matched', 'confidence': 70, 'canonical': canonical}
        if 'spectrum' in dsr_lower and arin_provider == 'AT&T':
            return {'status': 'matched', 'confidence': 70, 'canonical': canonical}
    
    # No match
    return {'status': 'no_match', 'confidence': 0, 'canonical': canonical}

# Create a summary view for easy querying
"""
CREATE OR REPLACE VIEW circuit_enrichment_summary AS
SELECT 
    e.site_id,
    e.site_name,
    e.circuit_purpose,
    e.dsr_provider,
    e.arin_provider,
    e.provider_canonical,
    e.provider_match_status,
    e.provider_match_confidence,
    e.wan_port,
    CASE 
        WHEN e.provider_match_status = 'matched' THEN '✓'
        WHEN e.provider_match_status = 'no_match' THEN '✗'
        ELSE '?'
    END as match_icon,
    e.speed,
    e.cost,
    e.last_updated
FROM enriched_circuits e
ORDER BY e.site_name, e.circuit_purpose;
"""