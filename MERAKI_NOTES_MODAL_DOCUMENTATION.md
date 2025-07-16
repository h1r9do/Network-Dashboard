# Meraki MX Notes Modal Documentation

## Overview
This document explains how the Meraki MX Notes modal works in the DSR Circuits system, including common issues and their solutions.

## How Notes are Stored and Displayed

### 1. Database Storage
- **Table**: `meraki_inventory`
- **Column**: `device_notes`
- **Format**: Plain text with actual newline characters (`\n`)

### 2. Data Flow
1. **Nightly Script** (`nightly_meraki_db.py`):
   - Collects device notes from Meraki API
   - Stores in database with proper newlines
   
2. **Enrichment Script** (`nightly_enriched_db.py`):
   - Updates device notes based on circuit data
   - Should maintain proper newline formatting

3. **Web Display** (`dsrcircuits.py` + `dsrcircuits.html`):
   - Flask endpoint serves notes to frontend
   - Modal displays notes in HTML

## Common Issues and Solutions

### Issue 1: Literal \n in Modal Display
**Problem**: Notes show as one line with visible `\n` characters:
```
WAN 1\nCox Communications\n300.0M x 30.0M\nWAN 2\nVZW Cell\nCell
```

**Expected**: Notes should show with proper line breaks:
```
WAN 1
Cox Communications
300.0M x 30.0M
WAN 2
VZW Cell
Cell
```

### Root Causes:
1. **JSON Encoding**: When Python sends data to JavaScript, newlines may be escaped
2. **HTML Rendering**: Browser needs `<br>` tags or CSS `white-space: pre-wrap`
3. **Database Storage**: Notes may have literal `\n` instead of actual newlines

### Solutions:

#### Frontend Fix (JavaScript/HTML):
```javascript
// In dsrcircuits.html modal rendering
// Replace \n with <br> for HTML display
var formattedNotes = deviceNotes.replace(/\\n/g, '<br>');
$('#modalNotesContent').html(formattedNotes);

// OR use pre-wrap CSS
$('#modalNotesContent').css('white-space', 'pre-wrap').text(deviceNotes);
```

#### Backend Fix (Python):
```python
# In dsrcircuits.py when serving notes
# Ensure notes have actual newlines, not literal \n
if device_notes and '\\n' in device_notes:
    device_notes = device_notes.replace('\\n', '\n')
```

#### Database Fix:
```sql
-- Check for literal \n in database
SELECT network_name, device_notes 
FROM meraki_inventory 
WHERE device_notes LIKE '%\\n%';

-- Fix literal \n in database
UPDATE meraki_inventory 
SET device_notes = REPLACE(device_notes, '\\n', E'\n')
WHERE device_notes LIKE '%\\n%';
```

## ARIN Provider Issues

### Issue 2: ARIN Shows "Unknown" for Valid IPs
**Problem**: IP 68.15.185.94 shows as "Unknown" but should be Cox

### Root Causes:
1. **ARIN API Failure**: Timeout or connection error during lookup
2. **Rate Limiting**: Too many requests to ARIN RDAP API
3. **Cached Bad Data**: Previous failed lookup stored as "Unknown"

### Solutions:
```python
# Force fresh ARIN lookup
def get_arin_provider(ip_address):
    """Get ARIN provider with retry logic"""
    if not ip_address:
        return "Unknown"
    
    # Skip private IPs
    if ip_address.startswith(('10.', '172.', '192.168.')):
        return "Private IP"
    
    try:
        url = f'https://rdap.arin.net/registry/ip/{ip_address}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Extract provider name from RDAP response
            # Check multiple fields for provider info
            provider = extract_provider_from_rdap(data)
            return provider if provider else "Unknown"
    except Exception as e:
        print(f"ARIN lookup failed for {ip_address}: {e}")
        return "Unknown"
```

## Quick Reference Commands

### Check Current Notes Format:
```bash
# Check specific site
psql -U dsruser -d dsrcircuits -c "SELECT network_name, device_notes FROM meraki_inventory WHERE network_name = 'AZP 08';"

# Check for literal \n issues
psql -U dsruser -d dsrcircuits -c "SELECT COUNT(*) FROM meraki_inventory WHERE device_notes LIKE '%\\\\n%';"
```

### Fix Notes in Database:
```sql
-- PostgreSQL command to fix all literal \n
UPDATE meraki_inventory 
SET device_notes = REPLACE(device_notes, '\\n', E'\n')
WHERE device_notes LIKE '%\\n%';
```

### Force ARIN Update for Specific IP:
```python
# Script to update ARIN for specific sites
UPDATE meraki_inventory 
SET wan1_arin_provider = 'Cox Communications Inc.'
WHERE network_name = 'AZP 08' AND wan1_ip = '68.15.185.94';
```

## Files to Check When Debugging:
1. `/usr/local/bin/Main/dsrcircuits.py` - Flask endpoint serving notes
2. `/usr/local/bin/templates/dsrcircuits.html` - Modal HTML/JavaScript
3. `/usr/local/bin/Main/nightly_meraki_db.py` - Nightly collection script
4. `/usr/local/bin/Main/nightly_enriched_db.py` - Enrichment script

## Testing Notes Display:
```python
# Quick test script
import psycopg2
conn = psycopg2.connect(host='localhost', database='dsrcircuits', user='dsruser', password='dsrpass123')
cursor = conn.cursor()
cursor.execute("SELECT device_notes FROM meraki_inventory WHERE network_name = 'AZP 08'")
notes = cursor.fetchone()[0]
print(f"Raw: {repr(notes)}")
print(f"Display:\n{notes}")
```

## Important: Proper Notes Format
Correct format should be:
```
WAN 1
Provider Name
Speed
WAN 2  
Provider Name
Speed
```

With actual newline characters, not literal \n strings.