# DSR Circuits - Tag Management Documentation

## Overview
**URL**: `/tags`  
**File**: `/usr/local/bin/Main/tags.py`  
**Blueprint**: `tags_bp`  
**Purpose**: Network device tag management, bulk operations, and organizational structuring

## Page Layout & Components

### Header Section
- **Title**: "Network Device Tag Management"
- **Subtitle**: "Organize and categorize network infrastructure"
- **Tag Statistics**: Total tags, devices tagged, untagged devices
- **Last Sync**: Meraki API synchronization time

### Control Panel
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **Search Bar**: Find devices by name, serial, or tag
- **Filter Controls**: By device type, network, existing tags
- **Bulk Actions**: Apply tags to multiple devices
- **Import/Export**: CSV operations

## Tag Organization System

### Tag Categories
**Hierarchical Tag Structure**: Organized by purpose

#### Location Tags
```
Location/
├── Region/Southwest
├── Region/Northeast
├── State/TX
├── State/AZ
├── City/Phoenix
└── City/Houston
```

#### Device Role Tags
```
Role/
├── Core/Firewall
├── Core/Switch
├── Edge/AccessPoint
├── Edge/Camera
├── Special/Guest
└── Special/IoT
```

#### Status Tags
```
Status/
├── Production
├── Staging
├── Maintenance
├── Decommission
└── Spare
```

#### Custom Tags
```
Custom/
├── Project/2025-Refresh
├── Compliance/PCI
├── Priority/High
└── Owner/IT-Team
```

## Device Tag Interface

### Device List View
**Purpose**: See all devices with their current tags

#### Table Display
| Device Name | Serial | Model | Network | Current Tags | Actions |
|-------------|---------|--------|---------|--------------|---------|
| Store-001-MX | Q2XX-XXXX | MX67 | Store 001 | `Production` `Region/SW` `Role/Firewall` | Edit |
| Store-001-SW1 | Q2YY-YYYY | MS225 | Store 001 | `Production` `Region/SW` `Role/Switch` | Edit |
| Store-001-AP1 | Q2ZZ-ZZZZ | MR46 | Store 001 | `Production` `Region/SW` `Role/AP` | Edit |

#### Interactive Features
- **Click Tag**: Filter by that tag
- **Drag Tag**: Move between devices
- **Multi-Select**: Checkbox selection
- **Inline Edit**: Quick tag updates

### Tag Editor Modal
**Purpose**: Detailed tag editing for single device

#### Editor Features
- **Current Tags**: Visual tag chips
- **Available Tags**: Dropdown selector
- **Create New**: Add custom tags
- **Remove Tags**: Click X to remove
- **Tag History**: Previous tags

## Bulk Tag Operations

### CSV Import
**Purpose**: Mass tag updates via spreadsheet

#### CSV Format
```csv
Serial,Device Name,Add Tags,Remove Tags
Q2XX-XXXX-XXXX,Store-001-MX,"Region/Southwest;Priority/High","Status/Staging"
Q2YY-YYYY-YYYY,Store-001-SW1,"Region/Southwest;Role/CoreSwitch",""
```

#### Import Process
1. **Download Template**: Get current device list
2. **Edit Offline**: Add/remove tags in Excel
3. **Upload CSV**: Drag and drop file
4. **Preview Changes**: Review before apply
5. **Execute**: Apply all changes
6. **Report**: Success/failure summary

### Bulk Tag Builder
**Purpose**: Apply tags to multiple devices at once

#### Selection Methods
- **Manual Select**: Checkbox individual devices
- **Smart Select**: By model, network, or pattern
- **Query Select**: Advanced search criteria
- **Group Select**: Predefined device groups

#### Bulk Actions
```javascript
bulkOperations = {
    add: ["Region/Southwest", "Status/Production"],
    remove: ["Status/Staging"],
    replace: {
        old: "Priority/Low",
        new: "Priority/Medium"
    },
    clear: false // Remove all tags
};
```

## Tag Rules & Automation

### Auto-Tagging Rules
**Purpose**: Automatically apply tags based on criteria

#### Rule Examples
```javascript
// Auto-tag by model
{
    name: "Tag MX Devices",
    condition: "model LIKE 'MX%'",
    action: "add",
    tags: ["Role/Firewall", "Type/Security"]
}

// Auto-tag by network name
{
    name: "Southwest Stores",
    condition: "network LIKE 'TX-%' OR network LIKE 'AZ-%'",
    action: "add",
    tags: ["Region/Southwest"]
}

// Auto-tag new devices
{
    name: "New Device Setup",
    condition: "firstSeen > NOW() - INTERVAL 24 HOURS",
    action: "add",
    tags: ["Status/Staging", "Needs/Configuration"]
}
```

### Tag Inheritance
- **Network → Device**: Devices inherit network tags
- **Template Tags**: Apply template tag sets
- **Parent/Child**: Hierarchical inheritance
- **Override Rules**: Device-specific overrides

## Search & Filter

### Advanced Search
```sql
-- Search syntax
tag:"Region/Southwest" AND model:"MX*"
tag:"Priority/High" AND NOT tag:"Status/Production"
serial:"Q2*" AND (tag:"Maintenance" OR tag:"Staging")
network:"Store*" AND tagCount:">5"
```

### Filter Presets
1. **Untagged Devices**: No tags assigned
2. **Multi-Tagged**: More than 5 tags
3. **Missing Required**: Lacking mandatory tags
4. **Conflicting Tags**: Invalid combinations

## Tag Analytics

### Tag Usage Dashboard
**Visual Analytics**: Tag distribution and usage

#### Metrics Displayed
- **Most Used Tags**: Top 10 by device count
- **Tag Categories**: Distribution pie chart
- **Untagged Devices**: Count and percentage
- **Tag Growth**: Tags added over time
- **Tag Cleanup**: Unused tags

### Tag Reports
1. **Device Coverage**:
   ```
   Total Devices: 5,271
   Tagged: 4,956 (94%)
   Untagged: 315 (6%)
   Average Tags/Device: 3.2
   ```

2. **Tag Consistency**:
   - Missing required tags
   - Conflicting tag pairs
   - Deprecated tags in use
   - Standardization score

## Tag Policies

### Required Tags
**Mandatory Tags**: Every device must have

```javascript
requiredTags = {
    all: ["Status/*", "Region/*"],
    MX: ["Role/Firewall"],
    MS: ["Role/Switch"],
    MR: ["Role/AccessPoint"],
    MV: ["Role/Camera"]
};
```

### Tag Validation
- **Format Validation**: Correct hierarchy
- **Value Validation**: Allowed values only
- **Conflict Detection**: Incompatible tags
- **Requirement Check**: Missing required

### Tag Governance
```javascript
governance = {
    approval: ["Custom/*"], // Requires approval
    restricted: ["Compliance/*"], // Admin only
    deprecated: ["Old/*"], // Being phased out
    maxTags: 10 // Per device limit
};
```

## Integration Features

### Meraki API Sync
```python
def sync_device_tags():
    """Sync tags with Meraki dashboard"""
    dashboard = meraki.DashboardAPI(api_key)
    
    for network in networks:
        devices = dashboard.networks.getNetworkDevices(network['id'])
        
        for device in devices:
            # Get current tags
            current_tags = device.get('tags', [])
            
            # Get our tags
            our_tags = get_device_tags(device['serial'])
            
            # Sync if different
            if set(current_tags) != set(our_tags):
                dashboard.devices.updateDevice(
                    device['serial'],
                    tags=our_tags
                )
```

### Export Integration
- **ServiceNow**: Asset management sync
- **Monitoring**: Tag-based alerting
- **Reporting**: Business intelligence
- **Automation**: Ansible inventory

## Mobile Interface

### Mobile-Optimized Features
- **Simplified View**: Essential tags only
- **Swipe Actions**: Quick tag add/remove
- **Voice Input**: Tag by speaking
- **Barcode Scan**: Find device quickly

### Offline Capability
- **Cache Tags**: Work without connection
- **Queue Changes**: Sync when online
- **Conflict Resolution**: Handle conflicts

## API Endpoints

### Tag Management APIs
- `GET /api/tags` - List all tags
- `GET /api/devices/{serial}/tags` - Device tags
- `POST /api/devices/{serial}/tags` - Update tags
- `DELETE /api/devices/{serial}/tags/{tag}` - Remove tag

### Bulk Operations APIs
- `POST /api/tags/bulk-update` - Bulk tag update
- `POST /api/tags/import` - CSV import
- `GET /api/tags/export` - Export all tags
- `POST /api/tags/rules` - Auto-tag rules

### Analytics APIs
- `GET /api/tags/analytics` - Tag usage stats
- `GET /api/tags/compliance` - Policy compliance
- `GET /api/tags/suggestions` - AI suggestions

## Best Practices

### Tag Naming
1. **Use Hierarchy**: Category/Subcategory/Value
2. **Be Consistent**: Same format always
3. **Avoid Spaces**: Use-Hyphens-Instead
4. **Keep Short**: Maximum 3 levels
5. **Document Tags**: Maintain tag dictionary

### Tag Strategy
1. **Plan Structure**: Before implementation
2. **Start Simple**: Add complexity later
3. **Regular Review**: Quarterly cleanup
4. **Train Team**: Consistent usage
5. **Automate**: Where possible

### Performance Tips
1. **Limit Tags**: 5-7 per device optimal
2. **Index Tags**: For search performance
3. **Cache Results**: Reduce API calls
4. **Batch Updates**: Not one at a time

## Troubleshooting

### Common Issues

1. **Sync Failures**:
   - Check API rate limits
   - Verify permissions
   - Review error logs
   - Retry with backoff

2. **Missing Tags**:
   - Check sync status
   - Verify tag format
   - Look for conflicts
   - Force refresh

3. **Performance Issues**:
   - Reduce tag count
   - Optimize searches
   - Clear tag cache
   - Archive old tags

### Validation Queries
```sql
-- Devices missing required tags
SELECT serial, name, tags
FROM devices
WHERE NOT tags @> '["Status"]'
   OR NOT tags @> '["Region"]';

-- Tag usage statistics
SELECT tag, COUNT(*) as usage
FROM devices, LATERAL unnest(tags) as tag
GROUP BY tag
ORDER BY usage DESC;
```

---
*Last Updated: July 3, 2025*  
*Comprehensive network device tagging and organization*  
*Part of DSR Circuits Documentation Suite*