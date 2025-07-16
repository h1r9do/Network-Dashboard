# Meraki EOL (End-of-Life) Tracking System

## Overview

The Enhanced EOL Tracking System provides comprehensive tracking of Meraki device end-of-life announcements. It automatically:

1. Monitors the Meraki EOL documentation page for changes
2. Downloads and parses EOL announcement PDFs
3. Extracts model numbers and EOL dates from multiple sources
4. Maintains a database of all EOL information
5. Integrates with the inventory system for enhanced reporting

## Components

### 1. **meraki_eol_tracker.py**
- Main EOL tracking script
- Checks the Meraki EOL page for updates
- Downloads and parses PDFs
- Processes the comprehensive EOL CSV
- Updates the `meraki_eol` database table

### 2. **nightly_inventory_db_enhanced.py**
- Enhanced inventory collection script
- Integrates EOL data from the database
- Provides better EOL matching (exact and pattern-based)
- Tracks EOL data source and confidence levels

### 3. **eol_routes.py**
- Flask blueprint for the EOL dashboard
- Provides web interface for viewing EOL data
- API endpoints for EOL queries

### 4. **eol_dashboard.html**
- Interactive web dashboard
- Displays EOL models with status badges
- Filtering by status (Active, EOS, EOL, Upcoming)
- Shows inventory counts for affected devices

## Database Schema

### meraki_eol Table
```sql
CREATE TABLE meraki_eol (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    model_variants TEXT,  -- JSON array of all model variants
    announcement_date DATE,
    end_of_sale_date DATE,
    end_of_support_date DATE,
    pdf_url VARCHAR(500),
    pdf_filename VARCHAR(200),
    pdf_hash VARCHAR(64),
    csv_source BOOLEAN DEFAULT FALSE,
    pdf_source BOOLEAN DEFAULT FALSE,
    raw_text TEXT,  -- Raw text extracted from PDF
    parsed_data JSONB,  -- Additional parsed data
    last_checked TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Enhanced inventory_summary Table
```sql
-- Additional columns added to existing table:
eol_source VARCHAR(20),  -- 'pdf', 'csv', 'both', 'none'
eol_confidence VARCHAR(20),  -- 'exact', 'pattern', 'none'
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements_eol.txt
   ```

2. **Test the installation:**
   ```bash
   python3 /usr/local/bin/Main/test_eol_tracker.py
   ```

3. **Run initial EOL data collection:**
   ```bash
   python3 /usr/local/bin/Main/meraki_eol_tracker.py
   ```

4. **Run enhanced inventory collection:**
   ```bash
   python3 /usr/local/bin/Main/nightly_inventory_db_enhanced.py
   ```

## Usage

### Manual Execution

```bash
# Run EOL tracker
python3 /usr/local/bin/Main/meraki_eol_tracker.py

# Run enhanced inventory with EOL data
python3 /usr/local/bin/Main/nightly_inventory_db_enhanced.py

# Run combined script
python3 /usr/local/bin/Main/nightly_eol_and_inventory.py
```

### Automated Execution (Cron)

Add to crontab:
```bash
# Daily EOL check at 1 AM
0 1 * * * /usr/bin/python3 /usr/local/bin/Main/meraki_eol_tracker.py

# Daily inventory update at 2 AM
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_db_enhanced.py
```

### Web Interface

Access the EOL dashboard at:
```
http://your-server:8080/eol
```

## Features

### EOL Data Sources
- **PDF Documents**: Automatically downloads and parses EOL announcement PDFs
- **CSV Summary**: Processes Meraki's comprehensive EOL CSV file
- **HTML Tables**: Parses tables from the EOL documentation page

### Model Matching
- **Exact Match**: Direct model number matching
- **Pattern Match**: Handles model variants (e.g., MS250-24 matches MS250 EOL data)
- **Variant Tracking**: Stores all model variants mentioned in PDFs

### Status Tracking
- **Active**: Models not yet end-of-sale
- **End of Sale (EOS)**: No longer available for purchase
- **End of Support (EOL)**: No longer supported
- **Upcoming**: EOS within 90 days

### Integration Features
- **Inventory Counts**: Shows how many devices of each model are in inventory
- **Organization Breakdown**: Tracks EOL devices by organization
- **PDF Links**: Direct links to official EOL announcements

## API Endpoints

### GET /api/eol/summary
Returns all EOL models with summary statistics

### GET /api/eol/model/<model>
Detailed EOL information for a specific model

### GET /api/eol/affected-devices
List of all devices affected by EOL/EOS

### POST /api/eol/refresh
Manually trigger EOL data refresh (admin only)

## Monitoring

### Log Files
- `/var/log/meraki-eol-tracker.log` - EOL tracker logs
- `/var/log/nightly-inventory-db-enhanced.log` - Enhanced inventory logs
- `/var/log/nightly-eol-and-inventory.log` - Combined script logs

### Health Checks
The EOL tracker maintains state in the `eol_tracker_state` table to track:
- Last page hash (for change detection)
- Last CSV hash
- PDF inventory
- Last check time

## Troubleshooting

### Common Issues

1. **PDF parsing errors**
   - Some PDFs may have unusual formatting
   - Check raw_text field in database for manual review

2. **Model matching issues**
   - Review model_variants field for all variations
   - Check pattern matching logic for complex models

3. **Memory issues with large PDFs**
   - The script limits text storage to 10KB per PDF
   - Consider increasing if needed

### Debug Mode

Run with verbose logging:
```bash
python3 -u /usr/local/bin/Main/meraki_eol_tracker.py 2>&1 | tee debug.log
```

## Future Enhancements

1. **Email Notifications**: Alert when new EOL announcements are found
2. **Slack Integration**: Post EOL updates to Slack channels
3. **Report Generation**: Automated EOL impact reports
4. **API Rate Limiting**: Implement rate limiting for API endpoints
5. **Historical Tracking**: Track EOL announcement patterns over time

## Support

For issues or questions:
1. Check the log files for errors
2. Run the test script to verify setup
3. Review the database tables for data integrity
4. Check the Meraki EOL page for format changes