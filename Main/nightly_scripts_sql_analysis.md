# DSR Circuits Nightly Scripts SQL Analysis

## Overview
This document analyzes the SQL queries used by the nightly scripts in the DSR Circuits system. Each script interacts with different database tables for various data processing tasks.

## 1. nightly_dsr_pull_db_with_override.py / update_circuits_from_tracking_with_override_working.py

### Purpose
Downloads tracking data from DSR Global portal and updates the circuits table while respecting manual overrides.

### Implementation Details
- **Main Script**: `nightly_dsr_pull_db_with_override.py` - Downloads CSV from DSR Global portal
- **Update Script**: `update_circuits_from_tracking_with_override_working.py` - Processes CSV and updates database
- **Data Processing**: Converts "G" speed units to "M" (e.g., "1G" → "1000M")
- **Override Protection**: Respects manual_override flag to prevent overwriting manual changes
- **Authentication**: Uses session-based login with CSRF token extraction

### Tables Read From
- circuits (for checking manual_override flag)

### Tables Written To
- circuits
- daily_summaries

### Key SQL Queries

#### 1. Update Fingerprints
```sql
UPDATE circuits 
SET fingerprint = site_name || '|' || site_id || '|' || circuit_purpose 
WHERE fingerprint IS NULL OR fingerprint = '';
```

#### 2. Insert/Update Circuits with Manual Override Protection
```sql
INSERT INTO circuits (
    record_number, site_name, site_id, circuit_purpose, status, substatus,
    provider_name, details_service_speed, details_ordered_service_speed,
    billing_monthly_cost, ip_address_start, date_record_updated,
    milestone_service_activated, milestone_enabled, assigned_to, sctask,
    created_at, updated_at, data_source, address_1, city, state, zipcode,
    primary_contact_name, primary_contact_email, billing_install_cost,
    target_enablement_date, details_provider, details_provider_phone,
    billing_account, fingerprint, last_csv_file
) VALUES (...)
ON CONFLICT (record_number) DO UPDATE SET
    site_name = EXCLUDED.site_name,
    site_id = EXCLUDED.site_id,
    circuit_purpose = EXCLUDED.circuit_purpose,
    status = EXCLUDED.status,
    substatus = EXCLUDED.substatus,
    provider_name = EXCLUDED.provider_name,
    details_service_speed = EXCLUDED.details_service_speed,
    details_ordered_service_speed = EXCLUDED.details_ordered_service_speed,
    billing_monthly_cost = EXCLUDED.billing_monthly_cost,
    ip_address_start = EXCLUDED.ip_address_start,
    date_record_updated = EXCLUDED.date_record_updated,
    milestone_service_activated = EXCLUDED.milestone_service_activated,
    milestone_enabled = EXCLUDED.milestone_enabled,
    assigned_to = COALESCE(circuits.assigned_to, EXCLUDED.assigned_to),
    sctask = COALESCE(circuits.sctask, EXCLUDED.sctask),
    address_1 = EXCLUDED.address_1,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    zipcode = EXCLUDED.zipcode,
    primary_contact_name = EXCLUDED.primary_contact_name,
    primary_contact_email = EXCLUDED.primary_contact_email,
    billing_install_cost = EXCLUDED.billing_install_cost,
    target_enablement_date = EXCLUDED.target_enablement_date,
    details_provider = EXCLUDED.details_provider,
    details_provider_phone = EXCLUDED.details_provider_phone,
    billing_account = EXCLUDED.billing_account,
    fingerprint = EXCLUDED.fingerprint,
    last_csv_file = EXCLUDED.last_csv_file,
    data_source = EXCLUDED.data_source,
    updated_at = NOW()
WHERE circuits.manual_override IS NOT TRUE;
```

#### 3. Clear Notes for Enabled/Cancelled Circuits
```sql
UPDATE circuits 
SET notes = NULL 
WHERE (status ILIKE '%enabled%' OR status ILIKE '%cancelled%' OR status ILIKE '%canceled%') 
AND notes IS NOT NULL;
```

#### 4. Update Daily Summary
```sql
INSERT INTO daily_summaries (
    summary_date, total_circuits, enabled_count, ready_count,
    customer_action_count, construction_count, planning_count,
    csv_file_processed, processing_time_seconds, created_at
)
SELECT
    CURRENT_DATE as summary_date,
    COUNT(*) as total_circuits,
    COUNT(*) FILTER (WHERE status ILIKE '%enabled%' OR status ILIKE '%activated%') as enabled_count,
    COUNT(*) FILTER (WHERE status ILIKE '%ready%') as ready_count,
    COUNT(*) FILTER (WHERE status ILIKE '%customer action%') as customer_action_count,
    COUNT(*) FILTER (WHERE status ILIKE '%construction%') as construction_count,
    COUNT(*) FILTER (WHERE status ILIKE '%planning%') as planning_count,
    [csv_file] as csv_file_processed,
    0 as processing_time_seconds,
    NOW() as created_at
FROM circuits
ON CONFLICT (summary_date) DO UPDATE SET
    total_circuits = EXCLUDED.total_circuits,
    enabled_count = EXCLUDED.enabled_count,
    ready_count = EXCLUDED.ready_count,
    customer_action_count = EXCLUDED.customer_action_count,
    construction_count = EXCLUDED.construction_count,
    planning_count = EXCLUDED.planning_count,
    csv_file_processed = EXCLUDED.csv_file_processed,
    processing_time_seconds = EXCLUDED.processing_time_seconds,
    created_at = NOW();
```

### Data Processing Features
- **Speed Normalization**: Converts "G" units to "M" (1G → 1000M)
- **SQL Injection Protection**: Uses proper SQL escaping for all values
- **Date Parsing**: Handles multiple date formats with fallback to NULL
- **Duplicate Handling**: Tracks unique records to prevent duplicates
- **File Processing**: Sets appropriate permissions and ownership on downloaded files

## 2. nightly_meraki_db.py

### Purpose
Collects Meraki device and network data, enriches with ARIN RDAP data, and stores in database.

### Implementation Details
- **API Integration**: Uses Meraki API v1 with adaptive rate limiting
- **Provider Detection**: Combines ARIN RDAP lookups with known IP mappings
- **Provider Normalization**: Fuzzy matching and mapping to canonical provider names
- **Notes Parsing**: Extracts provider and speed information from device notes
- **Data Collection**: Inventories devices, VLANs, DHCP options, WAN ports, and firewall rules

### Tables Read From
- rdap_cache (for cached ARIN provider lookups)
- new_stores (for new store network detection)

### Tables Written To
- meraki_inventory (device and network data)
- rdap_cache (ARIN provider lookup cache)
- network_vlans (VLAN configurations)
- network_dhcp_options (DHCP options per VLAN)
- network_wan_ports (WAN port configurations)
- firewall_rules (L3 firewall rules)

### Key SQL Queries

#### 1. Insert/Update Meraki Inventory
```sql
INSERT INTO meraki_inventory (
    organization_name, network_id, network_name, device_serial,
    device_model, device_name, device_tags, device_notes,
    wan1_ip, wan1_assignment, wan1_arin_provider, wan1_provider_comparison,
    wan1_provider_label, wan1_speed_label,
    wan2_ip, wan2_assignment, wan2_arin_provider, wan2_provider_comparison,
    wan2_provider_label, wan2_speed_label,
    last_updated
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (device_serial) DO UPDATE SET
    organization_name = EXCLUDED.organization_name,
    network_id = EXCLUDED.network_id,
    network_name = EXCLUDED.network_name,
    device_model = EXCLUDED.device_model,
    device_name = EXCLUDED.device_name,
    device_tags = EXCLUDED.device_tags,
    device_notes = EXCLUDED.device_notes,
    wan1_ip = EXCLUDED.wan1_ip,
    wan1_assignment = EXCLUDED.wan1_assignment,
    wan1_arin_provider = EXCLUDED.wan1_arin_provider,
    wan1_provider_comparison = EXCLUDED.wan1_provider_comparison,
    wan1_provider_label = EXCLUDED.wan1_provider_label,
    wan1_speed_label = EXCLUDED.wan1_speed_label,
    wan2_ip = EXCLUDED.wan2_ip,
    wan2_assignment = EXCLUDED.wan2_assignment,
    wan2_arin_provider = EXCLUDED.wan2_arin_provider,
    wan2_provider_comparison = EXCLUDED.wan2_provider_comparison,
    wan2_provider_label = EXCLUDED.wan2_provider_label,
    wan2_speed_label = EXCLUDED.wan2_speed_label,
    last_updated = EXCLUDED.last_updated
```

#### 2. Update RDAP Cache
```sql
INSERT INTO rdap_cache (ip_address, provider_name)
VALUES (%s, %s)
ON CONFLICT (ip_address) DO UPDATE SET
    provider_name = EXCLUDED.provider_name,
    last_queried = NOW()
```

#### 3. Insert/Update Network VLANs
```sql
INSERT INTO network_vlans (
    network_id, network_name, vlan_id, name,
    appliance_ip, subnet, subnet_mask,
    dhcp_handling, dhcp_lease_time,
    dhcp_boot_options_enabled, dhcp_boot_next_server, dhcp_boot_filename,
    dhcp_relay_server_ips, dns_nameservers,
    reserved_ip_ranges, fixed_ip_assignments
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (network_id, vlan_id) DO UPDATE SET
    name = EXCLUDED.name,
    appliance_ip = EXCLUDED.appliance_ip,
    subnet = EXCLUDED.subnet,
    subnet_mask = EXCLUDED.subnet_mask,
    dhcp_handling = EXCLUDED.dhcp_handling,
    dhcp_lease_time = EXCLUDED.dhcp_lease_time,
    dhcp_boot_options_enabled = EXCLUDED.dhcp_boot_options_enabled,
    dhcp_boot_next_server = EXCLUDED.dhcp_boot_next_server,
    dhcp_boot_filename = EXCLUDED.dhcp_boot_filename,
    dhcp_relay_server_ips = EXCLUDED.dhcp_relay_server_ips,
    dns_nameservers = EXCLUDED.dns_nameservers,
    reserved_ip_ranges = EXCLUDED.reserved_ip_ranges,
    fixed_ip_assignments = EXCLUDED.fixed_ip_assignments,
    updated_at = CURRENT_TIMESTAMP
```

#### 4. Insert DHCP Options
```sql
INSERT INTO network_dhcp_options (
    network_id, vlan_id, code, type, value
) VALUES (%s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
```

#### 5. Insert/Update WAN Ports
```sql
INSERT INTO network_wan_ports (
    network_id, network_name, port_number, enabled, wan_enabled,
    access_policy, vlan, allowed_vlans, udld, link_negotiation,
    poe_enabled, peer_sgt_capable, flexible_stacking_enabled,
    dai_trusted, profile
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (network_id, port_number) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    wan_enabled = EXCLUDED.wan_enabled,
    access_policy = EXCLUDED.access_policy,
    vlan = EXCLUDED.vlan,
    allowed_vlans = EXCLUDED.allowed_vlans,
    udld = EXCLUDED.udld,
    link_negotiation = EXCLUDED.link_negotiation,
    poe_enabled = EXCLUDED.poe_enabled,
    peer_sgt_capable = EXCLUDED.peer_sgt_capable,
    flexible_stacking_enabled = EXCLUDED.flexible_stacking_enabled,
    dai_trusted = EXCLUDED.dai_trusted,
    profile = EXCLUDED.profile,
    updated_at = CURRENT_TIMESTAMP
```

#### 6. Firewall Rules Management
```sql
-- Clear existing rules
DELETE FROM firewall_rules WHERE network_id = %s

-- Insert new rules
INSERT INTO firewall_rules (
    network_id, network_name, rule_order, comment, policy,
    protocol, src_port, src_cidr, dest_port, dest_cidr,
    syslog_enabled, rule_type, is_template, template_source,
    created_at, updated_at, last_synced
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    NOW(), NOW(), NOW()
)
```

### Data Processing Features
- **Provider Mapping**: Canonical name mapping for ISPs (AT&T, Charter, Comcast, etc.)
- **RDAP Integration**: Real-time ARIN lookups with intelligent caching
- **Device Notes Parsing**: Extracts provider and speed from structured notes
- **Adaptive Rate Limiting**: Handles Meraki API rate limits automatically
- **Fuzzy Matching**: Compares provider names with 80% similarity threshold

## 3. nightly_enriched_db.py

### Purpose
Enriches circuit data by matching Meraki device information with DSR circuit tracking data.

### Implementation Details
- **Device Notes Processing**: Parses Meraki device notes to extract provider and speed information
- **Provider Normalization**: Maps parsed provider names to canonical names
- **Circuit Matching**: Uses fuzzy matching to correlate Meraki networks with DSR circuits
- **Change Tracking**: Maintains hash-based change detection for device notes and IP assignments

### Tables Read From
- meraki_inventory (device and network data)
- circuits (DSR circuit tracking data)
- enrichment_change_tracking (change detection)

### Tables Written To
- enriched_circuits (enriched circuit data)
- enrichment_change_tracking (change tracking)
- enrichment_change_log (change history)

### Key SQL Queries

#### 1. Insert/Update Enriched Circuits
```sql
INSERT INTO enriched_circuits (
    network_name, device_tags, 
    wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
    wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
    wan1_ip, wan2_ip, wan1_arin_org, wan2_arin_org,
    last_updated, created_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (network_name) DO UPDATE SET
    device_tags = EXCLUDED.device_tags,
    wan1_provider = EXCLUDED.wan1_provider,
    wan1_speed = EXCLUDED.wan1_speed,
    wan1_circuit_role = EXCLUDED.wan1_circuit_role,
    wan1_confirmed = EXCLUDED.wan1_confirmed,
    wan2_provider = EXCLUDED.wan2_provider,
    wan2_speed = EXCLUDED.wan2_speed,
    wan2_circuit_role = EXCLUDED.wan2_circuit_role,
    wan2_confirmed = EXCLUDED.wan2_confirmed,
    wan1_ip = EXCLUDED.wan1_ip,
    wan2_ip = EXCLUDED.wan2_ip,
    wan1_arin_org = EXCLUDED.wan1_arin_org,
    wan2_arin_org = EXCLUDED.wan2_arin_org,
    last_updated = EXCLUDED.last_updated
```

#### 2. Update Change Tracking
```sql
INSERT INTO enrichment_change_tracking (
    network_name, last_device_notes_hash, last_wan1_ip, last_wan2_ip,
    last_enrichment_run, dsr_circuits_hash
) VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (network_name) DO UPDATE SET
    last_device_notes_hash = EXCLUDED.last_device_notes_hash,
    last_wan1_ip = EXCLUDED.last_wan1_ip,
    last_wan2_ip = EXCLUDED.last_wan2_ip,
    last_enrichment_run = EXCLUDED.last_enrichment_run,
    dsr_circuits_hash = EXCLUDED.dsr_circuits_hash
```

#### 3. Log Changes
```sql
INSERT INTO enrichment_change_log (
    site_name, change_type, wan_affected, field_changed,
    old_value, new_value, change_reason, change_date
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
```

### Data Processing Features
- **Provider Mapping**: Comprehensive provider name normalization
- **Speed Parsing**: Extracts speed information from device notes
- **Change Detection**: Hash-based detection of device notes and IP changes
- **Fuzzy Matching**: Correlates Meraki networks with DSR circuits using similarity scoring

## 4. nightly_inventory_db.py

### Purpose
Collects all devices from all Meraki organizations and creates inventory summaries.

### Implementation Details
- **Multi-Organization Support**: Processes devices from all Meraki organizations
- **Device Categorization**: Groups devices by model, organization, and product type
- **EOL Integration**: Matches devices with End-of-Life data
- **Summary Generation**: Creates aggregated inventory statistics

### Tables Read From
- meraki_eol_enhanced (End-of-Life data)
- meraki_eol_pdf (PDF-sourced EOL data)

### Tables Written To
- inventory_devices (individual device records)
- inventory_summary (aggregated device counts)

### Key SQL Queries

#### 1. Insert/Update Inventory Devices
```sql
INSERT INTO inventory_devices (
    serial, model, organization, network_id, network_name,
    name, mac, lan_ip, firmware, product_type, tags, notes, details
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (serial) DO UPDATE SET
    model = EXCLUDED.model,
    organization = EXCLUDED.organization,
    network_id = EXCLUDED.network_id,
    network_name = EXCLUDED.network_name,
    name = EXCLUDED.name,
    mac = EXCLUDED.mac,
    lan_ip = EXCLUDED.lan_ip,
    firmware = EXCLUDED.firmware,
    product_type = EXCLUDED.product_type,
    tags = EXCLUDED.tags,
    notes = EXCLUDED.notes,
    details = EXCLUDED.details
```

#### 2. Update Inventory Summary
```sql
INSERT INTO inventory_summary (
    model, total_count, org_counts, 
    announcement_date, end_of_sale, end_of_support, highlight
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (model) DO UPDATE SET
    total_count = EXCLUDED.total_count,
    org_counts = EXCLUDED.org_counts,
    announcement_date = EXCLUDED.announcement_date,
    end_of_sale = EXCLUDED.end_of_sale,
    end_of_support = EXCLUDED.end_of_support,
    highlight = EXCLUDED.highlight
```

### Data Processing Features
- **Multi-Organization Processing**: Handles devices from multiple Meraki organizations
- **Device Deduplication**: Ensures unique devices by serial number
- **EOL Matching**: Correlates devices with End-of-Life information
- **Summary Aggregation**: Creates model-based inventory summaries

## 5. nightly_circuit_history.py

### Purpose
Compares daily tracking CSV files to detect changes and update circuit history.

### Implementation Details
- **File Comparison**: Compares today's vs yesterday's tracking CSV files
- **Change Detection**: Identifies modifications to circuit records
- **History Logging**: Records all changes in circuit_history table
- **Field-Level Tracking**: Tracks changes to individual circuit fields

### Tables Read From
- circuits (for circuit ID mapping)

### Tables Written To
- circuit_history (change records)

### Key SQL Queries

#### 1. Insert Circuit Changes
```sql
INSERT INTO circuit_history (
    circuit_id, change_date, change_type, field_changed,
    old_value, new_value, csv_file_source, created_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
```

#### 2. Find Circuit by Record Number
```sql
SELECT id FROM circuits WHERE record_number = %s
```

### Data Processing Features
- **Change Detection**: Compares CSV files to identify modifications
- **Field-Level Tracking**: Records specific field changes
- **Historical Audit**: Maintains complete change history for circuits
- **File-Based Processing**: Works with daily CSV downloads

## 6. nightly_enablement_db.py

### Purpose
Tracks circuit enablement events and maintains enablement statistics.

### Implementation Details
- **Status Monitoring**: Detects circuits that transition to "Enabled" status
- **Team Attribution**: Assigns enablements to team members
- **Daily Tracking**: Creates daily enablement records
- **Trend Analysis**: Maintains enablement summary statistics

### Tables Read From
- circuits (for enablement detection)
- circuit_assignments (for team attribution)

### Tables Written To
- daily_enablements (individual enablement records)
- enablement_summary (daily counts)
- enablement_trends (trend analysis)

### Key SQL Queries

#### 1. Detect New Enablements
```sql
SELECT 
    record_number, site_name, site_id, circuit_purpose, 
    provider_name, details_service_speed, billing_monthly_cost,
    assigned_to, sctask, status
FROM circuits 
WHERE status ILIKE '%enabled%' 
AND milestone_enabled IS NOT NULL
```

#### 2. Insert Daily Enablements
```sql
INSERT INTO daily_enablements (
    date, site_name, site_id, circuit_purpose, provider_name,
    service_speed, monthly_cost, previous_status, current_status,
    assigned_to, sctask, record_number, created_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT DO NOTHING
```

#### 3. Update Enablement Summary
```sql
INSERT INTO enablement_summary (summary_date, daily_count, created_at)
VALUES (CURRENT_DATE, %s, NOW())
ON CONFLICT (summary_date) DO UPDATE SET
    daily_count = EXCLUDED.daily_count,
    created_at = NOW()
```

### Data Processing Features
- **Status Transition Detection**: Identifies newly enabled circuits
- **Team Attribution**: Maps enablements to responsible team members
- **Daily Aggregation**: Creates daily enablement statistics
- **Trend Analysis**: Maintains historical enablement trends

## 7. hourly_api_performance.py

### Purpose
Collects performance metrics for all API endpoints on an hourly basis.

### Implementation Details
- **Endpoint Monitoring**: Tests 24 API endpoints across 9 categories
- **Performance Measurement**: Records response times, status codes, and data sizes
- **Comprehensive Coverage**: Monitors circuits, inventory, firewall, and other APIs
- **Automated Testing**: Runs hourly via cron job

### Tables Written To
- performance_metrics (detailed performance data)

### Key SQL Queries

#### 1. Insert Performance Metrics
```sql
INSERT INTO performance_metrics (
    endpoint_name, endpoint_method, endpoint_params,
    query_execution_time_ms, data_size_bytes, data_rows_returned,
    response_status, error_message, timestamp, module_category,
    db_query_count, cache_hit, user_agent, is_monitoring
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
```

### Monitored Endpoints
- **Circuits**: Dashboard data, search, assignments, inflight data
- **Inventory**: Device summaries, EOL data, switch visibility
- **Firewall**: Rules, templates, deployment status
- **Documentation**: Content and structure APIs
- **Reports**: Enablement reports, performance metrics
- **Network**: VLAN data, subnet analysis
- **New Stores**: Store management and tracking
- **Status**: System health and monitoring
- **Subnets**: Network analysis and grouping

### Data Processing Features
- **Multi-Category Testing**: Covers all major system components
- **Performance Tracking**: Records response times and data metrics
- **Error Detection**: Captures and logs API failures
- **Monitoring Integration**: Supports real-time system health monitoring

## Summary

The nightly script ecosystem includes 7 main components:

1. **nightly_dsr_pull_db_with_override.py**: Downloads and processes DSR Global tracking data
2. **nightly_meraki_db.py**: Collects Meraki device and network configuration data
3. **nightly_enriched_db.py**: Enriches circuit data by correlating Meraki and DSR information
4. **nightly_inventory_db.py**: Aggregates device inventory across all organizations
5. **nightly_circuit_history.py**: Tracks changes to circuit records over time
6. **nightly_enablement_db.py**: Monitors circuit enablement events and team attribution
7. **hourly_api_performance.py**: Collects performance metrics for system monitoring

These scripts work together to maintain a comprehensive, real-time view of circuit inventory, configuration, and performance across the DSR Circuits system. They handle data collection, processing, enrichment, and monitoring to support operational decision-making and system health.
