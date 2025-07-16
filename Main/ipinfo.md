# WAN IP Provider Identification System

## Current Implementation Overview

The DSR Circuits system identifies WAN IP providers through multiple methods, primarily relying on ARIN RDAP lookups for public IPs. This document outlines the current approach and proposed enhancements.

## Current Provider Identification Methods

### 1. ARIN RDAP API (Primary Method for Public IPs)
- **Endpoint:** `https://rdap.arin.net/registry/ip/{ip}`
- **Implementation:** `/usr/local/bin/Main/nightly/nightly_meraki_db.py`
- **Features:**
  - Real-time ISP lookups via RDAP API
  - Caching mechanism in `rdap_cache` table to reduce API calls
  - Special handling for IP ranges (e.g., 166.80.0.0/16 for Verizon Business)
  - Returns "Private IP" for RFC1918 addresses

### 2. Device Notes Parsing
- Extracts provider labels from Meraki device notes
- Parses "WAN1: Provider" and "WAN2: Provider" format
- Normalizes provider names using fuzzy matching (80% threshold)

### 3. DSR Circuit Data Matching
- Matches by IP address or provider name
- Uses fuzzy matching for provider name comparison
- Priority order: IP match → Provider name match → Notes vs ARIN comparison

### 4. Static IP Mappings
- Hardcoded `KNOWN_IPS` dictionary for specific IP-to-provider mappings
- Provider normalization and mapping rules

## Current Limitations

### Private IP Handling
- Returns generic "Private IP" for all RFC1918 addresses
- Doesn't utilize available context (device notes, DSR data)
- No fallback mechanism for provider identification

### Missing Data Points
- No DDNS hostname capture
- No DNS resolution capabilities
- Limited context for dynamic IP assignments

## Proposed Enhancement: Meraki DDNS Integration

### Overview
Utilize Meraki's Dynamic DNS (DDNS) service to create reliable site-to-IP-to-provider mappings.

### Benefits
1. **Consistent Site Identification**
   - Each device has unique DDNS hostname (e.g., `store-1234.dynamic.meraki.com`)
   - Site identification regardless of IP type (public/private)
   - Reliable tracking even with dynamic IP changes

2. **Enhanced Provider Resolution**
   - DDNS → Site → Provider mapping chain
   - Works for both public and private IPs
   - Reduces dependency on RDAP for private networks

### Implementation Architecture

```
┌─────────────────────┐
│   Meraki Device     │
│  (store-1234.mx)    │
├─────────────────────┤
│ DDNS: store-1234.   │
│ dynamic.meraki.com  │
│ WAN1: 10.1.1.1     │
│ WAN2: 68.1.2.3     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Enhanced Provider  │
│   Identification    │
├─────────────────────┤
│ 1. Resolve DDNS     │
│ 2. Extract Site ID  │
│ 3. Query DSR/Notes  │
│ 4. WHOIS/RDAP API  │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Provider Result   │
├─────────────────────┤
│ WAN1: AT&T (Notes)  │
│ WAN2: Comcast(RDAP) │
└─────────────────────┘
```

### Enhanced Provider Resolution Logic

```python
def identify_provider(ip_address, ddns_hostname, device_notes, site_name):
    # Step 1: Try DDNS-based identification
    if ddns_hostname:
        site_id = extract_site_from_ddns(ddns_hostname)
        provider = lookup_provider_by_site(site_id)
        if provider:
            return provider
    
    # Step 2: Check if private IP
    if is_private_ip(ip_address):
        # Try device notes
        if device_notes:
            provider = parse_provider_from_notes(device_notes)
            if provider:
                return provider
        
        # Try DSR circuit match by site
        if site_name:
            provider = lookup_dsr_by_site(site_name)
            if provider:
                return provider
        
        return "Unknown Provider (Private IP)"
    
    # Step 3: Public IP - use RDAP/WHOIS
    provider = rdap_lookup(ip_address)
    if provider:
        return normalize_provider(provider)
    
    # Step 4: Fallback to device notes
    if device_notes:
        return parse_provider_from_notes(device_notes)
    
    return "Unknown Provider"
```

## Database Schema Changes

### Add DDNS Fields to meraki_inventory
```sql
ALTER TABLE meraki_inventory 
ADD COLUMN ddns_hostname VARCHAR(255),
ADD COLUMN wan1_ddns_resolved_ip INET,
ADD COLUMN wan2_ddns_resolved_ip INET,
ADD COLUMN ddns_last_resolved TIMESTAMP;
```

### Enhanced rdap_cache Table
```sql
ALTER TABLE rdap_cache
ADD COLUMN lookup_method VARCHAR(50), -- 'rdap', 'ddns', 'notes', 'dsr'
ADD COLUMN confidence_score FLOAT;     -- 0.0 to 1.0
```

## API Enhancement Requirements

### Meraki API Calls Needed
1. **Get DDNS Hostname**
   - Endpoint: `/devices/{serial}` (may include DDNS info)
   - Alternative: Custom endpoint if available

2. **DNS Resolution**
   - Resolve DDNS hostname to current IP
   - Compare with reported WAN IPs
   - Track changes over time

## Benefits of WHOIS vs RDAP

### RDAP (Current - Preferred)
- **Structured JSON responses**
- **Standardized format (RFC 7483)**
- **Better for automation**
- **Includes CIDR blocks and ASN data**
- **Free and unlimited for ARIN region**

### WHOIS (Alternative)
- **Wider availability globally**
- **Legacy support**
- **Text-based parsing required**
- **May have rate limits**
- **Less structured data**

## Implementation Phases

### Phase 1: Database Schema Updates
- Add DDNS fields to database
- Create migration scripts
- Update models.py

### Phase 2: Meraki DDNS Collection
- Modify nightly_meraki_db.py to collect DDNS
- Add DNS resolution functionality
- Store DDNS-to-IP mappings

### Phase 3: Enhanced Provider Logic
- Implement multi-source provider resolution
- Add confidence scoring
- Update enrichment process

### Phase 4: UI Updates
- Display DDNS hostnames
- Show provider confidence levels
- Add provider source indicators

## Monitoring and Metrics

### Key Metrics to Track
- Provider identification success rate by method
- DDNS resolution success rate
- Private IP provider identification improvement
- API call volumes and performance

### Success Criteria
- >95% provider identification for public IPs
- >80% provider identification for private IPs (up from 0%)
- <2 second average identification time
- Reduced RDAP API calls through better caching

## Security Considerations

1. **DNS Spoofing Protection**
   - Validate DDNS responses
   - Cross-reference with Meraki API data
   - Log anomalies

2. **API Key Management**
   - Secure storage of Meraki API keys
   - Rate limiting compliance
   - Audit logging

3. **Data Privacy**
   - No sensitive data in DDNS hostnames
   - Proper access controls on provider data
   - Compliance with data retention policies

## Conclusion

The proposed Meraki DDNS integration would significantly improve provider identification, especially for private IP addresses. By combining DDNS with existing RDAP lookups, device notes parsing, and DSR circuit data, the system can achieve near-complete provider identification coverage while maintaining performance and reliability.