# Circuit Enablement Tracking Documentation

## Overview
The Circuit Enablement Tracking system monitors and reports on circuits that change to "Enabled" status, providing insights into network activation patterns and team performance.

## Core Business Logic

### What Counts as an Enablement?
An enablement is counted when a circuit changes TO "Enabled" status from ANY other status, including:
- Ready for Enablement → Enabled (most common)
- Installation Failed → Enabled
- Service Activated → Enabled
- Customer Action Required → Enabled
- Any other non-enabled status → Enabled

**Important**: A circuit that is already "Enabled" and remains "Enabled" is NOT counted as a new enablement.

### Data Sources
1. **Primary**: Daily CSV files from DSR Global (`/var/www/html/circuitinfo/tracking_data_YYYY-MM-DD.csv`)
2. **Comparison**: Previous day's CSV to determine status changes
3. **Unique Identifier**: Site ID (each circuit has a unique Site ID)

## Database Schema

### Tables Used

#### 1. `daily_enablements`
Stores individual circuit enablement records with full details.
```sql
- id: Serial primary key
- date: Date of enablement
- site_name: Store/site name
- circuit_purpose: Primary/Secondary
- provider_name: Circuit provider
- previous_status: Status before enablement (actual status from CSV)
- current_status: Always "Enabled" or variant
- assigned_to: Team member responsible
- sctask: ServiceNow task number
- created_at: Record creation timestamp
```

#### 2. `enablement_summary`
Stores daily count summaries for quick reporting.
```sql
- id: Serial primary key
- summary_date: Date (unique)
- daily_count: Number of enablements that day
- created_at: Record creation timestamp
```

#### 3. `ready_queue_daily`
Tracks the daily count of circuits in "Ready for Enablement" status.
```sql
- id: Serial primary key
- summary_date: Date (unique)
- ready_count: Number of circuits ready for enablement
- created_at: Record creation timestamp
```

## Processing Logic

### Nightly Processing Script (`nightly_enablement_db_v2.py`)

1. **Load Today's CSV**: Read current day's tracking data
2. **Load Yesterday's CSV**: Read previous day's data for comparison
3. **Count Ready Queue**: Count all circuits with status = "Ready for Enablement"
4. **Identify New Enablements**:
   ```python
   for each circuit in today's data:
       if status contains "enabled" (but not "ready"):
           if circuit was NOT enabled yesterday:
               count as new enablement
               record previous status
   ```
5. **Store Results**: Update database tables with counts and details

### Historical Processing
When rebuilding historical data:
1. Process CSV files in chronological order
2. Skip the first file (no previous data to compare)
3. Track each circuit's status history
4. Only count status changes TO enabled

## Report Features

### 1. Enablement Tracking Tab
- Shows daily enablement counts over time
- Line chart visualization
- Summary statistics (total, average, best day)
- Configurable date ranges

### 2. Ready Queue Tracking Tab
- Shows daily count of circuits ready for enablement
- Tracks queue size trends
- Helps identify bottlenecks

### 3. Team Attribution Tab
- Shows enablements by team member
- Performance metrics per person
- Based on "assigned_to" field from circuits

### 4. Enablement Details Tab (NEW)
- Complete list of all enabled circuits
- Shows actual previous status (not generic "Not Enabled")
- Sortable by date, site, provider, etc.
- Helps verify counts and audit changes

## API Endpoints

### `/api/daily-enablement-data`
Returns daily enablement counts and summary statistics.
- Parameters: `days`, `start_date`, `end_date`
- Default: All available data

### `/api/ready-queue-data`
Returns daily ready queue counts.
- Parameters: `days`, `start_date`, `end_date`
- Default: All available data

### `/api/enablement-details-list`
Returns detailed list of all individual enablements.
- Parameters: `days`, `start_date`, `end_date`
- Default: All available data
- Shows real previous status for each circuit

### `/api/closure-attribution-data`
Returns enablement data grouped by assigned team member.
- Parameters: `days`, `start_date`, `end_date`
- Used for team performance tracking

## Common Issues and Solutions

### Issue: Inflated counts on first day
**Cause**: No previous data to compare, all enabled circuits counted
**Solution**: Skip first CSV file in processing

### Issue: Duplicate circuits
**Cause**: Multiple records with same Site ID
**Solution**: Use Site ID as unique identifier, last record wins

### Issue: Missing July data
**Cause**: Nightly script may have failed
**Solution**: Run `nightly_enablement_db_v2.py` manually

### Issue: Wrong previous status
**Cause**: Old logic used generic "Not Enabled"
**Solution**: Track actual status history from CSVs

## Example Enablement Scenarios

### Scenario 1: Normal Enablement
- June 30: Circuit status = "Ready for Enablement"
- July 1: Circuit status = "Enabled"
- Result: Counts as 1 enablement on July 1

### Scenario 2: Failed Installation Recovery
- June 30: Circuit status = "Installation Failed"
- July 1: Circuit status = "Enabled"
- Result: Counts as 1 enablement on July 1

### Scenario 3: Already Enabled
- June 30: Circuit status = "Enabled"
- July 1: Circuit status = "Enabled"
- Result: Does NOT count as enablement

### Scenario 4: New Circuit
- June 30: Circuit doesn't exist
- July 1: Circuit appears with status = "Enabled"
- Result: Counts as 1 enablement on July 1

## Maintenance Tasks

### Daily (Automated via Cron)
- Run `nightly_enablement_db_v2.py` to process new CSV data
- Update ready queue counts
- Track new enablements

### Weekly (Manual Check)
- Verify enablement counts match expectations
- Review team attribution data
- Check for any processing errors

### Monthly
- Audit a sample of enablements
- Review trends and patterns
- Update documentation as needed

## Performance Considerations

- Processing ~4,000 circuits per CSV file
- Comparison requires previous day's data in memory
- Database indexes on date fields for fast queries
- Historical rebuild takes ~2-3 minutes for 90 days

## Future Enhancements

1. **Automated Alerts**: Notify when enablement rate drops
2. **SLA Tracking**: Time from "Ready" to "Enabled"
3. **Provider Analysis**: Enablement rates by provider
4. **Predictive Analytics**: Forecast enablement trends

---

**Last Updated**: July 2, 2025
**Author**: System Documentation
**Version**: 2.0