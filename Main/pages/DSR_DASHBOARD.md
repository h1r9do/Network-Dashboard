# DSR Circuits - Dashboard Documentation

## Overview
**URL**: `/dsrdashboard`  
**Route Handler**: `/usr/local/bin/Main/dsrcircuits.py` (routes to `/dsrdashboard`)
**Template**: `/usr/local/bin/templates/dsrdashboard.html` (Note: Flask uses `/usr/local/bin/templates/`, not `/usr/local/bin/Main/templates/`)
**Purpose**: Real-time circuit status tracking and assignment management dashboard with interactive filtering

## Page Layout & Components

### Header Section
- **Title**: "Circuit Status Dashboard"
- **Live Row Count**: Displays last updated timestamp and total record count
- **Real-time Updates**: Automatically refreshes data every 30 seconds

### Navigation Controls
- **🏠 Home Button**: Returns to main navigation page (`/home`)
- **Responsive Design**: Adapts to desktop, tablet, and mobile layouts

## Interactive Dashboard Features

### Action Required Sidebar
**Title**: "Action Required - Click Any Item to Filter"  
**Functionality**: Interactive filtering system with live circuit counts

#### Filter Categories (Clickable Action Items)

##### 🟡 Ready for Turn Up
- **Color**: Yellow accent border (`#ffc107`)
- **Purpose**: Circuits awaiting enablement and activation
- **Count Display**: Live count of circuits ready for deployment
- **Details Panel**: Shows breakdown of ready circuits with assignment information
- **Special Features**: 
  - Enhanced with assignment data merging
  - SCTASK and assigned team member display
  - Site-based counting (prevents duplicates)

##### 🔴 Customer Action Required  
- **Color**: Red accent border (`#dc3545`)
- **Purpose**: Circuits requiring customer intervention
- **Count Display**: Live count of circuits waiting for customer response
- **Details Panel**: Lists customer action items and pending requirements

##### 🔴 NOC Action Required
- **Color**: Red accent border (`#dc3545`) 
- **Purpose**: Circuits requiring Network Operations Center intervention
- **Count Display**: Live count of circuits needing NOC attention
- **Details Panel**: Technical issues and escalated problems requiring NOC resolution

##### 🟠 Real Estate Action Required
- **Color**: Orange accent border (`#fd7e14`)
- **Purpose**: Circuits requiring real estate or site preparation
- **Count Display**: Live count of circuits blocked by real estate issues
- **Details Panel**: Site access, permitting, and property-related blocking issues

##### ⚫ Construction
- **Color**: Gray accent border (`#6c757d`)
- **Purpose**: Circuits in construction or infrastructure phase
- **Count Display**: Live count of circuits in construction status
- **Details Panel**: Active construction projects and infrastructure work

##### ⚫ Other
- **Color**: Gray accent border (`#6c757d`)
- **Purpose**: Circuits with miscellaneous status requirements
- **Count Display**: Live count of circuits with undefined or special status
- **Details Panel**: Various other status categories not covered above

### Interactive Behavior
- **Click to Filter**: Each action item filters the main data table
- **Active State Highlighting**: Selected filter shows blue background and shadow
- **Hover Effects**: Visual feedback with transform and shadow animations  
- **Responsive Design**: Sidebar collapses on mobile devices

### Details Panel
**Dynamic Content Area**: Changes based on selected filter category

#### Content Features
- **Details Title**: Updates to match selected category
- **Description Text**: Contextual information about the selected status
- **Substatus Breakdown**: Detailed subcategory information when available
- **Live Data**: Real-time updates as circuit statuses change

#### Assignment Information Display
Enhanced July 2025 with comprehensive assignment data:
- **SCTASK Numbers**: ServiceNow ticket correlation
- **Assigned Team Members**: Individual responsibility tracking
- **Assignment Status**: Active assignment tracking
- **Historical Data**: Assignment change history

## Data Sources & Integration

### Primary Data Sources
- **PostgreSQL circuits table**: 4,171+ circuit records
- **circuit_assignments table**: Active assignment data
- **Meraki API**: Real-time device status integration
- **DSR Global CSV**: Daily imports with record_number tracking

### Enhanced Features (July 2025)
#### Record Number Integration
- **Primary Key Tracking**: Uses DSR Global record_numbers for correlation
- **Cross-System Sync**: Accurate tracking between DSR Global, database, and ServiceNow
- **Duplicate Prevention**: Site-based counting eliminates duplicate records

#### Assignment Data Merging
```python
# Enhanced assignment data retrieval
assignments = CircuitAssignment.query.filter_by(status='active').all()
assignment_data = {assignment.site_name: {
    'sctask': assignment.sctask or '',
    'assigned_to': assignment.assigned_to or ''
} for assignment in assignments}

# Priority merging (assignment table takes precedence)
if site_assignment.get('assigned_to'):
    circuit_dict['assigned_to'] = site_assignment['assigned_to']
if site_assignment.get('sctask'):
    circuit_dict['sctask'] = site_assignment['sctask']
```

### Performance Optimizations
- **Efficient Database Queries**: Indexed lookups on site_id and record_number
- **Redis Caching**: Response caching for frequently accessed data
- **Real-time Updates**: WebSocket integration for live data synchronization
- **Batch Processing**: Optimized bulk data operations

## API Endpoints

### Primary API
**`/api/dashboard-data`** - Main dashboard data retrieval
- **Method**: GET
- **Parameters**: Optional category filters
- **Response**: Circuit data with counts, assignments, and status breakdown
- **Caching**: Redis-backed with 30-second refresh interval

### Assignment Management
**`/api/save-assignment`** - Update circuit assignments
- **Method**: POST
- **Purpose**: Assign SCTASK numbers and team members
- **Data**: Circuit ID, SCTASK, assigned team member
- **Validation**: Assignment conflict checking

**`/api/get-assignments`** - Retrieve assignment data
- **Method**: GET
- **Purpose**: Get current assignment information
- **Response**: Assignment data with historical tracking

## Technical Implementation

### JavaScript Architecture
The dashboard uses a client-side JavaScript application that:
- Fetches data from `/api/dashboard-data` endpoint
- Stores all circuit data in `allData` array
- Implements interactive filtering without page reloads
- Updates UI dynamically based on selected filters

### Database Schema
- **circuits**: Primary circuit data (site_name, status, record_number)
- **circuit_assignments**: Assignment tracking (sctask, assigned_to, status)
- **circuit_history**: Historical change tracking
- **enriched_circuits**: Enhanced circuit data with provider information

### Status Categorization Logic
```javascript
// Dynamic status categorization
const categorizeStatus = (status) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('ready for turn up') || 
        statusLower.includes('ready for enablement')) return 'ready';
    if (statusLower.includes('customer action')) return 'customer-action';
    if (statusLower.includes('noc action')) return 'noc-action';
    if (statusLower.includes('real estate')) return 'real-estate-action';
    if (statusLower.includes('construction')) return 'construction';
    return 'other';
};
```

### Real-time Updates
- **Auto-refresh**: 30-second interval for live data updates
- **WebSocket Integration**: Real-time status change notifications
- **Optimistic Updates**: Immediate UI feedback for user actions
- **Error Handling**: Graceful degradation and retry mechanisms

## User Workflows

### Network Technician Daily Tasks
1. **Access Dashboard**: Navigate to `/dsrdashboard`
2. **Review Ready Circuits**: Click "Ready for Turn Up" filter
3. **Check Assignments**: Review SCTASK and team member assignments
4. **Update Status**: Mark circuits as completed upon enablement
5. **Monitor Progress**: Track team performance and completion rates

### Team Lead Management
1. **Workload Balancing**: Review assignment distribution across team
2. **Priority Management**: Focus on high-priority circuits and customer escalations
3. **Performance Tracking**: Monitor individual and team completion metrics
4. **Issue Escalation**: Identify and address blocked circuits

### NOC Operations
1. **Technical Issues**: Monitor NOC action required circuits
2. **Escalation Response**: Address technical problems and outages
3. **Vendor Coordination**: Manage provider-related issues and repairs
4. **Status Updates**: Maintain accurate circuit status information

## Data Quality Features

### Enhanced Accuracy (July 2025)
- **Site-Based Counting**: Counts unique sites instead of circuit records (fixed 14→10 duplicate issue)
- **Record Number Correlation**: Uses DSR Global record_numbers for precise tracking
- **Assignment Data Validation**: Ensures SCTASK and team member data accuracy

### Problem Resolution Examples
- **INI 06**: Now shows `assigned_to="Taren Andrickson"` ✅
- **MSG 01**: Now shows `assigned_to="Taren Andrickson"` ✅  
- **TXH 97**: Now shows `assigned_to="Taren Andrickson"` ✅
- **TXD 76**: Now shows both assignment and SCTASK data ✅
- **TXS 24**: Now shows `assigned_to="Taren Andrickson"` ✅

## Mobile Responsiveness

### Adaptive Layout
- **Desktop**: Full sidebar + details panel layout
- **Tablet**: Compressed sidebar with abbreviated labels
- **Mobile**: Stacked layout with collapsible sidebar
- **Touch Optimization**: Large click targets for mobile interaction

### Mobile-Specific Features
- **Swipe Navigation**: Touch gestures for category switching
- **Responsive Tables**: Horizontal scrolling for detailed data
- **Optimized Typography**: Readable font sizes on small screens

## Debugging Features

### Built-in Debug Console
The dashboard includes comprehensive debugging tools accessible through the browser console:

```javascript
// Available debug commands:
debugDashboard.test()     // Run comprehensive system tests
debugDashboard.status()   // Show current dashboard status
debugDashboard.ready()    // Analyze ready for turn up circuits
debugDashboard.compare()  // Compare displayed data with database
debugDashboard.timing()   // Show API performance metrics
```

### Debug Information Tracked
- API call history with response times
- Data record counts and filtering results
- Performance metrics (load time, render time)
- Error logging with stack traces
- Recent activity log

### Common Issues & Solutions

#### Template Location Issue (Fixed July 7, 2025)
- **Problem**: Flask app uses `/usr/local/bin/templates/` but files may be edited in `/usr/local/bin/Main/templates/`
- **Solution**: Ensure template changes are made to `/usr/local/bin/templates/dsrdashboard.html`
- **Verification**: Check template path in Flask config: `template_folder='/usr/local/bin/templates'`

#### JavaScript Syntax Errors
- **Problem**: Extra closing braces or missing catch blocks
- **Solution**: Use browser console to identify syntax errors
- **Prevention**: Validate JavaScript changes before deployment

## Integration Points

### External Systems
- **ServiceNow**: SCTASK ticket correlation and assignment tracking
- **DSR Global**: Daily CSV imports with record_number synchronization  
- **Meraki API**: Real-time device status and configuration data
- **New Stores Module**: Construction project coordination

### Related Pages
- [Circuit Orders](CIRCUIT_ORDERS.md) - Order management and tracking
- [Circuit Enablement Report](CIRCUIT_ENABLEMENT_REPORT.md) - Performance analytics
- [New Stores Management](NEW_STORES.md) - Construction project integration

## Key Implementation Details

### Data Flow
1. **Page Load**: `DOMContentLoaded` event triggers `loadDashboardData()`
2. **API Call**: Fetches from `/api/dashboard-data` using `debugApiCall()` wrapper
3. **Data Storage**: Response stored in `dashboardData` object and `allData` array
4. **Initial Display**: Shows "Ready for Turn Up" circuits by default
5. **Interactive Filtering**: Click events on sidebar items filter the table without new API calls

### Global Variables
- `allData`: Array containing all circuit records from API
- `dashboardData`: Complete API response including stats and breakdowns
- `currentFilter`: Active filter state (e.g., 'category:ready')
- `currentCategory`: Currently selected category for display
- `debugData`: Debug information tracking

### Filter Functions
- `applyStatusFilter()`: Filters by status text
- `applyNOCActionFilter()`: Special handling for NOC action items
- `applyRealEstateActionFilter()`: Real estate specific filtering
- `showCategoryDetails()`: Updates sidebar details panel
- `renderTable()`: Renders filtered data to HTML table

---
*Last Updated: July 7, 2025*  
*Enhanced with debugging features, template path clarification, and comprehensive implementation details*  
*Part of DSR Circuits Documentation Suite*