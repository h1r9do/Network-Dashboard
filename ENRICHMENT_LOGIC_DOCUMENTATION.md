# Original Enrichment Logic Documentation

## Critical Business Rules

### 1. ENABLED Circuits Only
- **MUST** filter tracking data for status = "Enabled"
- Never process disabled, cancelled, or pending circuits
- This prevents incorrect provider data from old/cancelled orders

### 2. Provider Selection Hierarchy

```
1. Parse Meraki device notes (WAN1: Provider Speed)
2. Perform ARIN lookup on IP addresses
3. Compare ARIN provider with notes provider
4. Decision logic:
   - If provider_comparison == "No match": Use provider from notes
   - If provider_comparison == "Match": Use ARIN provider
   - If no notes: Use ARIN provider
   - If no ARIN: Use notes provider
```

### 3. Data Flow

```
Tracking CSV (DSR Global)
    ↓
Filter: Status = "Enabled" AND Cost > $0
    ↓
Meraki Inventory (from API)
    ↓
Parse Device Notes → Extract WAN1/WAN2 providers
    ↓
ARIN IP Lookups → Get ISP providers
    ↓
Compare Notes vs ARIN → "Match" or "No match"
    ↓
Apply Selection Logic → Choose best provider
    ↓
Normalize Provider Names → Canonical form
    ↓
Store in enriched_circuits table
```

### 4. Provider Normalization Rules

#### Cell Providers
- VZW, VZ, VZG, Digi → "VZW Cell"
- Inseego → "Inseego"  
- Speed always displayed as "Cell"

#### Satellite Providers
- Starlink → "Starlink"
- Speed always displayed as "Satellite"

#### DSR Prefix Handling
- Remove prefixes: "DSR", "NOT DSR", "AGG", etc.
- Remove suffixes: "fiber", "dsl", "extended cable"

#### Provider Mapping
- spectrum → Charter Communications
- clink → CenturyLink
- verizon → Verizon Business
- [Full mapping table with 132 entries]

### 5. Special Cases

#### IP Ranges
- 166.80.0.0/16 → Always "Verizon Business" (DT range)
- Private IPs → Skip ARIN lookup, use notes

#### Provider Comparison
- Fuzzy matching with 80% threshold
- Keyword-based canonical mapping
- Case-insensitive comparison

#### Missing Data
- No tracking match → Use Meraki data
- No IP match → Try fuzzy provider match
- No notes → Rely on ARIN data

### 6. Implementation Requirements

1. **Parse Notes Function**
   - Extract WAN1/WAN2 sections
   - Handle various formats
   - Return provider_label and speed

2. **Provider Comparison**
   - Compare ARIN vs notes providers
   - Use fuzzy matching
   - Return "Match"/"No match"

3. **Enrichment Logic**
   - Filter enabled circuits
   - Apply selection hierarchy
   - Normalize providers
   - Store comparison results

## Example: CAL 17

Given:
- Status: "Order Canceled" (in DSR)
- Notes: "WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M"
- ARIN: "Frontier Communications"
- Old DSR: "Charter Communications"

Result:
- Skip DSR data (not enabled)
- Parse notes → "Frontier Fiber"
- ARIN lookup → "Frontier Communications"
- Comparison → "Match"
- Final provider → "Frontier Communications"

## Missing in Current Implementation

1. ❌ Not filtering for enabled circuits
2. ❌ Not parsing device notes
3. ❌ Not comparing ARIN vs notes
4. ❌ Not applying selection hierarchy
5. ❌ Using cancelled circuit data

## Required Fixes

1. Add notes parsing to nightly_meraki_db.py
2. Store parsed provider_label in meraki_inventory
3. Add provider comparison logic
4. Update enrichment to filter enabled only
5. Implement proper selection hierarchy