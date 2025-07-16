# Flask Routes SQL Analysis - DSR Circuits Application

This document analyzes all SQL queries used by the Flask web routes in the DSR Circuits application. It's organized by module/blueprint and includes tables accessed, query types, and specific SQL operations.

## 1. Main Application (dsrcircuits.py)

### Health Check Route
**Route:** `/api/health`
- **Tables Read:** None (connection test only)
- **SQL Query:** `SELECT 1` (simple connection test)
- **Type:** Raw SQL via SQLAlchemy

### Quick Stats Route
**Route:** `/api/stats/quick`
- **Tables Read:** circuits, circuit_history, circuit_assignments, daily_summaries
- **Operations:**
  - `Circuit.query.count()` - Count all circuits
  - `Circuit.get_status_counts()` - Group by status with counts
  - `Circuit.get_recent_enablements(days=7)` - Filter by date and status
  - `CircuitHistory.query.count()` - Count all history records
  - `CircuitAssignment.query.count()` - Count all assignments
  - `DailySummary.query.order_by(DailySummary.summary_date.desc()).first()` - Get latest summary

### Circuit Search Route
**Route:** `/api/circuits/search`
- **Tables Read:** circuits
- **Operations:**
  - Dynamic query building with filters:
    - `Circuit.site_name.ilike(f'%{site_name}%')`
    - `Circuit.status.ilike(f'%{status}%')`
    - `Circuit.provider_name.ilike(f'%{provider}%')`
  - `query.limit(limit).all()` - Limit results
- **Features:** Redis caching of results

### Firewall Management Routes

#### Get Networks
**Route:** `/api/networks`
- **Tables Read:** meraki_inventory, firewall_rules
- **SQL Queries:**
```sql
-- Get networks with devices
SELECT DISTINCT network_name, network_id, 
       COUNT(*) as device_count
FROM meraki_inventory 
WHERE network_name IS NOT NULL 
GROUP BY network_name, network_id
ORDER BY network_name

-- Get networks with firewall rules but no devices
SELECT DISTINCT network_name, network_id,
       COUNT(*) as rule_count
FROM firewall_rules 
WHERE network_name NOT IN (
    SELECT DISTINCT network_name 
    FROM meraki_inventory 
    WHERE network_name IS NOT NULL
)
GROUP BY network_name, network_id
ORDER BY network_name
```

#### Get Firewall Rules
**Route:** `/api/firewall/rules/<network_name>`
- **Tables Read:** firewall_rules
- **SQL Query:**
```sql
SELECT id, rule_order, comment, policy, protocol,
       src_port, src_cidr, dest_port, dest_cidr,
       syslog_enabled, rule_type, is_template,
       created_at, updated_at
FROM firewall_rules 
WHERE network_name = :network_name
ORDER BY rule_order
```

#### Save Firewall Rule
**Route:** `/api/firewall/rules` (POST)
- **Tables Write:** firewall_rules
- **Operations:**
  - UPDATE existing rule
  - INSERT new rule with auto-increment rule_order
```sql
-- Get next rule order
SELECT COALESCE(MAX(rule_order), 0) + 1 as next_order 
FROM firewall_rules 
WHERE network_name = :network_name

-- Insert new rule
INSERT INTO firewall_rules (
    network_id, network_name, rule_order, comment, policy,
    protocol, src_port, src_cidr, dest_port, dest_cidr,
    syslog_enabled, rule_type, is_template, template_source,
    created_at, updated_at
) VALUES (...)
```

#### Delete Firewall Rule
**Route:** `/api/firewall/rules/<int:rule_id>` (DELETE)
- **Tables Write:** firewall_rules
- **SQL Query:** `DELETE FROM firewall_rules WHERE id = :id`

#### Template Management Routes
**Routes:** Various `/api/firewall/template/...`
- **Tables Read/Write:** firewall_rules, firewall_rule_revisions
- **Operations:** Template CRUD with revision tracking

#### Deploy Rules Route
**Route:** `/api/firewall/deploy` (POST)
- **Tables Read:** firewall_rules
- **Tables Write:** firewall_rules, firewall_deployment_log
- **Operations:** Copy template rules to target networks with deployment logging

## 2. New Stores Module (new_stores.py)

### Get New Stores
**Route:** `/api/new-stores` (GET)
- **Tables Read:** new_stores
- **Query:** `NewStore.query.filter_by(is_active=True).order_by(NewStore.site_name).all()`

### Add New Stores
**Route:** `/api/new-stores` (POST)
- **Tables Write:** new_stores
- **Operations:**
  - Check existing: `NewStore.query.filter_by(site_name=site_name).first()`
  - Insert new or reactivate existing stores

### Update New Store
**Route:** `/api/new-stores/<int:store_id>` (PUT)
- **Tables Write:** new_stores
- **Operations:** Update store details including TOD dates

### Get New Store Circuits with TOD
**Route:** `/api/new-store-circuits-with-tod`
- **Tables Read:** new_stores, circuits
- **Operations:**
  - Get all active new stores
  - `Circuit.query.filter(Circuit.site_name.in_(new_store_names)).all()`
  - Join TOD data with circuit data

### Excel Upload
**Route:** `/api/new-stores/excel-upload` (POST)
- **Tables Write:** new_stores
- **Operations:** Bulk insert/update from Excel data

### Create New Circuit
**Route:** `/api/new-circuits` (POST)
- **Tables Write:** circuits
- **Operations:**
  - Check existing circuit
  - Generate unique record number
  - Insert with manual_override flag

### Update Circuit Notes
**Route:** `/api/circuits/update-notes` (POST)
- **Tables Write:** circuits
- **Query:** Update notes field for specific circuit

## 3. EOL Routes Module (eol_routes.py)

### EOL Summary
**Route:** `/api/eol/summary`
- **Tables Read:** meraki_eol, inventory_summary
- **SQL Query:**
```sql
WITH eol_latest AS (
    SELECT DISTINCT ON (model) 
        model, model_variants, announcement_date,
        end_of_sale_date, end_of_support_date,
        pdf_url, pdf_filename,
        CASE 
            WHEN pdf_source AND csv_source THEN 'both'
            WHEN pdf_source THEN 'pdf'
            WHEN csv_source THEN 'csv'
            ELSE 'none'
        END as eol_source,
        updated_at
    FROM meraki_eol
    ORDER BY model, updated_at DESC
),
inventory_counts AS (
    SELECT model, total_count as inventory_count
    FROM inventory_summary
)
SELECT e.*, COALESCE(i.inventory_count, 0) as inventory_count
FROM eol_latest e
LEFT JOIN inventory_counts i ON e.model = i.model
ORDER BY [priority logic]
```

### EOL Model Detail
**Route:** `/api/eol/model/<model>`
- **Tables Read:** meraki_eol, inventory_devices
- **Operations:** Get EOL records and inventory info for specific model

### Affected Devices
**Route:** `/api/eol/affected-devices`
- **Tables Read:** meraki_eol, inventory_devices
- **SQL Query:**
```sql
WITH eol_models AS (
    SELECT DISTINCT model, end_of_sale_date, end_of_support_date
    FROM meraki_eol
    WHERE end_of_sale_date <= CURRENT_DATE
)
SELECT id.*, em.*, 
       CASE 
           WHEN em.end_of_support_date <= CURRENT_DATE THEN 'eol'
           ELSE 'eos'
       END as status
FROM inventory_devices id
INNER JOIN eol_models em ON id.model = em.model
ORDER BY em.end_of_support_date, id.organization, id.network_name
```

## 4. Reports Module (reports.py)

### Daily Enablement Data
**Route:** `/api/daily-enablement-data`
- **Tables Read:** enablement_summary
- **SQL Queries with date series generation:**
```sql
-- Last N days
WITH date_series AS (
    SELECT generate_series(
        CURRENT_DATE - INTERVAL %s,
        CURRENT_DATE,
        '1 day'::interval
    )::date AS date
)
SELECT ds.date, COALESCE(es.daily_count, 0) as count
FROM date_series ds
LEFT JOIN enablement_summary es ON ds.date = es.summary_date
ORDER BY ds.date ASC

-- Date range
WITH date_series AS (
    SELECT generate_series(
        %s::date, %s::date,
        '1 day'::interval
    )::date AS date
)
SELECT ds.date, COALESCE(es.daily_count, 0) as count
FROM date_series ds
LEFT JOIN enablement_summary es ON ds.date = es.summary_date
ORDER BY ds.date ASC
```

### Ready Queue Data
**Route:** `/api/ready-queue-data`
- **Tables Read:** ready_queue_daily, enablement_summary
- **SQL Query:**
```sql
SELECT 
    rq.summary_date,
    rq.ready_count,
    COALESCE(es.daily_count, 0) as closed_from_ready
FROM ready_queue_daily rq
LEFT JOIN enablement_summary es ON rq.summary_date = es.summary_date
ORDER BY rq.summary_date ASC
```

### Enablement Details List
**Route:** `/api/enablement-details-list`
- **Tables Read:** daily_enablements
- **SQL Queries:**
```sql
-- Main data query
SELECT 
    date, site_id, site_name, circuit_purpose,
    provider_name, previous_status, current_status,
    assigned_to, sctask, created_at
FROM daily_enablements
WHERE [date filters]
ORDER BY date DESC, site_name

-- Daily counts query
SELECT date, COUNT(*) as count
FROM daily_enablements
WHERE [date filters]
GROUP BY date
ORDER BY date DESC
```

### Closure Attribution Data
**Route:** `/api/closure-attribution-data`
- **Tables Read:** daily_enablements, circuit_assignments, enablement_summary
- **Complex SQL with date series and LEFT JOIN for attribution:
```sql
SELECT 
    de.date as enablement_date,
    de.site_name,
    de.circuit_purpose,
    de.previous_status,
    de.current_status,
    CASE 
        WHEN ca.assigned_to IS NOT NULL AND ca.assigned_to <> '' THEN ca.assigned_to
        WHEN de.assigned_to IS NOT NULL AND de.assigned_to <> '' THEN de.assigned_to
        ELSE 'Unknown'
    END as assigned_person,
    COALESCE(ca.sctask, de.sctask, '') as sctask_number
FROM daily_enablements de
LEFT JOIN circuit_assignments ca ON de.site_name = ca.site_name AND ca.status = 'active' 
WHERE [date filters]
ORDER BY de.date ASC
```

## 5. Inventory Module (inventory.py)

### Inventory Summary
**Route:** `/api/inventory-summary`
- **Tables Read:** inventory_summary
- **SQL Query:**
```sql
SELECT model, total_count, org_counts, announcement_date, 
       end_of_sale, end_of_support, highlight
FROM inventory_summary
ORDER BY model
```

### Inventory Details
**Route:** `/api/inventory-details`
- **Tables Read:** inventory_devices
- **SQL Query with JSON validation and tag filtering:**
```sql
SELECT serial, model, organization, 
       COALESCE(network_id, '') as network_id, 
       COALESCE(network_name, '') as network_name,
       COALESCE(name, '') as name, 
       COALESCE(mac, '') as mac, 
       COALESCE(lan_ip, '') as lan_ip, 
       COALESCE(firmware, '') as firmware, 
       COALESCE(product_type, '') as product_type,
       CASE 
         WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'
         ELSE tags 
       END as tags,
       COALESCE(notes, '') as notes,
       CASE 
         WHEN details IS NULL OR details = '' OR details = 'null' THEN '{}'
         ELSE details 
       END as details
FROM inventory_devices
WHERE 1=1
AND NOT EXISTS (
    SELECT 1 FROM jsonb_array_elements_text(
        CASE 
            WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
            ELSE tags::jsonb 
        END
    ) tag
    WHERE LOWER(tag) LIKE '%hub%' 
       OR LOWER(tag) LIKE '%lab%' 
       OR LOWER(tag) LIKE '%voice%'
)
[Additional filters]
ORDER BY organization, model
```

## 6. Switch Visibility Module (switch_visibility.py)

### Get Switch Port Clients
**Route:** `/api/switch-port-clients`
- **Tables Read:** switch_port_clients
- **Operations:**
  - Dynamic query building with filters:
    - Store filter: `SwitchPortClient.store_name == store_filter` or `IN` for multiple
    - Switch filter: `SwitchPortClient.switch_serial == switch_filter`
    - Search filter with OR across multiple fields:
```python
db.or_(
    SwitchPortClient.hostname.ilike(search_pattern),
    SwitchPortClient.ip_address.ilike(search_pattern),
    SwitchPortClient.mac_address.ilike(search_pattern),
    SwitchPortClient.switch_name.ilike(search_pattern),
    SwitchPortClient.manufacturer.ilike(search_pattern)
)
```
  - Ordering: `ORDER BY store_name, switch_name, port_id`
  - Pagination: `query.paginate(page=page, per_page=per_page)`
  - Distinct queries for filter dropdowns
- **Features:** Redis caching for 5 minutes

### Refresh Switch Data
**Route:** `/api/switch-port-clients/refresh-switch/<serial>` (POST)
- **Tables Write:** switch_port_clients
- **Operations:**
  - Check existing: `SwitchPortClient.query.filter_by(switch_serial, port_id, mac_address).first()`
  - Update existing records or insert new ones
  - Cache invalidation for switch-specific keys
- **External API:** Meraki API calls for live data

### Refresh Store Data
**Route:** `/api/switch-port-clients/refresh-store/<store_name>` (POST)
- **Tables Read/Write:** switch_port_clients
- **Operations:**
  - Get switches from database:
```python
db.session.query(SwitchPortClient.switch_serial, SwitchPortClient.switch_name).filter(
    SwitchPortClient.store_name == store_name
).distinct().all()
```
  - Sequential processing of switches
  - Cache invalidation for store-specific keys

### Export Switch Port Clients
**Route:** `/api/switch-port-clients/export`
- **Tables Read:** switch_port_clients
- **Operations:** Same filtering as main GET endpoint
- **Output:** Excel file generation with pandas

## 7. DSR Circuits Blueprint (dsrcircuits_blueprint.py)

### Main DSR Circuits Page
**Route:** `/dsrcircuits`
- **Tables Read:** v_circuit_summary (optimized view)
- **SQL Query:**
```sql
SELECT 
    network_name,
    device_tags,
    wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
    wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
    wan1_cost, wan2_cost
FROM v_circuit_summary
ORDER BY network_name
```
- **Features:** Redis caching for 5 minutes, fallback to legacy query

### Circuits Data API
**Route:** `/api/circuits/data`
- **Tables Read:** v_circuit_summary
- **Operations:**
  - Paginated queries with search filtering
  - Count query for pagination
  - Search across multiple fields with ILIKE
- **Features:** Redis caching per page

### DSR All Circuits Page
**Route:** `/dsrallcircuits`
- **Tables Read:** circuits
- **Query:** `Circuit.query.filter(Circuit.status == 'Enabled').all()`
- **Purpose:** Display all enabled circuits

### Confirm Site Popup
**Route:** `/confirm/<site_name>` (POST)
- **Tables Read:** circuits, enriched_circuits, meraki_inventory
- **Operations:**
  - Get circuits for site: `Circuit.query.filter_by(site_name=site_name).all()`
  - Get enriched data: `EnrichedCircuit.query.filter_by(network_name=site_name).first()`
  - Get Meraki data: Case-insensitive search with `func.lower()`

### Submit Confirmation
**Route:** `/confirm/<site_name>/submit` (POST)
- **Tables Write:** enriched_circuits, meraki_inventory
- **Operations:**
  - Update or create enriched circuit record
  - Update Meraki device notes after push
  - Set confirmation flags
- **External API:** Push to Meraki API

### Push to Meraki
**Route:** `/push_to_meraki` (POST)
- **Tables Read/Write:** enriched_circuits, meraki_inventory
- **Operations:** Batch processing of confirmed circuits
- **External API:** Meraki configuration API

## 8. Other Notable Routes

### System Health Module (system_health.py)
- Various monitoring endpoints using raw SQL queries
- Performance metrics collection
- Database connection pool monitoring

### Performance Module (performance.py)
- **Tables Read/Write:** performance_metrics
- Tracks API endpoint response times
- Aggregates performance statistics

### Historical Module (historical.py)
- **Tables Read:** circuit_history
- Time-series analysis of circuit changes
- Historical trend analysis

### Status Module (status.py)
- **Tables Read:** circuits
- Circuit status distribution and reporting

### Tags Module (tags.py)
- **Tables Read/Write:** meraki_inventory
- Device tag management and bulk operations

## Summary of Database Access Patterns

### Read-Heavy Tables:
1. **circuits** - Main circuit data, frequently queried with filters
2. **inventory_devices** - Device inventory, large table with JSON fields
3. **enablement_summary** - Pre-aggregated daily enablement counts
4. **firewall_rules** - Network firewall configurations

### Write-Heavy Tables:
1. **new_stores** - Frequent updates for TOD management
2. **firewall_rules** - CRUD operations for rule management
3. **circuit_assignments** - Team assignment updates

### Query Optimization Techniques Used:
1. **CTEs (Common Table Expressions)** - For complex date series generation
2. **Window Functions** - DISTINCT ON for latest records
3. **JSON Operations** - jsonb_array_elements_text for tag filtering
4. **Indexed Queries** - Most queries use indexed columns
5. **COALESCE** - For null handling and default values
6. **Prepared Statements** - Parameter binding for security

### Caching Strategy:
- Redis caching implemented for:
  - Circuit search results (10 minutes)
  - Full inventory datasets (10 minutes)
  - Performance-critical endpoints

### Performance Considerations:
1. **Date Series Generation** - Used for filling gaps in time-series data
2. **LEFT JOINs** - Preserve all records even without matches
3. **Batch Operations** - Excel uploads use bulk insert/update
4. **Query Result Limits** - Search queries limited to prevent overload
5. **Optimized Views** - v_circuit_summary for fast main page loads
6. **Connection Pooling** - SQLAlchemy manages database connections

## Database Tables Summary

### Main Application Tables:
1. **circuits** - Core circuit tracking data (7,000+ records)
2. **circuit_history** - Change tracking and audit trail
3. **circuit_assignments** - Team member assignments
4. **new_stores** - New store construction tracking
5. **enriched_circuits** - Meraki integration data
6. **meraki_inventory** - Device inventory from Meraki API
7. **inventory_devices** - Detailed device information
8. **inventory_summary** - Aggregated device model counts

### Reporting Tables:
1. **daily_enablements** - Circuit enablement records
2. **enablement_summary** - Aggregated daily counts
3. **ready_queue_daily** - Queue size tracking
4. **daily_summaries** - Overall daily statistics

### Monitoring Tables:
1. **performance_metrics** - API endpoint performance
2. **switch_port_clients** - Network device connections
3. **meraki_eol** - End-of-life tracking

### Configuration Tables:
1. **firewall_rules** - Network firewall configurations
2. **firewall_rule_revisions** - Change history
3. **firewall_deployment_log** - Deployment tracking
4. **provider_mappings** - ISP name normalization

## Key Query Patterns

### 1. Dynamic Filtering
Most routes build dynamic WHERE clauses based on user input:
```python
if site_name:
    query = query.filter(Circuit.site_name.ilike(f'%{site_name}%'))
```

### 2. JSON Field Handling
PostgreSQL JSONB operations for complex data:
```sql
jsonb_array_elements_text(tags::jsonb)
```

### 3. Date Series Generation
Fill missing dates in time series data:
```sql
WITH date_series AS (
    SELECT generate_series(start_date, end_date, '1 day'::interval)::date AS date
)
```

### 4. Case-Insensitive Searches
Using ILIKE and func.lower() for flexible matching:
```python
Circuit.site_name.ilike(f'%{search}%')
func.lower(MerakiInventory.network_name) == func.lower(site_name)
```

### 5. Aggregate Queries
GROUP BY for summaries and counts:
```sql
SELECT status, COUNT(*) FROM circuits GROUP BY status
```

## Performance Optimizations

### 1. Caching Strategy
- **Redis**: 5-10 minute TTL for frequently accessed data
- **Key Patterns**: Include filters in cache keys
- **Invalidation**: Clear related keys on updates

### 2. Query Optimization
- **Indexes**: On frequently filtered columns (site_name, status, dates)
- **Views**: Pre-joined v_circuit_summary for main page
- **Limits**: Pagination and result limits prevent overload

### 3. Batch Processing
- **Bulk Operations**: Multiple records in single transaction
- **Sequential Processing**: For API rate limits (Meraki)
- **Connection Pooling**: Reuse database connections

### 4. Progressive Loading
- **Pagination**: Large datasets loaded in chunks
- **Lazy Loading**: Related data fetched only when needed
- **API Endpoints**: Separate endpoints for different data needs

## Security Considerations

### 1. SQL Injection Prevention
- **Parameterized Queries**: All user input properly escaped
- **SQLAlchemy ORM**: Automatic parameter binding
- **Text Queries**: Using `:parameter` syntax

### 2. Access Control
- **Read-Only Views**: Limited access to sensitive data
- **Manual Override Flags**: Prevent automated overwrites
- **Audit Trails**: History tables track all changes

### 3. Data Validation
- **Input Sanitization**: Clean user input before database operations
- **Type Checking**: Ensure proper data types
- **Constraint Validation**: Database-level constraints enforced