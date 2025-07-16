# DSR Circuits Database Schema Documentation

**Database:** dsrcircuits  
**Total Tables:** 65  
**Last Updated:** July 8, 2025

## Table of Contents

1. [Core Circuit Management Tables](#core-circuit-management-tables) (12 tables - documented in CLAUDE.md)
2. [EOL (End of Life) Tables](#eol-end-of-life-tables) (6 tables)
3. [Inventory Management Tables](#inventory-management-tables) (15 tables)
4. [Network and Device Tables](#network-and-device-tables) (11 tables)
5. [Performance and Monitoring Tables](#performance-and-monitoring-tables) (2 tables)
6. [Enablement Tracking Tables](#enablement-tracking-tables) (4 tables)
7. [SNMP Related Tables](#snmp-related-tables) (2 tables)
8. [Backup Tables](#backup-tables) (2 tables)
9. [Other Tables](#other-tables) (11 tables)

---

## Core Circuit Management Tables

These 12 tables form the core of the DSR Circuits system and are documented in CLAUDE.md:

1. **circuits** (2,697 rows) - Main circuit tracking table
2. **circuit_history** (692 rows) - Historical changes to circuits
3. **circuit_assignments** (8 rows) - Manual circuit assignments to users
4. **new_stores** (133 rows) - Target Opening Date (TOD) store management
5. **meraki_inventory** (1,330 rows) - Meraki device inventory
6. **firewall_rules** (75,355 rows) - Firewall rule configurations
7. **firewall_deployment_log** (0 rows) - Log of firewall deployments
8. **provider_mappings** (10 rows) - ISP/carrier mapping table
9. **daily_summaries** (865 rows) - Daily operational summaries
10. **rdap_cache** (2,378 rows) - RDAP API cache for ISP lookups
11. **enriched_circuits** (1,323 rows) - Circuits with enriched data
12. **enrichment_change_tracking** (1,322 rows) - Track changes to enriched data

---

## EOL (End of Life) Tables

### 1. corporate_eol (32 rows)
Tracks corporate-level EOL information for hardware

### 2. eol_tracker_state (4 rows)
Maintains state for EOL tracking processes
- `last_page_hash` - Hash of last processed page
- `last_csv_hash` - Hash of last processed CSV
- `last_check_time` - Timestamp of last check
- `pdf_inventory` - JSONB storage of PDF inventory

### 3. meraki_eol (0 rows)
Meraki-specific EOL tracking (currently empty)

### 4. meraki_eol_enhanced (424 rows)
Enhanced Meraki EOL data with additional fields

### 5. meraki_eol_pdf (650 rows)
EOL data extracted from PDF documents

### 6. netdisco_eol_mapping (102 rows)
Maps Netdisco devices to EOL information

---

## Inventory Management Tables

### 1. collected_chassis (1,312 rows)
Physical chassis information from network devices

### 2. collected_fans (0 rows)
Fan module inventory (currently empty)

### 3. collected_fex_modules (12 rows)
Fabric Extender modules for Nexus switches

### 4. collected_modules (1,501 rows)
Network device modules and line cards

### 5. collected_power_supplies (0 rows)
Power supply inventory (currently empty)

### 6. collected_raw_inventory (3 rows)
Raw inventory data before processing

### 7. collected_sfps (1,643 rows)
SFP (Small Form-factor Pluggable) transceiver inventory

### 8. comprehensive_device_inventory (169 rows)
Complete device inventory with detailed JSONB fields:
- `system_info` - System-level information
- `physical_components` - Hardware components
- `interfaces` - Network interfaces
- `environmental_data` - Temperature, fan status
- `cisco_specific` - Cisco-specific data
- `stack_info` - Stack configuration

### 9. datacenter_inventory (225 rows)
Datacenter-specific device inventory

### 10. device_inventory (0 rows)
General device inventory (currently empty)

### 11. inventory_collection_history (2 rows)
History of inventory collection runs

### 12. inventory_collections (9 rows)
Inventory collection metadata

### 13. inventory_devices (13,092 rows)
Comprehensive device inventory listing

### 14. inventory_summary (65 rows)
Summary statistics of inventory

### 15. netdisco_inventory_summary (29 rows)
Summary of Netdisco-discovered devices

---

## Network and Device Tables

### 1. device_access (168 rows)
Device access credentials and methods

### 2. device_components (22,973 rows)
Individual components within devices

### 3. device_notes_backup (1,047 rows)
Backup of device notes and comments

### 4. device_snmp_credentials (68 rows)
SNMP credentials for device access

### 5. enriched_networks (1,239 rows)
Network information with enriched data

### 6. network_devices (84 rows)
Network device catalog

### 7. network_dhcp_options (0 rows)
DHCP configuration options (currently empty)

### 8. network_vlans (4,863 rows)
VLAN configurations across networks

### 9. network_wan_ports (0 rows)
WAN port configurations (currently empty)

### 10. port_forwarding_rules (0 rows)
Port forwarding configurations (currently empty)

### 11. switch_port_clients (74,350 rows)
Client devices connected to switch ports

---

## Performance and Monitoring Tables

### 1. api_performance (0 rows)
API endpoint performance metrics:
- `endpoint` - API endpoint path
- `response_time` - Response time in ms
- `status_code` - HTTP status code
- `timestamp` - When measured

### 2. performance_metrics (2,328 rows)
Detailed performance tracking:
- `endpoint_name` - Name of endpoint
- `query_execution_time_ms` - Database query time
- `data_size_bytes` - Response size
- `data_rows_returned` - Number of rows
- `module_category` - Module grouping

---

## Enablement Tracking Tables

### 1. circuit_enablements (723 rows)
Tracks circuit enablement events:
- `site_name` - Store location
- `circuit_purpose` - Primary/Secondary
- `enablement_date` - When enabled
- `provider_name` - ISP/Carrier

### 2. daily_enablements (41 rows)
Daily enablement records with attribution:
- `date` - Enablement date
- `assigned_to` - Person responsible
- `sctask` - ServiceNow task
- `site_id` - Circuit identifier

### 3. enablement_summary (53 rows)
Aggregated enablement statistics by date

### 4. enablement_trends (14 rows)
Trend analysis for enablements

---

## SNMP Related Tables

### 1. snmp_credentials (6 rows)
SNMP community strings and credentials

### 2. snmp_test_results (0 rows)
Results from SNMP connectivity tests

---

## Backup Tables

### 1. enriched_circuits_backup_20250627 (1,294 rows)
Backup from June 27, 2025

### 2. enriched_circuits_backup_20250627_v2 (1,384 rows)
Second backup version from June 27, 2025

---

## Other Tables

### 1. cellular_carrier_detection (0 rows)
Detection of cellular carriers (currently empty)

### 2. chassis_blades (149 rows)
Blade server information for chassis

### 3. firewall_rule_revisions (0 rows)
Revision history for firewall rules

### 4. hardware_components (2 rows)
Hardware component catalog

### 5. l7_firewall_rules (0 rows)
Layer 7 firewall rules (currently empty)

### 6. meraki_live_data (60 rows)
Real-time data from Meraki devices

### 7. nexus_fex_relationships (2 rows)
Nexus parent-FEX relationships

### 8. nexus_vdc_mapping (16 rows)
Virtual Device Context mappings for Nexus

### 9. one_to_one_nat_rules (0 rows)
1:1 NAT configurations (currently empty)

### 10. ready_queue_daily (53 rows)
Daily snapshot of circuits ready for turn-up

### 11. sfp_modules (89 rows)
SFP module inventory and specifications

---

## Summary Statistics

- **Total Tables:** 65
- **Empty Tables:** 11 (no data)
- **Largest Table:** firewall_rules (75,355 rows)
- **Most Complex:** comprehensive_device_inventory (7 JSONB fields)
- **Core Tables (from CLAUDE.md):** 12
- **New/Undocumented Tables:** 53

## Key Observations

1. **Enablement Tracking System** - New set of 4 tables for tracking circuit enablements
2. **Performance Monitoring** - 2 tables for API and system performance tracking
3. **Enhanced Inventory** - 15 tables for comprehensive hardware inventory
4. **EOL Management** - 6 tables for end-of-life tracking
5. **Many Empty Tables** - 11 tables with no data, possibly for future features

This represents a significant expansion from the 12 core tables documented in CLAUDE.md to a comprehensive 65-table system supporting enhanced monitoring, inventory, and operational capabilities.