# New Stores TOD (Target Opening Date) Management System

## Overview

The New Stores TOD Management System is a comprehensive module within the DSR Circuits application designed to track and manage circuit provisioning for new Discount Tire store constructions. This system integrates Target Opening Date (TOD) tracking with circuit management, providing visibility into upcoming store openings and their network readiness.

## System Components

### 1. Web Interface (`/new-stores`)
- **URL**: http://10.46.0.3:5052/new-stores
- **Template**: `/usr/local/bin/templates/new_stores_tabbed.html`
- **Blueprint**: `/usr/local/bin/Main/new_stores.py`

### 2. Database Tables
- **new_stores**: Tracks store construction projects with TOD information
- **circuits**: Main circuit data with manual override protection for new store circuits

### 3. Key Features
- Target Opening Date (TOD) tracking and management
- Excel file upload for bulk TOD report processing
- Manual store entry with dynamic forms
- Circuit management with provider/speed configuration
- Automatic detection when stores go live in Meraki
- Free-form notes field for each circuit

## User Interface Components

### Navigation Buttons
1. **🏠 Home** - Return to main navigation
2. **➕ Add Circuit** - Create new circuits for stores
3. **📋 TOD Store List** - Manage store construction pipeline
4. **📤 Upload TOD Report** - Import Excel files with TOD data
5. **✏️ Enter New TOD Store** - Manual store entry form

### Export Options
- **Export to Excel** - Download current view as Excel file
- **Export as PDF** - Generate PDF report

## TOD Store List Management

### Store Status Codes
- **01 - Planning** - Initial planning phase
- **02 - Acquired** - Site acquired, pre-construction
- **03 - Construction** - Active construction
- **04 - Complete** - Construction complete, awaiting opening
- **05 - Live** - Store operational

### Data Fields
- **Site Name** - Store identifier (e.g., "PHX 101")
- **Target Opening Date** - Expected opening date or "TBD"
- **Region** - Geographic region
- **City/State** - Location details
- **Status** - Current project status (01-05)

## Excel Upload Functionality

### Upload TOD Report Process
1. Click **📤 Upload TOD Report** button
2. Select Excel file in "RE - Targeted Opening Dates" format
3. System processes file and:
   - **New stores**: Added to the system
   - **Existing stores**: Updated with new information
   - **Duplicates**: Prevented through site name matching

### Excel File Format Requirements
Required columns (flexible naming):
- Store/Site Name (required)
- Target Opening Date (optional)
- Region (optional)
- City (optional)
- State (optional)
- Project Status (optional)

### Update Logic (July 2025 Enhancement)
- Existing stores are **updated** rather than skipped
- Only non-empty Excel values update existing records
- Preserves existing data when Excel field is empty
- Upload results show:
  - "New stores added: X"
  - "Existing stores updated: Y"
  - Clear indication with "(updated)" suffix

## Manual Store Entry

### Enter New TOD Store Form
Dynamic form with fields:
- **Site Name** (required) - Uppercase conversion
- **Target Opening Date** - Date picker or "TBD"
- **Region** - Geographic region
- **City** - City name
- **State** - State abbreviation
- **Project Status** - Dropdown selection

### Add Multiple Stores
- Click **Add Row** to create additional entry fields
- Submit all stores in a single operation
- Validation ensures no duplicate site names

## Circuit Management

### Add Circuit Modal
- **Site Name** - Select from existing stores
- **Circuit Purpose** - Primary or Secondary only
- **Provider** - Free-form text input
  - Special handling: "Starlink" auto-fills speed as "Satellite"
- **Speed** - Service speed or auto-filled
- **Monthly Cost** - Billing amount

### Circuit Notes Feature
- **Location**: Notes column in circuit table
- **Functionality**: 
  - Type directly in the notes field
  - Auto-saves on blur (when clicking away)
  - No save button required
  - Persists until circuit is enabled/cancelled
  - Automatically cleared during nightly DSR pull

### Manual Override Protection
Circuits created through new stores interface are protected:
- **manual_override** = TRUE
- **manual_override_date** = Creation timestamp
- **manual_override_by** = "new_stores_ui"
- Prevents automatic DSR updates from overwriting
- Can be removed through Edit Status modal

## API Endpoints

### Core Endpoints
- `GET /api/new-stores` - Retrieve all active stores
- `POST /api/new-stores/manual` - Add stores manually
- `POST /api/new-stores/excel-upload` - Upload Excel file
- `PUT /api/new-stores/<id>` - Update store details
- `DELETE /api/new-stores/<id>` - Remove store

### Circuit Integration
- `GET /api/new-store-circuits-with-tod` - Get circuits with TOD data
- `POST /api/circuits/update-notes` - Update circuit notes

### Excel Upload Response Format
```json
{
  "success": true,
  "added": ["STORE1", "STORE2 (updated)"],
  "new": ["STORE1"],
  "updated": ["STORE2 (updated)"],
  "errors": [],
  "total_added": 1,
  "total_updated": 1,
  "total_errors": 0
}
```

## Filtering and Search

### Available Filters
- **Status** - Filter by project status (01-05)
- **Region** - Regional filtering
- **Provider** - Circuit provider
- **Site** - Search by site name

### DataTables Integration
- Real-time search across all columns
- Sortable columns (click headers)
- Pagination for large datasets
- Entries per page selection

## Integration with Main System

### Nightly Processing
1. **DSR Pull** (00:00) - Updates circuit data with override protection
2. **Meraki Collection** (01:00) - Detects when stores go live
3. **Store Detection** - Automatic status update when found in Meraki

### Go-Live Detection
When a store is detected in Meraki inventory:
- `meraki_network_found` = TRUE
- `meraki_found_date` = Detection timestamp
- Store can be manually removed from active list

## Data Persistence

### Database Schema
```sql
-- new_stores table
CREATE TABLE new_stores (
    id SERIAL PRIMARY KEY,
    site_name VARCHAR(100) UNIQUE NOT NULL,
    target_opening_date DATE,
    target_opening_date_text VARCHAR(50),
    region VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(20),
    project_status VARCHAR(20),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    meraki_network_found BOOLEAN DEFAULT FALSE,
    meraki_found_date TIMESTAMP,
    added_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- circuits table additions
ALTER TABLE circuits ADD COLUMN notes TEXT;
ALTER TABLE circuits ADD COLUMN manual_override BOOLEAN DEFAULT FALSE;
ALTER TABLE circuits ADD COLUMN manual_override_date TIMESTAMP;
ALTER TABLE circuits ADD COLUMN manual_override_by VARCHAR(100);
```

## Best Practices

### Data Entry
1. Use consistent site naming (e.g., "PHX 101" not "Phoenix 101")
2. Enter TOD dates in MM/DD/YYYY format or use "TBD"
3. Keep status codes current through regular updates

### Excel Upload
1. Verify Excel format matches expected columns
2. Review upload results for any errors
3. Use updates feature to refresh TOD dates regularly

### Circuit Management
1. Always specify Primary/Secondary for circuit purpose
2. Use standard provider names for consistency
3. Add notes for special requirements or issues

## Troubleshooting

### Common Issues

#### Excel Upload Fails
- **Issue**: "Could not find store name column"
- **Solution**: Ensure Excel has column with "store", "site", or "name" in header

#### Duplicate Store Error
- **Issue**: Store already exists when using manual entry
- **Solution**: Use Excel upload which updates existing stores

#### Circuit Not Appearing
- **Issue**: Added circuit doesn't show in table
- **Solution**: Check filters - reset "All" filters if needed

#### Notes Not Saving
- **Issue**: Notes disappear after typing
- **Solution**: Click outside the field to trigger auto-save

### Debug Information
- Check browser console for JavaScript errors
- Review Flask logs: `journalctl -u dsrcircuits.service -f`
- Verify database: `psql -U dsradmin -d dsrcircuits`

## Security Considerations

### Manual Override Protection
- Prevents accidental data loss from automated updates
- Only new_stores interface and manual DB updates can modify
- Audit trail maintained with date and source

### Access Control
- Currently integrated with main DSR Circuits authentication
- No separate permissions for new stores module
- All users with circuit access can manage new stores

## Future Enhancements

### Planned Features
1. Email notifications for approaching TOD dates
2. Integration with construction management systems
3. Automated circuit ordering based on TOD
4. Historical TOD accuracy reporting

### API Expansion
1. Webhook notifications for store status changes
2. Bulk circuit creation API
3. TOD calendar integration
4. Construction milestone tracking

---

**Module Version**: 2.0 (July 2025 - TOD terminology update)  
**Last Updated**: July 2, 2025  
**Primary Developer**: Database-integrated version with manual override protection