# DSR Circuits - Switch Port Visibility Documentation

## Overview
**URL**: `/switch-visibility`  
**File**: `/usr/local/bin/Main/switch_visibility.py`  
**Blueprint**: `switch_visibility_bp`  
**Purpose**: Real-time switch port monitoring, client identification, and network troubleshooting

## Page Layout & Components

### Header Section
- **Title**: "Switch Port Visibility"
- **Subtitle**: "Real-time port status and client tracking"
- **Auto-Refresh Toggle**: Enable/disable live updates
- **Refresh Interval**: 30 seconds default

### Control Panel
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **Store Selector**: Dropdown list of all stores
- **Switch Selector**: Switches at selected store
- **Refresh Button**: Manual data refresh
- **Export Button**: Download port data

## Main Display Areas

### Store Switch Overview
**Purpose**: Summary of all switches at selected store

#### Switch Cards
```
┌─────────────────────────┐
│ MS225-48LP             │
│ Serial: Q2XX-XXXX-XXXX │
│ ━━━━━━━━━━━━━━━━━━━━━ │
│ Ports: 48 | Used: 36   │
│ PoE: 370W/740W         │
│ Uplink: Port 49-50     │
│ Status: ● Online       │
└─────────────────────────┘
```

#### Card Features
- **Visual Port Map**: Mini representation of ports
- **Usage Indicator**: Color-coded by utilization
- **PoE Budget**: Power consumption gauge
- **Click Action**: Expand to full port details

### Detailed Port View
**Purpose**: Comprehensive port-by-port visibility

#### Port Information Grid
| Port | Status | Client | MAC Address | IP Address | VLAN | Speed | PoE |
|------|---------|---------|-------------|------------|------|--------|-----|
| 1 | 🟢 Connected | POS Terminal 1 | AA:BB:CC:DD:EE:01 | 10.1.1.101 | 10 | 1 Gbps | 15.4W |
| 2 | 🟢 Connected | Credit Card Reader | AA:BB:CC:DD:EE:02 | 10.1.1.102 | 10 | 100 Mbps | 6.5W |
| 3 | ⚫ Disabled | - | - | - | - | - | - |
| 4 | 🔴 Disconnected | - | - | - | - | - | - |
| 5 | 🟡 Warning | Unknown Device | AA:BB:CC:DD:EE:05 | - | 1 | 10 Mbps | - |

#### Status Indicators
- **🟢 Connected**: Active with client
- **🔴 Disconnected**: No link
- **🟡 Warning**: Issues detected
- **⚫ Disabled**: Administratively down
- **🔵 Trunk**: Uplink/trunk port

### Client Identification

#### Known Device Types
```javascript
const devicePatterns = {
    'POS': /^(AA:BB|CC:DD)/,
    'Phone': /^(11:22|33:44)/,
    'Printer': /^(55:66|77:88)/,
    'Camera': /^(99:AA|BB:CC)/,
    'AP': /^(DD:EE|FF:00)/,
    'Unknown': /.*/ // Default
};
```

#### Client Details Panel
- **Device Name**: Friendly name if known
- **MAC Address**: Hardware address
- **Manufacturer**: OUI lookup result
- **IP Address**: Current IP assignment
- **First Seen**: When first detected
- **Last Seen**: Most recent activity
- **Data Usage**: Traffic statistics

## Search & Filter

### Quick Filters
- **Port Status**: Connected, Disconnected, Warning
- **Client Type**: POS, Phone, Printer, Camera, etc.
- **VLAN**: Filter by VLAN ID
- **PoE Status**: Powered, Not Powered
- **Speed**: 10/100/1000 Mbps

### Search Functionality
```javascript
// Search examples
"mac:AA:BB:*" // MAC address search
"ip:10.1.1.*" // IP address search
"vlan:10" // VLAN search
"client:POS" // Client type search
"port:1-24" // Port range search
```

## Real-Time Monitoring

### Live Updates
**WebSocket Connection**: Real-time port changes

#### Event Types
- **Link Up**: Port connected
- **Link Down**: Port disconnected
- **New Client**: Unknown MAC detected
- **PoE Alert**: Power threshold exceeded
- **Error**: Port errors/collisions

### Alert Configuration
```javascript
alerts: {
    linkDown: true,
    newDevice: true,
    poeThreshold: 90, // percent
    errorThreshold: 100, // errors per minute
    notification: 'dashboard|email|sms'
}
```

## Troubleshooting Tools

### Port Diagnostics
**Purpose**: Detailed port troubleshooting

#### Available Tests
1. **Cable Test**:
   - Test cable integrity
   - Distance to fault
   - Pair status

2. **Port Statistics**:
   - Packet counts
   - Error counts
   - Utilization graphs

3. **MAC Table**:
   - All MACs on port
   - MAC history
   - MAC moves

4. **LLDP Info**:
   - Neighbor details
   - Topology mapping
   - CDP compatibility

### Historical Data
- **Port History**: Link up/down events
- **Client History**: Device connections
- **Error History**: Historical error rates
- **Performance**: Utilization over time

## Integration Features

### Meraki API Integration
```python
def get_switch_port_statuses(serial):
    """Get real-time port statuses"""
    dashboard = meraki.DashboardAPI(api_key)
    
    # Get port statuses
    statuses = dashboard.switch.getDeviceSwitchPortsStatuses(serial)
    
    # Get port configs
    configs = dashboard.switch.getDeviceSwitchPorts(serial)
    
    # Merge data
    return merge_port_data(statuses, configs)
```

### Client Identification
```python
def identify_client(mac_address):
    """Identify device type from MAC"""
    # Check known devices table
    known = lookup_known_device(mac_address)
    if known:
        return known
    
    # OUI lookup
    manufacturer = lookup_oui(mac_address[:8])
    
    # Pattern matching
    device_type = match_device_pattern(mac_address)
    
    return {
        'mac': mac_address,
        'manufacturer': manufacturer,
        'type': device_type
    }
```

## Bulk Operations

### Port Configuration
**Purpose**: Bulk port management

#### Bulk Actions
- **Enable/Disable**: Multiple ports
- **VLAN Assignment**: Bulk VLAN changes
- **PoE Control**: Enable/disable PoE
- **Port Naming**: Bulk description updates

### Template Application
```javascript
// Port template example
const posTemplate = {
    enabled: true,
    vlan: 10,
    poeEnabled: true,
    type: 'access',
    stpGuard: 'bpdu',
    description: 'POS Terminal'
};
```

## Visualization Features

### Switch Faceplate View
```
┌─────────────────────────────────────────────┐
│ [1] [2] [3] [4] [5] [6] ... [45][46][47][48]│
│ 🟢  🟢  ⚫  🔴  🟢  🟢      🟢  🟢  🔵  🔵 │
└─────────────────────────────────────────────┘
```

### Heat Map View
- **Utilization Heat Map**: Color by usage
- **Error Heat Map**: Color by error rate
- **PoE Heat Map**: Color by power draw
- **Age Heat Map**: Color by connection age

### Topology View
- **Connected Devices**: Visual tree
- **VLAN Visualization**: Color by VLAN
- **Traffic Flow**: Animated flows
- **Physical Layout**: Rack positioning

## Export & Reporting

### Export Formats
1. **Port Report** (Excel):
   - All ports with status
   - Client information
   - Configuration details
   - Historical data

2. **Troubleshooting Report** (PDF):
   - Error summary
   - Problem ports
   - Recommendations
   - Historical trends

3. **Inventory Report** (CSV):
   - Connected devices
   - MAC addresses
   - IP assignments
   - Device types

### Scheduled Reports
- **Daily Summary**: Port utilization
- **Weekly Alerts**: New devices detected
- **Monthly Analysis**: Trending and capacity
- **Compliance**: Unauthorized devices

## Mobile Features

### Mobile Interface
- **Simplified View**: Essential info only
- **Swipe Navigation**: Between switches
- **Touch Targets**: Large port buttons
- **Quick Actions**: Enable/disable ports

### Mobile-Specific Tools
- **Cable Tester**: Initiate from mobile
- **Photo Upload**: Document installations
- **Barcode Scan**: Quick switch lookup
- **Voice Notes**: Troubleshooting notes

## API Endpoints

### Port Data APIs
- `GET /api/switches/{store}/ports` - All ports for store
- `GET /api/switch/{serial}/ports` - Specific switch ports
- `GET /api/port/{serial}/{port}` - Single port details
- `POST /api/port/{serial}/{port}/test` - Run cable test

### Bulk Operations APIs
- `POST /api/ports/bulk-update` - Update multiple ports
- `POST /api/ports/template` - Apply template
- `GET /api/ports/export` - Export port data

## Performance Optimization

### Caching Strategy
- **Port Status**: 30-second cache
- **Client Data**: 5-minute cache
- **Static Config**: 1-hour cache
- **Invalidation**: On configuration change

### Data Aggregation
- **Store Level**: Pre-aggregate metrics
- **Switch Level**: Summary statistics
- **Historical**: Hourly rollups
- **Alerts**: Real-time processing

## Use Cases

### Daily Operations
1. Check port status each morning
2. Verify all POS terminals online
3. Investigate any warnings
4. Document any changes

### Troubleshooting
1. User reports connectivity issue
2. Find their switch port
3. Check port status and history
4. Run cable test if needed
5. Review error counters

### New Device Installation
1. Connect new device
2. Monitor for port to come up
3. Verify correct VLAN
4. Label port appropriately
5. Document in system

### Security Monitoring
1. Review new devices daily
2. Investigate unknown MACs
3. Check for unauthorized devices
4. Generate compliance reports

---
*Last Updated: July 3, 2025*  
*Real-time switch port monitoring and management*  
*Part of DSR Circuits Documentation Suite*