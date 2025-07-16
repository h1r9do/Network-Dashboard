# Non-DSR Circuit Creation Process

## Overview
Based on analysis of the DSR Circuits page and database structure, here's how to create Non-DSR circuit records for the Frontier sites that are failing to match.

## Key Findings

### 1. Record Number Pattern
- **DSR Circuits**: Have record_number like `DISCOUNTAZP3635747389_BR`
- **Non-DSR Circuits**: Have **NULL** record_number (this is the key identifier)
- This distinction is crucial for the system to recognize non-DSR circuits

### 2. Data Source Field Values
- **DSR Circuits**: `data_source = 'csv_import'` or similar
- **Non-DSR Circuits**: `data_source = 'Non-DSR'` or `'new_stores_manual'`

### 3. Unique Identifier Generation
- When creating through the UI, the system uses `MAX(id) + 1` for the next ID
- No special unique identifier is generated - the NULL record_number is the identifier
- The edit modal in dsrcircuits.html has a "Create Non-DSR Circuit" form that:
  - Uses `/api/create-non-dsr-circuit` endpoint
  - Automatically sets `data_source = 'Non-DSR'`
  - Sets `record_number = NULL`

## Process for Creating Non-DSR Circuits from Excel

### Target Sites (Frontier failures)
Sites that have matching ARIN and device notes but fail DSR matching:
- CAL 13: EB2-Frontier Fiber (1000M X 1000M)
- CAL 17: Frontier Dedicated (500M X 500M)
- CAL 20: Frontier Fios (500M X 500M)
- CAL 24: Frontier Fios (500M X 500M) - Already has non-DSR record
- CAN 16: Frontier Dedicated (500M X 500M)
- CAS 35: Frontier (500M X 50M)
- CAS 40: Frontier (500M X 50M)
- CAS 41: Frontier (500M X 50M)
- CAS 48: EB2-Frontier Fiber (500M X 500M)

### Required Fields for Non-DSR Circuits
```python
{
    'id': next_available_id,  # Using MAX(id) + 1
    'site_name': 'CAL 13',    # From Excel "Store" column
    'site_id': None,          # Typically NULL for Non-DSR
    'circuit_purpose': 'Primary',  # or 'Secondary'
    'status': 'Enabled',
    'provider_name': 'EB2-Frontier Fiber',  # From Excel
    'details_ordered_service_speed': '1000M X 1000M',  # From Excel
    'billing_monthly_cost': 105.01,  # From Excel (as float)
    'data_source': 'Non-DSR',  # Critical identifier
    'record_number': None,      # Must be NULL for Non-DSR
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}
```

### Implementation Steps

1. **Check Existing Circuits First**
   - Query for existing circuits at each site
   - Skip if equivalent circuit already exists
   - CAL 24 already has non-DSR circuits

2. **Create Primary Circuits**
   - For each site's WAN1 data from Excel
   - Map provider names exactly as shown in Excel
   - Include speed and cost information

3. **Skip Secondary Circuits if "Cell"**
   - Most sites show WAN2 as "Cell" in Excel
   - These are typically not created as circuits

4. **Use Exact Provider Names**
   - Don't normalize names - use exactly what's in Excel:
     - "EB2-Frontier Fiber"
     - "Frontier Dedicated"
     - "Frontier Fios"
     - "Frontier"

## Script Execution Plan

The `create_non_dsr_frontier_circuits.py` script will:

1. Read the Excel file with proper permissions
2. Target only the 9 failing Frontier sites
3. Check existing circuits to avoid duplicates
4. Create Non-DSR circuits with proper structure
5. Show what will be created before committing
6. Ask for confirmation before database changes

## Expected Outcome

After creating these Non-DSR circuits:
1. The enrichment process will find matching circuits for these sites
2. The provider-only matching logic will work correctly
3. These sites will show as matched instead of failing

## Alternative Approach

Instead of creating Non-DSR circuits, we could also:
1. Implement the provider-only matching logic that recognizes when ARIN = Device Notes as a valid match
2. This would solve the issue without needing to create manual records
3. The logic: If WAN notes provider == WAN ARIN provider → Consider it matched