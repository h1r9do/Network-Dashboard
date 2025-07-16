# DSR Circuits - Historical Data Documentation

## Overview
**URL**: `/dsrhistorical`  
**File**: `/usr/local/bin/Main/historical.py`  
**Blueprint**: `historical_bp`  
**Purpose**: Circuit change tracking, audit trails, and historical trend analysis

## Page Layout & Components

### Header Section
- **Title**: "DSR Circuit Historical Data"
- **Subtitle**: "Track changes and analyze trends over time"
- **Last Updated**: Shows data freshness timestamp

### Navigation & Controls
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **Date Range Picker**: Select historical period to analyze
- **Search Bar**: Find specific circuits or changes
- **Export Button**: Download historical data

## Main Features

### Circuit Change History Table
**Purpose**: Complete audit trail of all circuit modifications

#### Table Columns
- **Timestamp**: When the change occurred
- **Site Name**: Circuit location
- **Site ID**: Unique identifier
- **Field Changed**: What was modified
- **Old Value**: Previous value
- **New Value**: Updated value
- **Changed By**: User/system that made change
- **Change Type**: Auto/Manual/System

#### Interactive Features
- **Sortable Columns**: Click headers to sort
- **Filterable**: Quick filters per column
- **Expandable Rows**: Show full change context
- **Color Coding**: Visual change indicators

### Change Analytics Dashboard
**Purpose**: Visualize patterns in circuit modifications

#### Metric Cards
- **Total Changes**: Count in selected period
- **Most Changed Sites**: Top 10 by change frequency
- **Common Changes**: Most frequent field modifications
- **Change Velocity**: Changes per day trend

#### Visualization Components
- **Timeline Chart**: Changes over time
- **Heat Map**: Change intensity by site/date
- **Category Breakdown**: Pie chart of change types
- **User Activity**: Changes by user/system

## Search & Filter Capabilities

### Quick Filters
- **By Change Type**:
  - Status Changes
  - Assignment Updates
  - Provider Changes
  - Speed Modifications
  - Cost Updates

- **By Time Period**:
  - Today
  - Last 7 Days
  - Last 30 Days
  - Last Quarter
  - Custom Range

### Advanced Search
```javascript
// Search syntax examples
"site:TXH97" // All changes for specific site
"field:status" // All status changes
"user:system" // All automated changes
"value:enabled" // Changes to "enabled"
```

## Data Sources

### Primary Table
```sql
-- circuit_history table structure
CREATE TABLE circuit_history (
    id SERIAL PRIMARY KEY,
    circuit_id INTEGER REFERENCES circuits(id),
    site_name VARCHAR(100),
    site_id VARCHAR(50),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_date TIMESTAMP,
    changed_by VARCHAR(100),
    change_source VARCHAR(50)
);
```

### Data Collection
- **Nightly Script**: `nightly_circuit_history.py`
- **Runs**: 4:30 AM daily
- **Method**: Compares current state with previous snapshot
- **Excludes**: Timestamp fields, system fields

## Historical Analysis Features

### Trend Analysis
**Purpose**: Identify patterns in circuit lifecycle

#### Available Reports
1. **Status Progression**:
   - Average time in each status
   - Common status paths
   - Bottleneck identification

2. **Provider Changes**:
   - Provider switch frequency
   - Cost impact analysis
   - Service improvement tracking

3. **Assignment Patterns**:
   - Team workload over time
   - Assignment duration metrics
   - Handoff frequency

### Compliance Reporting
**Purpose**: Audit trail for compliance requirements

#### Features
- **Complete History**: No data deletion
- **Change Attribution**: Who made what change when
- **Export Formats**: PDF for auditors, CSV for analysis
- **Date Range Proof**: Cryptographic timestamps

## Interactive Features

### Timeline View
```javascript
// Interactive timeline navigation
const timeline = {
    zoom: 'month', // day/week/month/year
    filter: 'all', // all/status/assignment/cost
    highlight: [], // specific events to highlight
    playback: false // animation mode
};
```

### Comparison Tool
**Purpose**: Compare circuit state between two dates

#### Usage
1. Select "Compare" mode
2. Choose two dates
3. View side-by-side differences
4. Export comparison report

### Change Rollback (View Only)
**Purpose**: See what values would restore previous state

#### Features
- **Point-in-Time View**: Circuit state at any date
- **Rollback Preview**: What would change
- **Impact Analysis**: Affected systems
- **Documentation**: Why changes were made

## API Endpoints

### Primary APIs
- `/api/historical/changes` - Get change history
- `/api/historical/timeline` - Timeline data
- `/api/historical/analytics` - Change analytics
- `/api/historical/compare` - Compare states

### Query Parameters
```
GET /api/historical/changes?
    start_date=2025-01-01&
    end_date=2025-07-03&
    site_id=TXH97&
    field=status&
    limit=100&
    offset=0
```

## Performance Considerations

### Database Optimization
- **Indexes**: On date, site_id, field_name
- **Partitioning**: By month for large datasets
- **Archival**: Old data to compressed tables
- **Query Limits**: Maximum 10,000 rows per request

### Frontend Performance
- **Virtual Scrolling**: For large datasets
- **Lazy Loading**: Load on scroll
- **Data Aggregation**: Server-side grouping
- **Caching**: 15-minute cache for analytics

## Use Cases

### Incident Investigation
1. Search for affected circuit
2. Review changes around incident time
3. Identify what changed
4. Determine root cause

### Compliance Audit
1. Select audit period
2. Export all changes
3. Filter by compliance-relevant fields
4. Generate PDF report

### Performance Analysis
1. Select time range
2. View enablement patterns
3. Analyze bottlenecks
4. Export for presentation

### Change Validation
1. Review recent changes
2. Verify automated updates
3. Catch unexpected modifications
4. Alert on anomalies

## Data Retention

### Retention Policy
- **Full Detail**: 90 days
- **Summary Data**: 2 years
- **Compliance Data**: 7 years
- **Archived**: Compressed after 90 days

### Privacy Considerations
- **No PII**: No personal information stored
- **User Tracking**: System/username only
- **Access Logs**: Separate audit system
- **Data Masking**: Sensitive fields hidden

## Export Options

### Available Formats
1. **Excel**: Full formatting, multiple sheets
2. **CSV**: Raw data for analysis
3. **PDF**: Formatted reports with charts
4. **JSON**: For system integration

### Export Templates
- **Audit Report**: Compliance-focused format
- **Change Summary**: Executive overview
- **Technical Detail**: Full field-level changes
- **Trend Analysis**: Statistical summary

## Troubleshooting

### Common Issues

1. **Missing History**:
   - Check if nightly job ran
   - Verify circuit exists in main table
   - Look for gaps in history collection

2. **Slow Queries**:
   - Reduce date range
   - Use specific filters
   - Check index health

3. **Export Failures**:
   - Check row count limits
   - Verify disk space
   - Try smaller date range

### Validation Queries
```sql
-- Check history collection
SELECT DATE(change_date), COUNT(*)
FROM circuit_history
WHERE change_date > CURRENT_DATE - 7
GROUP BY DATE(change_date)
ORDER BY DATE(change_date) DESC;
```

---
*Last Updated: July 3, 2025*  
*Complete circuit change tracking and historical analysis*  
*Part of DSR Circuits Documentation Suite*