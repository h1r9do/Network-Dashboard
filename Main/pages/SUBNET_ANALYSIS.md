# DSR Circuits - Subnet Analysis Documentation

## Overview
**URL**: `/subnets`  
**File**: `/usr/local/bin/Main/subnets_blueprint.py`  
**Blueprint**: `subnets_bp`  
**Purpose**: Network subnet visualization, VLAN analysis, and IP space management across all store locations using data VLANs (1 and 100) from 10.x networks only

## 🔄 Data Updates
**Automatic Updates**: Data refreshes nightly at 1:00 AM via `nightly_meraki_db.py`
**Data Source**: Meraki API collection of VLAN configurations
**Collection Method**: Uses only data VLANs (VLAN 1 and 100) to determine site /24 networks
**Network Filter**: Shows only 10.x networks (excludes 172.x guest networks, 192.168.x, etc.)

## Page Layout & Components

### Header Section
- **Title**: "Network Subnet Analysis"
- **Row Count**: Dynamic display showing "Showing X of Y networks"
- **Statistics Grid**: Four key metrics displayed prominently:
  - **Total Networks**: Count of unique network locations (10.x only, data VLANs)
  - **Total VLANs**: Total VLAN configurations across all sites (10.x only)
  - **Unique /24 Networks**: Count of distinct /24 subnets in use
  - **Shared /16 Networks**: Number of /16 networks used by multiple sites

### Control Panel

#### Navigation Buttons
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **📖 Help & Documentation**: Opens this documentation page
- **🔄 Refresh Button**: Reloads data with visual confirmation

#### Export Options
- **📊 Export to Excel**: Downloads current view as .xlsx file with tabular format
  - Each site gets its own column (Site_01, Site_02, etc.)
  - Format: "Network_16, Site_Count, Unique_24_Networks, TXG 02 10.13.105.0/24, TXH 04 10.13.4.0/24..."
- **📄 Export to CSV**: Downloads current view as .csv file  
  - All sites in one column, comma-separated
  - Format: "TXG 02 10.13.105.0/24, TXH 04 10.13.4.0/24..."

### View Mode

#### Group by /16 Networks
- **Purpose**: Identify which sites share the same /16 network space
- **Columns**:
  - **Network /16**: The parent /16 network (e.g., 10.1.0.0/16)
  - **Sites**: Number of sites using this /16
  - **Unique /24s**: Count of different /24 subnets within this /16
  - **Site Names**: Grid of clickable site buttons showing "Site Name /24Network"

### Filter Controls

#### Search Networks/Sites
- **Type**: Free-text search box
- **Searches**: Network CIDR patterns or site names
- **Example**: "10.1" finds all 10.1.x.x networks, "COD" finds all COD sites

#### Minimum Sites Filter
- **Type**: Numeric input (default: 1)
- **Purpose**: Show only networks used by at least N sites
- **Use Case**: Set to 5+ to find widely-used subnets

#### Apply Filters Button
- **Color**: Green (#27ae60)
- **Action**: Applies all filter criteria to current view

## Interactive Features

### Site Buttons Display
**New Format**: Each site button displays "Site Name /24Network"
- **Example**: "TXG 02 10.13.105.0/24" instead of just "TXG 02"
- **Width**: Optimized 180px minimum width to prevent text wrapping
- **Layout**: Responsive grid that adjusts to screen size
- **Functionality**: Click any button to view detailed VLAN information

### Site Details Modal
**Trigger**: Click any site button

#### Modal Contents:
- **Header**: "Network Details: [Site Name]" (shows just site name, not /24)
- **Statistics**: Total VLANs and Unique /24 count for that site
- **VLAN Table**: Shows **ALL VLANs** at the site (not just data VLANs):
  - **VLAN ID**: Numeric VLAN identifier
  - **Name**: VLAN description/purpose
  - **Subnet**: Full subnet with mask (e.g., 10.1.5.0/26)
  - **Parent /24**: The containing /24 network
  - **DHCP Mode**: Configuration (Server/Relay/Disabled)
  - **Gateway IP**: Appliance IP address

### DataTables Integration
- **No Pagination**: All data shows on single page for easy viewing
- **Sorting**: Click column headers to sort
- **Search**: Table-level search functionality
- **Responsive**: Adapts to different screen sizes

## Data Collection Methodology

### VLAN Selection Criteria
1. **Data VLANs Only**: Uses VLAN 1 or 100 (primary data networks)
2. **10.x Networks Only**: Excludes 172.x (guest), 192.168.x, 198.18.x
3. **Site Identification**: Uses `network_name` field from Meraki
4. **/24 Calculation**: Automatically derives parent /24 from data VLAN subnet

### Automatic Filters Applied
1. **172.x Networks**: Guest networks excluded from all views
2. **Hub/Voice/Lab**: Special-purpose networks filtered out
3. **Non-10.x Networks**: Only 10.x IP space shown
4. **Null Subnets**: VLANs without subnet assignments ignored

### Database Views Used
- `sites_by_16_network`: Pre-aggregated /16 groupings with site-network mappings

## Common Use Cases

### 1. IP Space Planning
**Scenario**: Need to find available IP space for new site
- Switch to "/16 Networks" view
- Sort by "Sites" ascending to find less-used /16s
- Look for /16s with low site counts
- Click site buttons to verify actual VLAN usage patterns

### 2. Network Standardization Review
**Scenario**: Ensure sites follow standard VLAN patterns
- Use the /16 Networks view to identify commonly used network ranges
- Look for /16 networks with high site counts (these are your standards)
- Sites using unique /16 ranges may need configuration review
- Click site buttons to see all VLANs and identify deviations

### 3. Subnet Conflict Prevention
**Scenario**: Check if a /24 subnet is already in use before assigning
- Use search box to enter target subnet (e.g., "10.1.50")
- View results in the /16 Networks view
- Click site buttons to see exact configurations and conflicts

### 4. Regional Network Analysis
**Scenario**: Analyze network usage patterns by region/state
- Search for regional prefix (e.g., "TXD" for Texas Dallas)
- Export results for offline analysis and documentation
- Compare subnet usage patterns across regions

### 5. Growth Planning
**Scenario**: Determine which /16 networks have capacity for new sites
- Filter by minimum sites (e.g., 10+) to see established networks
- Look at "Unique /24s" to see how much of each /16 is used
- Calculate remaining /24 space (256 total /24s per /16)

## API Endpoints

### GET /subnets/api/by-16
**Parameters**: 
- `network`: Filter string for searching
- `min_sites`: Minimum site count threshold

**Response**:
```json
{
  "data": [{
    "network_16": "10.1.0.0/16",
    "site_count": 45,
    "sites": "COD 01 10.1.1.0/24, COD 02 10.1.2.0/24, ...",
    "unique_24_networks": 12,
    "all_24_networks": "10.1.1.0/24, 10.1.2.0/24, ..."
  }],
  "total": 30
}
```


### GET /subnets/api/site-details/[site_name]
**Response**: Returns ALL VLANs for the site, not just data VLANs
```json
{
  "site_name": "COD 01",
  "vlans": [{
    "vlan_id": 1,
    "name": "Corporate",
    "subnet": "10.1.5.0/26",
    "parent_24": "10.1.5.0/24",
    "dhcp_handling": "Run a DHCP server",
    "appliance_ip": "10.1.5.1"
  }, {
    "vlan_id": 100,
    "name": "Guest",
    "subnet": "172.16.1.0/24",
    "parent_24": "172.16.1.0/24",
    "dhcp_handling": "Run a DHCP server",
    "appliance_ip": "172.16.1.1"
  }],
  "unique_24_count": 5
}
```

### GET /subnets/api/export/excel
**Parameters**: 
- `view`: Always 'by16' (only view mode supported)
- `network`: Filter string for searching
- `min_sites`: Minimum site count threshold
**Response**: Excel file with tabular format (each site in separate column)

### GET /subnets/api/export/csv  
**Parameters**: Same as above
**Response**: CSV file with sites comma-separated in single column

## Performance Considerations

### Optimization Features
- Database views pre-aggregate complex queries using data VLANs only
- Client-side DataTables for sorting/searching without pagination
- Indexes on network_name, vlan_id, and subnet columns
- Parent /24 networks calculated automatically via database functions

### Expected Performance
- Initial page load: < 2 seconds
- View switching: < 1 second  
- Site details modal: < 500ms
- Export operations: 2-5 seconds depending on data size

## Troubleshooting

### No Data Displayed
1. **Check VLAN Collection**: `SELECT COUNT(*) FROM network_vlans WHERE vlan_id IN (1, 100);`
2. **Verify Views Exist**: `\dv` in PostgreSQL to list views
3. **Check Nightly Script**: Last run time in `/var/log/meraki-mx-db.log`
4. **Browser Console**: Check for JavaScript/API errors

### Incorrect Site Counts
1. **Verify Data VLAN Filter**: Ensure only VLAN 1/100 counted for site identification
2. **Check 10.x Filter**: `SELECT COUNT(*) FROM network_vlans WHERE subnet LIKE '10.%';`
3. **Review Exclusions**: Confirm hub/voice/lab sites properly filtered

### Export Issues
1. **Excel Problems**: Ensure pandas and xlsxwriter installed: `pip3 list | grep -E "(pandas|xlsxwriter)"`
2. **CSV Issues**: Check browser download settings and popup blockers
3. **Large Exports**: May timeout on very large datasets (>1000 networks)

### Site Details Modal Issues
1. **Site Not Found**: Site name must match exactly (case-sensitive)
2. **No VLANs Shown**: Check if site has any VLAN data: `SELECT * FROM network_vlans WHERE network_name = 'SITE_NAME';`
3. **Missing /24 Info**: Verify parent_network field populated

## Data Quality Notes

### What Data is Included
- **Sites**: Only sites with data VLANs (VLAN 1 or 100) on 10.x networks
- **Networks**: Only 10.x IP space (corporate networks)
- **Grouping**: Based on actual data VLAN subnets, not all VLANs

### What Data is Excluded  
- **Guest Networks**: 172.x networks filtered out of main views
- **Non-Standard Sites**: Hub, voice, lab, and test networks
- **Non-Data VLANs**: Management, guest, and application VLANs not used for grouping
- **Non-10.x Networks**: 192.168.x, 198.18.x, and other non-corporate ranges

### Update Schedule
- **Nightly Collection**: 1:00 AM via cron job
- **Data Source**: Live Meraki API calls
- **Processing Time**: ~30-45 minutes for full collection
- **Availability**: New data available by 2:00 AM daily

## Security & Access
- **Read-Only**: No modification capabilities in web interface
- **Authentication**: Integrated with DSR Circuits session management  
- **Data Protection**: SQL injection protected via parameterized queries
- **XSS Prevention**: All user input sanitized and escaped

## Related Documentation
- [Nightly VLAN Collection Process](NIGHTLY_SCRIPTS.md#vlan-dhcp-collection)
- [Database Schema Details](../README.md#database-tables)
- [API Performance Monitoring](PERFORMANCE_MONITORING.md)
- [Home Page Navigation](HOME_PAGE.md)

---
**Last Updated**: July 6, 2025  
**Data Collection**: Updated nightly at 1:00 AM  
**Page Performance**: Optimized for 10.x corporate networks using data VLANs only