# DSR Circuits - Home Page Documentation

## Overview
**URL**: `/home`  
**File**: `/usr/local/bin/Main/dsrcircuits.py`  
**Template**: `/usr/local/bin/Main/templates/home.html`  
**Purpose**: Main landing page and navigation hub for the DSR Circuits system

## Page Layout & Components

### Header Section
- **Title**: "Discount Tire Network Management System"
- **Subtitle**: "Central hub for circuit tracking, monitoring, and inventory management"
- **Responsive Design**: Adapts to desktop, tablet, and mobile devices

### Navigation Grid
The home page features a comprehensive navigation grid with specialized cards for each major system function.

## Interactive Navigation Cards

### 📡 SDWAN Circuit Management
- **URL**: `/dsrcircuits`
- **Purpose**: Advanced circuit tracking and Meraki integration interface
- **Description**: View, edit, confirm and push circuit configurations to Meraki devices
- **Key Features**:
  - **Home Button**: Return to main navigation
  - **1 Circuit Button**: View individual circuit details
  - **Push to Meraki Button**: Deploy configurations to Meraki devices
  - **Add Circuit Button**: Create new circuit entries
  - **Filter Controls**: Search by provider, status, store details
  - **Sortable Table**: Store Number, Circuit ID, Provider, Type, Status columns
- **Interface Preview**: Shows live data with status indicators (Active, Pending)
- **User Access**: Network provisioning teams

### 📋 All Circuits
- **URL**: `/dsrallcircuits`
- **Purpose**: Complete database view of all enabled circuits
- **Description**: Sortable and filterable table showing site names, IDs, circuit purposes, providers, speeds, and costs
- **Key Features**:
  - **Triple Filter System**: Site Name, Site ID, Provider search fields
  - **Comprehensive Data View**: Site details, circuit purpose, provider tags, speed specifications, cost information
  - **Provider Color Coding**: Visual indicators for AT&T (blue), Comcast (red), Cox (cyan)
  - **Cost Tracking**: Real-time monthly cost display
  - **Record Count**: Shows total enabled circuits (2,020+)
- **Data Display**: 6-column sortable table with color-coded provider tags
- **User Access**: Management and reporting teams

### 📊 Status Dashboard  
- **URL**: `/dsrdashboard`
- **Purpose**: Real-time circuit status overview with visual indicators
- **Description**: Monitor circuit health, connectivity status, and identify issues at a glance
- **Key Features**:
  - **Category Filters**: Ready for Turn Up, In Progress, Enabled, Issues, Order Canceled
  - **Assignment Management**: SCTASK and team member tracking
  - **Live Status Updates**: Real-time connectivity monitoring
  - **Color-Coded Indicators**: Green (Active), Orange (Pending), Red (Issues)
  - **Circuit Count Display**: Shows counts for each status category
- **Special Capabilities**:
  - Assignment data merging from circuit_assignments table
  - Record number-based tracking for accurate correlation
  - Site-based counting to prevent duplicates
- **User Access**: Network operations teams

### 📜 Historical Data
- **URL**: `/dsrhistorical`
- **Purpose**: Circuit change tracking and historical analysis
- **Description**: Track circuit modifications, status changes, and historical trends over time
- **Key Features**:
  - **Change Log Tracking**: Complete audit trail of circuit modifications
  - **Historical Analysis**: Trend analysis and pattern identification
  - **Date Range Filtering**: Custom time period selection
  - **Export Capabilities**: CSV and Excel export for reporting
- **User Access**: Compliance and audit teams

### 📈 Daily Enablement Report
- **URL**: `/circuit-enablement-report`
- **Purpose**: Analytics and performance tracking for circuit enablements
- **Description**: Comprehensive reporting with multiple analysis views and team attribution
- **Key Features**:
  - **4-Tab Interface**: 
    - **📈 Enablement Report**: Daily trends and summary statistics
    - **📋 Ready Queue Tracking**: Queue size monitoring and metrics  
    - **👥 Team Attribution**: Individual team member performance tracking
    - **📄 Enablement Details**: Detailed transaction logs
  - **Date Range Controls**: All data, Last N Days, Custom date range options
  - **Generate All Reports Button**: Unified report generation across all tabs
  - **Export Options**: Excel, PDF, and Print capabilities
- **Special Capabilities**:
  - Team attribution with assignment correlation
  - Daily trends with 0-value date inclusion
  - Performance metrics and anomaly detection
- **User Access**: Management and performance tracking teams

### 🏗️ New Stores Management
- **URL**: `/new-stores`  
- **Purpose**: Store construction and circuit planning management
- **Description**: Target Opening Date (TOD) tracking, bulk Excel uploads, circuit creation
- **Key Features**:
  - **Manual Circuit Creation**: Generate circuits with auto-record number creation
  - **Excel Bulk Upload**: Import store data via Excel templates
  - **TOD Tracking**: Target Opening Date management and milestone tracking
  - **Meraki Auto-Detection**: Automatic cleanup when stores go live
  - **Status Management**: Construction progress tracking
- **Special Capabilities**:
  - **Record Number Generation**: Auto-generates unique DSR-format record numbers
  - **Manual Override Protection**: Prevents DSR pull from overwriting manual entries
  - **Data Source Tracking**: Maintains creation attribution
- **User Access**: Construction and provisioning teams

### 📋 Inventory Summary
- **URL**: `/inventory-summary`
- **Purpose**: High-level network device management and monitoring
- **Description**: Device tracking, EOL monitoring, capacity planning with visual dashboards
- **Key Features**:
  - **Device Type Filters**: All Regions and All Device Types dropdowns
  - **Export Functionality**: Comprehensive data export capabilities
  - **Device Count Cards**: Visual display of device types
    - **MX Firewalls**: 847 devices tracked
    - **MS Switches**: 1,234 devices tracked  
    - **MR Access Points**: 2,567 devices tracked
    - **MV Cameras**: 423 devices tracked
  - **Deployment Progress**: Overall progress bar (85% completion shown)
  - **Real-time Metrics**: 4,456 of 5,271 devices deployed
- **Visual Elements**: Color-coded device type indicators and progress tracking
- **User Access**: Network operations and planning teams

### 📋 Inventory Details  
- **URL**: `/inventory-details`
- **Purpose**: Detailed inventory information and device tracking
- **Description**: Access serial numbers, configurations, and comprehensive equipment data
- **Key Features**:
  - **Advanced Search**: Search by serial number or store name
  - **Detailed Device Data**: Serial numbers, configurations, firmware versions
  - **Configuration Tracking**: Device-specific settings and parameters
  - **Maintenance Records**: Service history and update tracking
- **User Access**: Technical teams and device administrators

### 🔍 Switch Port Visibility
- **URL**: `/switch-visibility`
- **Purpose**: Switch port client monitoring and analysis
- **Description**: Port utilization tracking, client identification, and network troubleshooting
- **Key Features**:
  - **Real-time Port Client Discovery**: Live monitoring of connected devices
  - **Store-Specific Switch Monitoring**: Filter by individual store locations
  - **Port Utilization Analytics**: Usage patterns and capacity analysis
  - **Client Device Identification**: MAC address and device type tracking
  - **Refresh Controls**: Manual refresh by store or switch serial
- **Special Capabilities**:
  - Live API integration with Meraki switches
  - Port-level client tracking and identification
  - Export functionality for analysis
- **User Access**: Network troubleshooting and operations teams

### 🔥 Meraki MX Firewall Rules Editor
- **URL**: `/firewall`
- **Purpose**: Security rule administration and firewall management
- **Description**: Template management, rule deployment, live rule viewing
- **Key Features**:
  - **Template-Based Rule Management**: Standardized firewall rule templates
  - **Live Firewall Rule Viewing**: Real-time rule display from Meraki API
  - **Bulk Deployment**: Deploy rules across multiple networks simultaneously
  - **Rule Revision Tracking**: Version control for rule changes
  - **Network Selection**: Target specific networks for rule deployment
- **Special Capabilities**:
  - Direct Meraki API integration for live rule management
  - Template system for consistent rule deployment
  - Revision history and rollback capabilities
- **User Access**: Security and network administration teams

### 📈 System Health Monitor
- **URL**: `/system-health`
- **Purpose**: Infrastructure monitoring and diagnostics
- **Description**: Real-time health metrics, alert management, and system status monitoring
- **Key Features**:
  - **Real-time Health Metrics**: Live system performance indicators
  - **Alert Management**: Critical alert tracking and notification
  - **Service Status Monitoring**: Individual service health checks
  - **Performance Dashboards**: System resource utilization tracking
- **User Access**: IT operations and system administrators

### 🚀 Performance Monitoring
- **URL**: `/performance`
- **Purpose**: System performance tracking and optimization
- **Description**: Response time monitoring, anomaly detection, and performance analytics
- **Key Features**:
  - **Response Time Monitoring**: API and page load performance tracking
  - **Anomaly Detection**: Automated performance issue identification
  - **Historical Performance Data**: Trend analysis and baseline comparison
  - **Performance Optimization**: Bottleneck identification and recommendations
- **User Access**: System administrators and performance teams

### 🏷️ Tag Management
- **URL**: `/tags`
- **Purpose**: Network device tag management and organization
- **Description**: Bulk tag operations, CSV uploads, device organization
- **Key Features**:
  - **Bulk Tag Updates**: Mass tag assignment via CSV upload
  - **Device-Specific Tag Management**: Individual device tag editing
  - **Network-Wide Tag Operations**: Apply tags across entire networks
  - **Tag Validation**: Conflict detection and resolution
  - **Upload Processing**: CSV file validation and batch processing
- **Special Capabilities**:
  - CSV template system for bulk operations
  - Tag conflict resolution and validation
  - Integration with Meraki API for live tag updates
- **User Access**: Network administrators and operations teams

## External Integration Cards

### 🔧 Git Repository
- **URL**: `http://10.0.145.130:3003/mbambic/usr-local-bin`
- **Purpose**: Version control and code repository access
- **Description**: Access to project source code, documentation, and version history
- **User Access**: Development and administrative teams

### ⚙️ AWX Automation
- **URL**: `http://10.0.145.130:30483`  
- **Purpose**: Ansible automation platform integration
- **Description**: Automated deployment, configuration management, and task orchestration
- **User Access**: DevOps and automation teams

### 🔍 Netdisco Network Discovery
- **URL**: `http://10.0.145.130:5000`
- **Purpose**: Network device discovery and topology mapping
- **Description**: Automated network discovery, device identification, and topology visualization
- **User Access**: Network discovery and mapping teams

### 📊 LibreNMS Monitoring
- **URL**: `http://10.0.145.130:8686`
- **Purpose**: Network monitoring and alerting system
- **Description**: Comprehensive network device monitoring, SNMP polling, and alert management
- **User Access**: Network monitoring and operations teams

## Technical Implementation

### Real-time Data Sources
- **Circuit Statistics**: PostgreSQL circuits table (4,171+ records)
- **Network Health**: Meraki API integration for live device status
- **System Metrics**: Internal APIs for performance monitoring
- **Alert Status**: Redis-cached alert information

### Performance Features
- **Responsive Grid Layout**: Auto-fitting card layout adapts to screen size
- **Hover Effects**: Visual feedback with transform and shadow effects
- **Color-Coded Cards**: Unique gradient colors for each functional area
- **Loading States**: Skeleton loading animations for data-heavy cards
- **Progressive Enhancement**: Core functionality works without JavaScript

### Card Interface Previews
Each navigation card includes a detailed interface preview showing:
- **Browser Window Simulation**: Realistic browser chrome with traffic light controls
- **Page Headers**: Actual page titles and branding
- **Control Elements**: Buttons, filters, and form controls
- **Data Tables**: Sample data with realistic formatting
- **Status Indicators**: Color-coded status and progress elements

## User Scenarios

### Daily Operations Team
1. **Morning Check**: Review system health and circuit status on home page
2. **Issue Response**: Navigate to Status Dashboard for urgent circuit issues
3. **Team Coordination**: Check Daily Enablement Report for team performance
4. **Documentation**: Access specific tool documentation as needed

### Network Engineers  
1. **Troubleshooting**: Use Switch Port Visibility for connectivity issues
2. **Configuration**: Access Firewall Rules Editor for security changes
3. **Planning**: Review Inventory Summary for capacity planning
4. **Maintenance**: Update device tags for better organization

### Management Team
1. **Performance Review**: Access Daily Enablement Report for KPIs
2. **Strategic Planning**: Review All Circuits for cost and provider analysis
3. **Team Management**: Monitor team attribution and performance metrics
4. **Compliance**: Access Historical Data for audit requirements

### Construction Team
1. **Project Tracking**: Use New Stores Management for TOD coordination
2. **Circuit Planning**: Create circuits for upcoming store openings  
3. **Progress Monitoring**: Track construction milestones and deadlines
4. **Handoff Coordination**: Manage transition from construction to operations

## Related Documentation
- [DSR Dashboard](DSR_DASHBOARD.md)
- [New Stores Management](NEW_STORES.md)
- [Circuit Enablement Report](CIRCUIT_ENABLEMENT_REPORT.md)
- [System Health Monitor](SYSTEM_HEALTH.md)
- [Firewall Management](FIREWALL_MANAGEMENT.md)

---
*Last Updated: July 3, 2025*  
*Comprehensive documentation including all navigation cards and interactive features*  
*Part of DSR Circuits Documentation Suite*