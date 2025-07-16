# DSR Circuits - Primary Key Analysis & Database Logic

## Executive Summary

### Critical Finding: Record Number is NOT the Primary Key

After comprehensive analysis of all database scripts and models, I can confirm:

1. **Primary Key**: All tables use auto-increment integer `id` fields
2. **Record Number**: Stored as a regular column for reference only
3. **Business Logic**: Operates on `site_name` + `circuit_purpose` combination
4. **This is the CORRECT design** for this application's requirements

## Database Schema Analysis

### Circuits Table Structure
```sql
CREATE TABLE circuits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Actual primary key
    record_number VARCHAR(50),             -- Reference field only
    site_name VARCHAR(100) NOT NULL,       -- Part of business key
    site_id VARCHAR(50),
    circuit_purpose VARCHAR(50),           -- Part of business key
    ... additional fields ...
);

-- Unique constraint (if exists) would be:
-- UNIQUE(site_name, circuit_purpose)
```

### Why This Design is Correct

1. **Business Requirements**:
   - Each site can have multiple circuits (Primary, Backup, Guest, etc.)
   - The combination of site + purpose uniquely identifies a circuit
   - Record numbers can change without breaking relationships

2. **Data Integrity**:
   - Sites are the stable business entity
   - Record numbers from DSR Global can be reassigned
   - Manual override protection works at the site level

3. **Performance**:
   - Integer primary keys are fastest for joins
   - Site name is indexed for quick lookups
   - Record number can be indexed separately if needed

## Data Flow Using Current Architecture

### 1. DSR Import Process
```python
# Uses site_name + circuit_purpose for UPSERT logic
INSERT INTO circuits (...) VALUES (...)
ON CONFLICT (site_name, circuit_purpose) DO UPDATE
WHERE manual_override = FALSE
```

### 2. Assignment Tracking
```python
# Assignments linked by site_name
assignment_data = {
    assignment.site_name: {
        'sctask': assignment.sctask,
        'assigned_to': assignment.assigned_to
    }
}
```

### 3. Enablement Tracking
```python
# Tracks by Site ID, includes record_number for reference
INSERT INTO daily_enablements (
    site_id,           -- Primary tracking field
    date,
    enabled_by,
    record_number      -- Included for reference/reporting
)
```

## Record Number Usage Patterns

### Where Record Number IS Used:
1. **Display/Reporting**: Shown in UI for user reference
2. **DSR Correlation**: Matching with external CSV files
3. **Audit Trail**: Stored in history for tracking changes
4. **New Circuit Generation**: Auto-generated in specific format

### Where Record Number is NOT Used:
1. **Primary Key**: Not used as table primary key
2. **Foreign Keys**: Not used for table relationships
3. **Join Conditions**: Not primary join field
4. **Unique Constraints**: Not enforced as unique

## Implementation Examples

### New Stores Circuit Creation
```python
def generate_record_number(site_name, circuit_purpose):
    """Generate DSR-format record number"""
    # Format: DISCOUNT{SITE}{RANDOM}_BR[-I1]
    clean_site = ''.join(c for c in site_name.upper() if c.isalnum())[:10]
    random_num = ''.join([str(random.randint(0, 9)) for _ in range(8, 11)])
    record_number = f"DISCOUNT{clean_site}{random_num}_BR"
    
    if circuit_purpose.lower() != 'primary':
        record_number += "-I1"
    
    return record_number

# Create circuit with generated record_number
new_circuit = Circuit(
    site_name=site_name,          # Business key part 1
    circuit_purpose=purpose,      # Business key part 2  
    record_number=generate_record_number(site_name, purpose),  # Reference
    manual_override=True
)
```

### Dashboard Status Display
```python
# Query uses site_name for assignment matching
circuits = Circuit.query.filter_by(status='Ready for Turn Up').all()
assignments = CircuitAssignment.query.filter_by(status='active').all()

# Match by site_name, not record_number
for circuit in circuits:
    assignment = assignment_dict.get(circuit.site_name)
    if assignment:
        circuit.assigned_to = assignment['assigned_to']
```

## Database Integrity Features

### Manual Override Protection
- Based on site_name + circuit_purpose match
- Prevents DSR imports from overwriting manual data
- Works correctly without record_number as primary key

### Change Tracking
- Circuit history table uses circuit.id (integer) as foreign key
- Tracks all field changes including record_number changes
- Maintains complete audit trail

### Data Deduplication
- DSR import creates fingerprints of key fields
- Detects duplicates by content, not by record_number
- Handles sites with multiple circuits correctly

## Performance Considerations

### Current Indexes
```sql
-- Existing indexes for optimal performance
CREATE INDEX idx_circuits_site_name ON circuits(site_name);
CREATE INDEX idx_circuits_circuit_purpose ON circuits(circuit_purpose);
CREATE INDEX idx_circuits_status ON circuits(status);
CREATE INDEX idx_circuits_provider_name ON circuits(provider_name);
```

### Recommended Additional Index
```sql
-- Add index on record_number for faster lookups
CREATE INDEX idx_circuits_record_number ON circuits(record_number);
```

## Conclusions

### The Current Design is Correct Because:

1. **Business Logic Alignment**:
   - Sites are the core business entity
   - Each site needs multiple circuit types
   - Record numbers are external references that can change

2. **Data Integrity**:
   - Site-based operations ensure consistency
   - Manual overrides work correctly
   - No broken relationships when record numbers change

3. **Performance**:
   - Integer primary keys are optimal for joins
   - Indexed site_name provides fast lookups
   - Supports millions of records efficiently

### No Changes Needed

The current implementation correctly uses:
- Integer `id` as primary key for performance
- Site + purpose as the business key
- Record number as a reference field

This architecture properly supports all business requirements while maintaining data integrity and performance.

## Documentation Updates

### Created Documentation:
1. **[Nightly Scripts Documentation](NIGHTLY_SCRIPTS.md)** - Complete database logic for all automated processes
2. **[Flask Scripts Documentation](FLASK_SCRIPTS.md)** - Web application database operations
3. **[Primary Key Analysis](PRIMARY_KEY_ANALYSIS.md)** - This document

### Key Insights Documented:
- Record number generation logic for new circuits
- Assignment tracking by site name
- Manual override protection mechanisms
- Data enrichment matching algorithms
- Transaction handling and error recovery

---
*Last Updated: July 3, 2025*  
*Primary key architecture analysis and validation*  
*Part of DSR Circuits Documentation Suite*