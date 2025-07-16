# Provider Matching Integration Guide

## Simple Database-Driven Approach

Instead of complex client-side matching, we store all match results in the database during the nightly enrichment process. The web interface simply displays these pre-calculated results.

## Implementation Steps

### 1. Update Database Schema

```bash
# Add columns to store match results
psql -d your_db -f update_enriched_table.sql
```

This adds:
- `provider_match_status` - matched/no_match/no_data
- `provider_match_confidence` - 0-100 score
- `provider_canonical` - standardized provider name

### 2. Modify Nightly Enrichment Script

The nightly script now:
1. Loads provider mappings from `provider_mappings` table
2. Calculates match status for each circuit
3. Stores the results in `enriched_circuits` table

Key changes to `nightly_enriched_db.py`:
```python
# Check provider match using database
result = check_provider_match_db(dsr_provider, arin_provider, circuit_purpose, cursor)

# Store match results
INSERT INTO enriched_circuits (
    ...,
    provider_match_status,      # 'matched', 'no_match', 'no_data'
    provider_match_confidence,  # 0-100
    provider_canonical,         # Standardized name
    ...
)
```

### 3. Web Interface - Just Display Results

The modal simply queries and displays pre-calculated matches:

```javascript
// Fetch pre-matched data
fetch(`/api/circuit-matches/${site}`)
    .then(response => response.json())
    .then(data => {
        // Display with color coding based on confidence
        // ✓ = matched (green if 90%+, yellow if 70%+)
        // ✗ = no match (red)
        // ? = no data (gray)
    });
```

### 4. Flask Endpoint

Add to `dsrcircuits.py`:
```python
@app.route('/api/circuit-matches/<site_name>')
def get_circuit_matches(site_name):
    """Get pre-calculated circuit match data"""
    
    circuits = query_db("""
        SELECT * FROM enriched_circuits 
        WHERE site_name = %s
    """, (site_name,))
    
    return jsonify({
        'circuits': circuits,
        'matched_count': sum(1 for c in circuits if c['match_status'] == 'matched'),
        'avg_confidence': avg([c['match_confidence'] for c in circuits])
    })
```

## Benefits of This Approach

1. **Simplicity** - No complex JavaScript matching logic
2. **Performance** - Pre-calculated results, instant display
3. **Consistency** - All matching logic in one place (nightly script)
4. **Auditability** - Match results stored in database
5. **Debugging** - Easy to query and verify matches

## Database Views for Reporting

```sql
-- Check overall match rate
SELECT * FROM provider_match_statistics;

-- See all matches for a site
SELECT * FROM circuit_match_display WHERE site_name = 'ABC 01';

-- Find all no-match cases
SELECT * FROM enriched_circuits 
WHERE provider_match_status = 'no_match'
ORDER BY site_name;
```

## Testing

1. Run the enrichment with new logic:
```bash
python3 nightly_enriched_db.py --test-mode
```

2. Check results:
```sql
SELECT site_name, dsr_provider, arin_provider, 
       provider_match_status, provider_match_confidence
FROM enriched_circuits
ORDER BY provider_match_confidence DESC
LIMIT 20;
```

3. Verify in web interface - circuits should show:
   - Green checkmark for good matches (90%+)
   - Yellow checkmark for fair matches (70-89%)
   - Red X for no matches
   - Gray ? for missing data

## Summary

This approach moves all the intelligence to the nightly script, making the web interface a simple display layer. The provider mappings are applied during enrichment, and results are stored for instant retrieval.

---
**Last Updated**: July 11, 2025