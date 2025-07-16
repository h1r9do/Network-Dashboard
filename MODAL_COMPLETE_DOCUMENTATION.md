# Complete Modal Documentation - DSR Circuits

## Overview
The modal in DSR Circuits displays circuit confirmation data when clicking the "Confirm" button. This document explains the complete flow from backend to frontend.

## Backend Flow

### 1. Route Handler (`dsrcircuits.py`)
```python
@dsrcircuits_bp.route('/confirm/<site_name>', methods=['POST'])
def confirm_circuit(site_name):
    """Handle circuit confirmation popup data"""
    result = confirm_site(site_name)
    return jsonify(result)
```

### 2. Confirm Site Function (`confirm_meraki_notes_db.py`)
The `confirm_site()` function:
1. Queries multiple database tables:
   - `meraki_inventory` - For device info and ARIN data
   - `enriched_circuits` - For enriched provider/speed data
   - `circuits` - For DSR circuit data
2. Gets current device notes from Meraki API
3. Returns JSON with all modal data

### 3. Data Sources
```python
# Key data returned:
{
    'raw_notes': device_notes,           # From meraki_inventory.device_notes
    'wan1_arin_provider': arin_provider, # From meraki_inventory.wan1_arin_provider
    'wan2_arin_provider': arin_provider, # From meraki_inventory.wan2_arin_provider
    'csv_data': dsr_circuits,           # From circuits table
    'wan1': {...},                      # Enriched data
    'wan2': {...}                       # Enriched data
}
```

## Frontend Flow

### 1. Trigger (`dsrcircuits.html`)
```javascript
// Confirm button click
$('.confirm-btn').click(function() {
    var siteName = $(this).data('site');
    showConfirmModal(siteName);
});
```

### 2. AJAX Request
```javascript
function showConfirmModal(siteName) {
    $.ajax({
        url: '/confirm/' + encodeURIComponent(siteName),
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            // Populate modal
        }
    });
}
```

### 3. Modal Population
```javascript
// Populate Meraki Raw Notes
$('#modalRawNotes').css('white-space', 'pre-wrap').text(response.raw_notes || 'No Meraki notes available');

// Populate ARIN Info
$('#wan1ArinInfo').text('WAN1 IP: ' + response.wan1_ip + ' - Provider: ' + response.wan1_arin_provider);
$('#wan2ArinInfo').text('WAN2 IP: ' + response.wan2_ip + ' - Provider: ' + response.wan2_arin_provider);
```

## Common Issues and Fixes

### Issue 1: Literal \n in Notes
**Problem**: Notes show `WAN 1\nProvider\nSpeed` instead of line breaks

**Root Causes**:
1. Database has literal `\n` instead of actual newlines
2. Nightly script stores notes incorrectly
3. Manual updates use wrong format

**Fix**:
```python
# When storing notes in database
corrected_notes = "WAN 1\nProvider\nSpeed"  # Actual newlines
# NOT: "WAN 1\\nProvider\\nSpeed"  # Literal \n
```

### Issue 2: ARIN Data Mismatch
**Problem**: ARIN data in modal doesn't match live lookups

**Root Causes**:
1. Nightly script had lookup failures
2. ARIN API rate limiting
3. Cached "Unknown" values

**Fix**:
```python
# Run fix_all_notes_and_arin.py to refresh all ARIN data
python3 /usr/local/bin/Main/fix_all_notes_and_arin.py
```

## Database Schema

### meraki_inventory Table
```sql
CREATE TABLE meraki_inventory (
    network_name VARCHAR(255) PRIMARY KEY,
    device_notes TEXT,              -- Meraki device notes
    wan1_ip VARCHAR(45),           -- WAN1 IP address
    wan1_arin_provider VARCHAR(255), -- ARIN lookup result
    wan2_ip VARCHAR(45),           -- WAN2 IP address  
    wan2_arin_provider VARCHAR(255), -- ARIN lookup result
    last_updated TIMESTAMP
);
```

### enriched_circuits Table
```sql
CREATE TABLE enriched_circuits (
    site_name VARCHAR(255) PRIMARY KEY,
    device_notes TEXT,              -- Copy of device notes
    wan1_provider VARCHAR(255),     -- Final provider after enrichment
    wan1_speed VARCHAR(100),        -- Final speed
    wan2_provider VARCHAR(255),     -- Final provider after enrichment
    wan2_speed VARCHAR(100),        -- Final speed
    last_updated TIMESTAMP
);
```

## Nightly Script Issues

### Current Problem
The nightly script (`nightly_meraki_db.py`) stores notes with literal `\n`:

```python
# WRONG - Creates literal \n
device_notes = "WAN 1\\nProvider\\nSpeed"

# CORRECT - Creates actual newlines
device_notes = "WAN 1\nProvider\nSpeed"
```

### Fix Required
Update `nightly_meraki_db.py` to:
1. Store notes with actual newlines
2. Refresh ARIN lookups for failures
3. Handle rate limiting properly

## Testing the Modal

### 1. Check Database
```sql
-- Check notes format
SELECT network_name, device_notes, wan1_arin_provider 
FROM meraki_inventory 
WHERE network_name = 'AZP 08';
```

### 2. Test Modal Endpoint
```bash
# Test modal data
curl -X POST http://localhost:5052/confirm/AZP%2008 \
  -H "Content-Type: application/json" | python3 -m json.tool
```

### 3. Verify Frontend
1. Open browser to DSR Circuits page
2. Find AZP 08 and click "Confirm"
3. Check that notes show with proper line breaks
4. Verify ARIN data shows correct provider

## Quick Reference

### Fix All Issues
```bash
# 1. Run comprehensive fix
python3 /usr/local/bin/Main/fix_all_notes_and_arin.py

# 2. Clear browser cache
# Press Ctrl+F5 in browser

# 3. Test modal
# Click Confirm button on any site
```

### Check Specific Site
```python
# Quick check script
import psycopg2
conn = psycopg2.connect(host='localhost', database='dsrcircuits', user='dsruser', password='dsrpass123')
cursor = conn.cursor()
cursor.execute("SELECT device_notes FROM meraki_inventory WHERE network_name = 'AZP 08'")
notes = cursor.fetchone()[0]
print(f"Raw: {repr(notes)}")
print(f"Display:\n{notes}")
```