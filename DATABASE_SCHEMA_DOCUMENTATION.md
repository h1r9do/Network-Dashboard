# DSR Circuits Database Schema Documentation

## Overview
This document provides comprehensive documentation of the PostgreSQL database schema used by the DSR Circuits system, including all tables, relationships, indexes, and how various scripts interact with the database.

**Database Name:** dsrcircuits  
**Database User:** dsruser  
**Password:** dsrpass123  
**Host:** localhost  
**Port:** 5432  
**Total Tables:** 68 (actual count, not including views)  
**Total Views:** 12 database views  
**Documented Tables:** 39 (57% coverage - major tables documented)  
**Last Updated:** January 8, 2025  

## Table of Contents
1. [Primary Tables](#primary-tables)
2. [Table Relationships](#table-relationships)
3. [Column Naming Conventions](#column-naming-conventions)
4. [Script-to-Table Mapping](#script-to-table-mapping)
5. [Common Queries](#common-queries)
6. [Known Issues & Gotchas](#known-issues--gotchas)

## Primary Tables

### 1. circuits
**Purpose:** Main circuit data from DSR Global CSV import  
**Primary Key:** `id` (auto-increment)  
**Unique Constraint:** `(site_name, circuit_purpose)`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| site_name | VARCHAR(100) | Store identifier | "AZP 08" |
| circuit_purpose | VARCHAR(50) | Primary/Secondary | "Primary" |
| status | VARCHAR(100) | Circuit status | "Enabled" |
| provider_name | VARCHAR(100) | ISP provider | "Cox Business" |
| circuit_type | VARCHAR(100) | Connection type | "DIA Ethernet" |
| bandwidth_down | VARCHAR(50) | Download speed | "300.0M" |
| bandwidth_up | VARCHAR(50) | Upload speed | "30.0M" |
| monthly_cost | NUMERIC(10,2) | Monthly billing | 450.00 |
| ip | VARCHAR(50) | Circuit IP address | "68.15.185.94" |
| date_requested | TIMESTAMP | Request date | 2024-03-15 |
| date_ordered | TIMESTAMP | Order date | 2024-03-20 |
| date_installed | TIMESTAMP | Install date | 2024-04-01 |
| date_turned_up | TIMESTAMP | Activation date | 2024-04-05 |
| assigned_to | VARCHAR(100) | Person assigned | "John Doe" |
| sctask | VARCHAR(50) | ServiceNow task | "SCTASK0123456" |
| manual_override | BOOLEAN | Prevent DSR updates | false |
| manual_override_date | TIMESTAMP | Override date | null |
| manual_override_by | VARCHAR(100) | Who set override | null |
| notes | TEXT | Free-form notes | "Waiting on permit" |
| last_updated | TIMESTAMP | Last update time | 2024-04-05 10:30:00 |

### 2. meraki_inventory
**Purpose:** Meraki device inventory and network data  
**Primary Key:** `network_name`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| network_name | VARCHAR(255) | Network/store name | "AZP 08" |
| device_model | VARCHAR(100) | Device model | "MX67" |
| device_serial | VARCHAR(50) | Device serial | "Q2KN-XXXX-XXXX" |
| device_name | VARCHAR(255) | Device name | "AZP 08 - MX" |
| device_status | VARCHAR(50) | Online/Offline | "online" |
| device_tags | VARCHAR(255) | Space-separated tags | "voice lab" |
| device_notes | TEXT | Meraki notes field | "WAN 1\nCox Business\n300.0M x 30.0M" |
| wan1_ip | VARCHAR(45) | WAN1 IP address | "68.15.185.94" |
| wan1_arin_provider | VARCHAR(255) | ARIN lookup result | "Cox Communications Inc." |
| wan2_ip | VARCHAR(45) | WAN2 IP address | "166.156.123.45" |
| wan2_arin_provider | VARCHAR(255) | ARIN lookup result | "AT&T Corp." |
| last_updated | TIMESTAMP | Last update time | 2024-04-05 01:00:00 |

### 3. enriched_circuits
**Purpose:** Enriched circuit data combining DSR, Meraki, and ARIN data  
**Primary Key:** `id`  
**Note:** Uses `network_name` NOT `site_name` for store identifier  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| network_name | VARCHAR(255) | Store identifier | "AZP 08" |
| device_tags | TEXT[] | Array of tags | {"voice", "lab"} |
| wan1_provider | VARCHAR(255) | WAN1 provider | "Cox Business" |
| wan1_speed | VARCHAR(100) | WAN1 speed | "300.0M x 30.0M" |
| wan1_monthly_cost | VARCHAR(50) | WAN1 cost | "$450.00" |
| wan1_circuit_role | VARCHAR(50) | Primary/Secondary | "Primary" |
| wan1_confirmed | BOOLEAN | Confirmation status | true |
| wan2_provider | VARCHAR(255) | WAN2 provider | "AT&T" |
| wan2_speed | VARCHAR(100) | WAN2 speed | "50.0M x 50.0M" |
| wan2_monthly_cost | VARCHAR(50) | WAN2 cost | "$350.00" |
| wan2_circuit_role | VARCHAR(50) | Primary/Secondary | "Secondary" |
| wan2_confirmed | BOOLEAN | Confirmation status | true |
| wan1_ip | VARCHAR(45) | WAN1 IP | "68.15.185.94" |
| wan2_ip | VARCHAR(45) | WAN2 IP | "166.156.123.45" |
| wan1_arin_org | VARCHAR(255) | WAN1 ARIN org | "Cox Communications Inc." |
| wan2_arin_org | VARCHAR(255) | WAN2 ARIN org | "AT&T Corp." |
| pushed_to_meraki | BOOLEAN | Push status | true |
| pushed_date | TIMESTAMP | When pushed | 2024-04-05 14:30:00 |
| last_updated | TIMESTAMP | Last update | 2024-04-05 14:30:00 |
| created_at | TIMESTAMP | Creation time | 2024-04-01 10:00:00 |

### 4. circuit_history
**Purpose:** Track all changes to circuits  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| site_name | VARCHAR(100) | Store identifier | "AZP 08" |
| circuit_purpose | VARCHAR(50) | Primary/Secondary | "Primary" |
| change_type | VARCHAR(50) | Type of change | "status" |
| old_value | TEXT | Previous value | "In Progress" |
| new_value | TEXT | New value | "Enabled" |
| change_date | TIMESTAMP | When changed | 2024-04-05 10:00:00 |
| detected_by | VARCHAR(50) | Detection method | "nightly_dsr_pull" |

### 5. new_stores
**Purpose:** Track new store construction  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| store_number | VARCHAR(20) | Store identifier | "AZP 99" |
| region | VARCHAR(50) | Geographic region | "Arizona" |
| status | VARCHAR(20) | Construction status | "02-Acquired" |
| tod | DATE | Target Opening Date | 2024-06-01 |
| address | TEXT | Store address | "123 Main St, Phoenix, AZ" |
| primary_provider | VARCHAR(100) | Primary ISP | "Cox Business" |
| primary_speed | VARCHAR(50) | Primary speed | "300M" |
| secondary_provider | VARCHAR(100) | Secondary ISP | "AT&T" |
| secondary_speed | VARCHAR(50) | Secondary speed | "50M" |
| created_date | TIMESTAMP | Record creation | 2024-03-01 |
| last_updated | TIMESTAMP | Last update | 2024-03-15 |

### 6. daily_enablements
**Purpose:** Track daily enablement counts (Ready for Enablement → Enabled transitions only)  
**Primary Key:** `(enablement_date, site_id)`  
**Note:** This is the CORRECT table for enablement tracking  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| enablement_date | DATE | Date of enablement | 2024-04-05 |
| site_id | VARCHAR(20) | Store identifier | "AZP 08" |
| circuit_purpose | VARCHAR(50) | Primary/Secondary | "Primary" |
| assigned_to | VARCHAR(100) | Person assigned | "John Doe" |

### 7. enablement_summary
**Purpose:** Daily summary of enablement counts  
**Primary Key:** `summary_date`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| summary_date | DATE | Summary date | 2024-04-05 |
| total_enabled | INTEGER | Count for that day | 2 |
| week_total | INTEGER | 7-day rolling total | 5 |
| month_total | INTEGER | 30-day rolling total | 21 |
| assigned_breakdown | JSONB | By assignee | {"John Doe": 1, "Jane Smith": 1} |

### 8. circuit_enablements (DEPRECATED)
**Purpose:** OLD/INCORRECT enablement tracking - DO NOT USE  
**Issues:** Contains 723 incorrect records, tracks all status changes not just Ready→Enabled  

### 9. provider_mappings
**Purpose:** Normalize provider names  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| raw_name | VARCHAR(255) | Original name | "COX BUSINESS" |
| normalized_name | VARCHAR(255) | Standardized name | "Cox Business" |
| created_date | TIMESTAMP | Creation date | 2024-01-01 |

### 10. firewall_rules
**Purpose:** L3 firewall rule templates  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| network_name | VARCHAR(100) | Template source | "NEO 07" |
| rule_number | INTEGER | Rule order | 1 |
| name | VARCHAR(200) | Rule name | "Allow HTTPS" |
| protocol | VARCHAR(20) | Protocol | "tcp" |
| src_cidr | VARCHAR(50) | Source CIDR | "any" |
| src_port | VARCHAR(50) | Source port | "any" |
| dest_cidr | VARCHAR(50) | Destination CIDR | "any" |
| dest_port | VARCHAR(50) | Destination port | "443" |
| policy | VARCHAR(20) | Action | "allow" |
| comment | TEXT | Rule comment | "Allow HTTPS traffic" |

### 11. switch_port_clients
**Purpose:** Switch port visibility and connected devices  
**Primary Key:** Composite `(switch_serial, port_id, mac_address)`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| store_name | VARCHAR(100) | Store/network name | "AZP 08" |
| switch_name | VARCHAR(100) | Switch device name | "AZP 08 - SW1" |
| switch_serial | VARCHAR(50) | Switch serial | "Q2SW-XXXX-XXXX" |
| port_id | VARCHAR(50) | Port identifier | "1" |
| hostname | VARCHAR(200) | Connected device | "POS-01" |
| ip_address | VARCHAR(50) | Device IP | "192.168.1.100" |
| mac_address | VARCHAR(50) | Device MAC | "00:1b:44:11:3a:b7" |
| vlan | INTEGER | VLAN assignment | 100 |
| manufacturer | VARCHAR(100) | MAC OUI lookup | "Dell Inc." |
| description | TEXT | Port description | "POS Terminal 1" |
| last_seen | TIMESTAMP | Last detection | 2024-04-05 01:30:00 |

### 12. performance_metrics
**Purpose:** API endpoint performance monitoring  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| endpoint | VARCHAR(200) | API endpoint | "/api/circuits/search" |
| method | VARCHAR(10) | HTTP method | "GET" |
| response_time_ms | FLOAT | Response time | 45.6 |
| response_size_bytes | INTEGER | Response size | 15234 |
| status_code | INTEGER | HTTP status | 200 |
| timestamp | TIMESTAMP | Measurement time | 2024-04-05 10:00:00 |

### 13. inventory_summary
**Purpose:** Device model summaries  
**Primary Key:** `model`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| model | VARCHAR(100) | Device model | "MX67" |
| count | INTEGER | Device count | 245 |
| category | VARCHAR(50) | Device category | "Security Appliance" |
| last_updated | TIMESTAMP | Update time | 2024-04-05 03:00:00 |

### 14. rdap_cache
**Purpose:** Cache ARIN RDAP lookups  
**Primary Key:** `ip_address`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| ip_address | VARCHAR(45) | IP address | "68.15.185.94" |
| provider | VARCHAR(255) | ISP name | "Cox Communications Inc." |
| last_lookup | TIMESTAMP | Lookup time | 2024-04-05 01:00:00 |

### 15. circuit_assignments
**Purpose:** SCTASK and personnel attribution  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| site_name | VARCHAR(100) | Store identifier | "AZP 08" |
| site_id | VARCHAR(100) | Alternative site ID | "AZP 08" |
| circuit_purpose | VARCHAR(100) | Primary/Secondary | "Primary" |
| sctask | VARCHAR(50) | ServiceNow task | "SCTASK0123456" |
| sctask_number | VARCHAR(50) | Task number | "SCTASK0123456" |
| sctask_sys_id | VARCHAR(100) | ServiceNow sys ID | "abc123def456" |
| assigned_to | VARCHAR(100) | Person assigned | "John Doe" |
| assignment_date | TIMESTAMP | Assignment date | 2024-04-05 10:00:00 |
| status | VARCHAR(50) | Assignment status | "Completed" |
| notes | TEXT | Assignment notes | "Circuit enabled successfully" |
| created_by | VARCHAR(100) | Created by user | "system" |
| updated_by | VARCHAR(100) | Updated by user | "admin" |
| created_at | TIMESTAMP | Creation time | 2024-04-01 10:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 10:00:00 |

### 16. daily_summaries
**Purpose:** Daily processing summary statistics  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| summary_date | DATE | Summary date | 2024-04-05 |
| total_circuits | INTEGER | Total circuit count | 7026 |
| enabled_count | INTEGER | Enabled circuits | 5234 |
| ready_count | INTEGER | Ready for turn up | 234 |
| customer_action_count | INTEGER | Customer action needed | 45 |
| construction_count | INTEGER | Under construction | 123 |
| planning_count | INTEGER | In planning | 345 |
| csv_file_processed | VARCHAR(100) | CSV filename | "dsr_export_20240405.csv" |
| processing_time_seconds | NUMERIC | Processing duration | 45.67 |
| created_at | TIMESTAMP | Creation time | 2024-04-05 00:30:00 |

### 17. firewall_deployment_log
**Purpose:** Track firewall rule deployments  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| template_network_id | VARCHAR(100) | Source network ID | "N_123456" |
| template_network_name | VARCHAR(100) | Source network | "NEO 07" |
| target_network_id | VARCHAR(100) | Target network ID | "N_789012" |
| target_network_name | VARCHAR(100) | Target network | "AZP 08" |
| deployment_type | VARCHAR(50) | Type of deployment | "L3_RULES" |
| rules_deployed | INTEGER | Number of rules | 25 |
| deployment_status | VARCHAR(20) | Status | "SUCCESS" |
| error_message | TEXT | Error details | null |
| deployed_by | VARCHAR(100) | User who deployed | "admin" |
| deployment_time | TIMESTAMP | When deployed | 2024-04-05 14:30:00 |

### 18. enrichment_change_tracking
**Purpose:** Track changes in enrichment data  
**Primary Key:** `network_name`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| network_name | VARCHAR(255) | Network/store name | "AZP 08" |
| last_device_notes_hash | VARCHAR(64) | MD5 hash of notes | "a1b2c3d4e5f6..." |
| last_wan1_ip | VARCHAR(45) | Previous WAN1 IP | "68.15.185.94" |
| last_wan2_ip | VARCHAR(45) | Previous WAN2 IP | "166.156.123.45" |
| last_enrichment_run | TIMESTAMP | Last enrichment | 2024-04-05 01:00:00 |
| dsr_circuits_hash | VARCHAR(64) | DSR data hash | "f6e5d4c3b2a1..." |

### 19. meraki_live_data
**Purpose:** Real-time Meraki device status  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| network_name | VARCHAR(255) | Network name | "AZP 08" |
| network_id | VARCHAR(100) | Meraki network ID | "N_123456" |
| device_serial | VARCHAR(100) | Device serial | "Q2KN-XXXX-XXXX" |
| device_model | VARCHAR(50) | Device model | "MX67" |
| device_name | VARCHAR(255) | Device name | "AZP 08 - MX" |
| device_tags | TEXT | Device tags | "voice production" |
| wan1_provider_label | VARCHAR(255) | WAN1 label | "Cox Business" |
| wan1_speed | VARCHAR(100) | WAN1 speed | "300.0M x 30.0M" |
| wan1_ip | VARCHAR(45) | WAN1 IP | "68.15.185.94" |
| wan1_provider | VARCHAR(255) | WAN1 provider | "Cox Business" |
| wan1_provider_comparison | VARCHAR(50) | Match status | "MATCH" |
| wan2_provider_label | VARCHAR(255) | WAN2 label | "AT&T" |
| wan2_speed | VARCHAR(100) | WAN2 speed | "50.0M x 50.0M" |
| wan2_ip | VARCHAR(45) | WAN2 IP | "166.156.123.45" |
| wan2_provider | VARCHAR(255) | WAN2 provider | "AT&T" |
| wan2_provider_comparison | VARCHAR(50) | Match status | "MATCH" |
| raw_notes | TEXT | Raw device notes | "WAN 1\nCox Business\n300.0M x 30.0M" |
| last_updated | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

### 20. meraki_eol
**Purpose:** Basic Meraki EOL tracking  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| model | VARCHAR(100) | Device model | "MX67" |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale date | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| source | VARCHAR(50) | Data source | "meraki_website" |
| pdf_url | VARCHAR(500) | PDF link | "https://meraki.com/eol/mx67.pdf" |
| pdf_name | VARCHAR(200) | PDF filename | "MX67_EOL_Notice.pdf" |
| confidence | VARCHAR(20) | Data confidence | "HIGH" |
| created_at | TIMESTAMP | Creation time | 2024-01-15 10:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:15:00 |

### 21. meraki_eol_enhanced
**Purpose:** Enhanced EOL data with 505 models  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| model | VARCHAR(50) | Device model | "MX67" |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale date | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| source | VARCHAR(100) | Data source | "PDF:MX_Series_EOL_2023.pdf" |
| method | VARCHAR(50) | Collection method | "pdf_extraction" |
| confidence | VARCHAR(20) | Data confidence | "HIGH" |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:15:00 |

### 22. meraki_eol_pdf
**Purpose:** EOL data from 164 PDF files  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| model | VARCHAR(100) | Device model | "MX67" |
| model_family | VARCHAR(100) | Model family | "MX Series" |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale date | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| source_pdf | VARCHAR(200) | PDF filename | "MX_Series_EOL_2023.pdf" |
| pdf_url | VARCHAR(500) | PDF URL | "https://meraki.com/pdfs/eol/..." |
| pdf_hash | VARCHAR(64) | PDF MD5 hash | "a1b2c3d4e5f6..." |
| extracted_text | TEXT | Extracted text | "End-of-Life Announcement..." |
| confidence | VARCHAR(20) | Data confidence | "HIGH" |
| created_at | TIMESTAMP | Creation time | 2024-01-15 10:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:15:00 |

### 23. netdisco_eol_mapping
**Purpose:** EOL dates for traditional network devices  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| vendor | VARCHAR(100) | Device vendor | "Cisco" |
| model | VARCHAR(200) | Device model | "WS-C2960X-48FPD-L" |
| normalized_model | VARCHAR(200) | Normalized model | "C2960X-48FPD-L" |
| device_type | VARCHAR(50) | Device type | "Switch" |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale date | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| source | VARCHAR(50) | Data source | "excel_import" |
| notes | TEXT | Additional notes | "93 models imported" |
| last_updated | TIMESTAMP | Last update | 2024-04-05 01:45:00 |

### 24. netdisco_inventory_summary
**Purpose:** Traditional network device inventory  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment primary key | 1234 |
| vendor | VARCHAR(100) | Device vendor | "Cisco" |
| model | VARCHAR(200) | Device model | "WS-C2960X-48FPD-L" |
| device_type | VARCHAR(50) | Device type | "Switch" |
| logical_devices | INTEGER | Logical count | 5 |
| physical_devices | INTEGER | Physical count | 3 |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| last_updated | TIMESTAMP | Last update | 2024-04-05 01:45:00 |

### 25. network_vlans
**Purpose:** VLAN configurations per network  
**Primary Key:** Composite `(network_id, vlan_id)`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| network_id | VARCHAR(100) | Meraki network ID | "N_123456" |
| vlan_id | INTEGER | VLAN identifier | 100 |
| name | VARCHAR(100) | VLAN name | "Corporate" |
| subnet | VARCHAR(50) | VLAN subnet | "192.168.100.0/24" |
| appliance_ip | VARCHAR(50) | Gateway IP | "192.168.100.1" |
| group_policy_id | VARCHAR(100) | Group policy | "101" |
| template_vlan_id | INTEGER | Template VLAN | 100 |
| dhcp_handling | VARCHAR(50) | DHCP mode | "Run a DHCP server" |
| dhcp_lease_time | VARCHAR(50) | Lease duration | "1 day" |
| dhcp_boot_options_enabled | BOOLEAN | Boot options | false |
| dhcp_options | JSONB | DHCP options | [] |
| reserved_ip_ranges | JSONB | Reserved IPs | [] |
| fixed_ip_assignments | JSONB | Static IPs | {} |
| dns_nameservers | VARCHAR(255) | DNS servers | "8.8.8.8\n8.8.4.4" |

### 26. network_dhcp_options
**Purpose:** DHCP option configurations  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| network_id | VARCHAR(100) | Network ID | "N_123456" |
| vlan_id | INTEGER | VLAN ID | 100 |
| option_type | VARCHAR(50) | Option type | "text" |
| option_code | INTEGER | DHCP code | 66 |
| option_value | VARCHAR(255) | Option value | "192.168.1.10" |

### 27. network_wan_ports
**Purpose:** WAN port configurations  
**Primary Key:** Composite `(network_id, port_number)`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| network_id | VARCHAR(100) | Network ID | "N_123456" |
| port_number | INTEGER | WAN port | 1 |
| enabled | BOOLEAN | Port enabled | true |
| vlan_tagging_enabled | BOOLEAN | VLAN tagging | false |
| vlan_id | INTEGER | VLAN ID | null |
| access_type | VARCHAR(50) | Access type | "none" |
| allowed_vlans | VARCHAR(255) | Allowed VLANs | "all" |

### 28. inventory_devices
**Purpose:** Full Meraki inventory across all organizations  
**Primary Key:** `serial`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| serial | VARCHAR(50) | Device serial | "Q2KN-XXXX-XXXX" |
| name | VARCHAR(255) | Device name | "AZP 08 - MX" |
| model | VARCHAR(100) | Device model | "MX67" |
| network_id | VARCHAR(100) | Network ID | "N_123456" |
| network_name | VARCHAR(255) | Network name | "AZP 08" |
| organization_id | VARCHAR(100) | Org ID | "123456" |
| organization_name | VARCHAR(255) | Org name | "Discount Tire" |
| status | VARCHAR(50) | Device status | "online" |
| tags | TEXT | Device tags | "voice production" |
| address | TEXT | Device address | "123 Main St" |
| firmware | VARCHAR(100) | Firmware version | "15.44" |
| last_reported_at | TIMESTAMP | Last seen | 2024-04-05 10:00:00 |
| claimed_at | TIMESTAMP | Claim date | 2023-01-15 10:00:00 |
| product_type | VARCHAR(50) | Product type | "appliance" |
| details | JSONB | Additional details | {} |
| announcement_date | DATE | EOL announced | 2023-01-15 |
| end_of_sale | DATE | End of sale | 2024-06-30 |
| end_of_support | DATE | End of support | 2029-06-30 |
| created_at | TIMESTAMP | Record creation | 2024-04-05 02:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 02:00:00 |

### 29. ready_queue_daily
**Purpose:** Daily ready queue tracking  
**Primary Key:** `summary_date`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| summary_date | DATE | Summary date | 2024-04-05 |
| ready_count | INTEGER | Ready for turn-up | 45 |
| customer_action_count | INTEGER | Customer action | 12 |
| total_queue | INTEGER | Total in queue | 57 |
| created_at | TIMESTAMP | Creation time | 2024-04-05 04:00:00 |

### 30. enablement_trends
**Purpose:** Enablement trend analysis  
**Primary Key:** `id`  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| period_type | VARCHAR(20) | Period type | "7_day" |
| period_date | DATE | Period date | 2024-04-05 |
| average_daily | NUMERIC(10,2) | Daily average | 5.43 |
| total_period | INTEGER | Period total | 38 |
| created_at | TIMESTAMP | Creation time | 2024-04-05 04:00:00 |

### 31. device_components
**Purpose:** Hardware component inventory from SNMP collection  
**Primary Key:** `id`  
**Rows:** 22,973  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| ip_address | INET | Device IP | 192.168.1.1 |
| component_index | VARCHAR(50) | Component index | "1.0.1" |
| component_class | VARCHAR(50) | Component class | "chassis" |
| description | TEXT | Component description | "Cisco Catalyst 2960X" |
| serial_number | VARCHAR(255) | Serial number | "FOC1234ABCD" |
| model_name | VARCHAR(255) | Model name | "WS-C2960X-48FPD-L" |
| manufacturer | VARCHAR(255) | Manufacturer | "Cisco Systems" |
| hardware_revision | VARCHAR(100) | Hardware revision | "1.0" |
| firmware_revision | VARCHAR(100) | Firmware revision | "15.0(2)SE11" |
| software_revision | VARCHAR(100) | Software revision | "15.0(2)SE11" |
| physical_name | VARCHAR(255) | Physical name | "Switch 1" |
| asset_id | VARCHAR(100) | Asset ID | "AS123456" |
| is_fru | BOOLEAN | Field replaceable unit | true |
| collection_timestamp | TIMESTAMP | Collection time | 2024-04-05 01:00:00 |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

### 32. ip_assignment_history
**Purpose:** Track IP address changes over time  
**Primary Key:** `id`  
**Rows:** 3,912  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| site_name | VARCHAR(100) | Store identifier | "AZP 08" |
| wan1_ip | VARCHAR(45) | WAN1 IP address | "68.15.185.94" |
| wan2_ip | VARCHAR(45) | WAN2 IP address | "166.156.123.45" |
| snapshot_date | TIMESTAMP | Snapshot date | 2024-04-05 01:00:00 |
| ip_flip_detected | BOOLEAN | IP flip detected | false |
| flip_handled | BOOLEAN | Flip handled | true |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |

### 33. collected_chassis
**Purpose:** Chassis information from SNMP collection  
**Primary Key:** `id`  
**Rows:** 1,312  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| collection_id | INTEGER | Collection batch ID | 456 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| name | VARCHAR(255) | Chassis name | "Cisco Catalyst 2960X" |
| description | TEXT | Chassis description | "Cisco Catalyst 2960X 48 Port Switch" |
| pid | VARCHAR(100) | Product ID | "WS-C2960X-48FPD-L" |
| vid | VARCHAR(50) | Version ID | "V01" |
| serial_number | VARCHAR(100) | Serial number | "FOC1234ABCD" |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |

### 34. collected_modules
**Purpose:** Module information from SNMP collection  
**Primary Key:** `id`  
**Rows:** 1,501  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| collection_id | INTEGER | Collection batch ID | 456 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| module_number | VARCHAR(50) | Module number | "1" |
| module_name | VARCHAR(255) | Module name | "48-Port Ethernet Module" |
| module_type | VARCHAR(100) | Module type | "Ethernet" |
| model | VARCHAR(100) | Module model | "WS-C2960X-48FPD-L" |
| serial_number | VARCHAR(100) | Serial number | "FOC1234ABCD" |
| status | VARCHAR(50) | Module status | "active" |
| ports | INTEGER | Number of ports | 48 |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |

### 35. collected_sfps
**Purpose:** SFP module information from SNMP collection  
**Primary Key:** `id`  
**Rows:** 1,643  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| collection_id | INTEGER | Collection batch ID | 456 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| interface | VARCHAR(100) | Interface name | "GigabitEthernet1/0/1" |
| sfp_type | VARCHAR(100) | SFP type | "1000BASE-SX" |
| vendor | VARCHAR(100) | SFP vendor | "Cisco Systems" |
| part_number | VARCHAR(100) | Part number | "GLC-SX-MMD" |
| serial_number | VARCHAR(100) | Serial number | "ABC1234567" |
| wavelength | VARCHAR(50) | Wavelength | "850nm" |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |

### 36. comprehensive_device_inventory
**Purpose:** Complete device inventory with detailed JSON data  
**Primary Key:** `id`  
**Rows:** 169  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| ip_address | INET | Device IP | 192.168.1.1 |
| collection_timestamp | TIMESTAMP | Collection time | 2024-04-05 01:00:00 |
| system_info | JSONB | System information | {"uptime": "30 days"} |
| physical_components | JSONB | Physical components | {"chassis": {...}} |
| interfaces | JSONB | Interface data | {"GigE1/0/1": {...}} |
| environmental_data | JSONB | Environmental data | {"temperature": "35C"} |
| cisco_specific | JSONB | Cisco-specific data | {"ios_version": "15.0"} |
| stack_info | JSONB | Stack information | {"stack_member": 1} |
| summary | JSONB | Summary data | {"port_count": 48} |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

### 37. datacenter_inventory
**Purpose:** Datacenter device inventory with EOL tracking  
**Primary Key:** `id`  
**Rows:** 225  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| site | VARCHAR(100) | Datacenter site | "PHX-DC01" |
| hostname | VARCHAR(100) | Device hostname | "core01.phx.com" |
| vendor | VARCHAR(50) | Device vendor | "Cisco" |
| mgmt_ip | VARCHAR(45) | Management IP | "10.1.1.1" |
| device_type | VARCHAR(50) | Device type | "Router" |
| model | VARCHAR(100) | Device model | "ISR4431" |
| software_version | VARCHAR(200) | Software version | "16.09.04" |
| serial_number | VARCHAR(100) | Serial number | "FOC1234ABCD" |
| announcement_date | DATE | EOL announcement | 2023-01-15 |
| end_of_sale_date | DATE | End of sale | 2024-06-30 |
| end_of_support_date | DATE | End of support | 2029-06-30 |
| source | VARCHAR(50) | Data source | "manual_entry" |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

### 38. device_access
**Purpose:** Device access credentials and connection info  
**Primary Key:** `id`  
**Rows:** 168  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| hostname | VARCHAR(255) | Device hostname | "switch01.store.com" |
| mgmt_ip | VARCHAR(50) | Management IP | "192.168.1.1" |
| access_method | VARCHAR(20) | Access method | "ssh" |
| username | VARCHAR(100) | Username | "admin" |
| password | VARCHAR(255) | Password (encrypted) | "****" |
| snmp_community | VARCHAR(100) | SNMP community | "public" |
| snmp_version | VARCHAR(10) | SNMP version | "v2c" |
| ssh_port | INTEGER | SSH port | 22 |
| enable_password | VARCHAR(255) | Enable password | "****" |
| last_successful_access | TIMESTAMP | Last success | 2024-04-05 01:00:00 |
| last_failed_access | TIMESTAMP | Last failure | 2024-04-04 12:00:00 |
| failure_count | INTEGER | Failure count | 0 |
| notes | TEXT | Access notes | "Default credentials" |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

### 39. chassis_blades
**Purpose:** Chassis blade information  
**Primary Key:** `id`  
**Rows:** 149  

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-increment ID | 1234 |
| device_id | INTEGER | Device ID reference | 456 |
| module_number | VARCHAR(10) | Module number | "1" |
| ports | VARCHAR(10) | Port count | "48" |
| card_type | VARCHAR(255) | Card type | "Ethernet Line Card" |
| model | VARCHAR(100) | Blade model | "WS-X6748-GE-TX" |
| serial_number | VARCHAR(50) | Serial number | "JAE1234ABCD" |
| created_at | TIMESTAMP | Record creation | 2024-04-05 01:00:00 |
| updated_at | TIMESTAMP | Last update | 2024-04-05 01:00:00 |

## Table Relationships

### Primary Relationships
1. **circuits ↔ meraki_inventory**  
   - Join on: `circuits.site_name = meraki_inventory.network_name`
   - Purpose: Match DSR circuits with Meraki devices

2. **circuits ↔ enriched_circuits**  
   - Join on: `circuits.site_name = enriched_circuits.network_name`
   - Purpose: Get enriched circuit data

3. **meraki_inventory ↔ enriched_circuits**  
   - Join on: `meraki_inventory.network_name = enriched_circuits.network_name`
   - Purpose: Combine device and enriched data

4. **circuits → circuit_history**  
   - Relationship: One-to-many
   - Track all changes to circuit records

5. **circuits → daily_enablements**  
   - Join on: `circuits.site_name = daily_enablements.site_id`
   - Track enablement transitions

## Column Naming Conventions

### Important Differences
1. **circuits table:** Uses `site_name` for store identifier
2. **enriched_circuits table:** Uses `network_name` for store identifier
3. **meraki_inventory table:** Uses `network_name` for store identifier

### Standard Conventions
- Timestamps: `last_updated`, `created_at`, `created_date`
- Boolean flags: `manual_override`, `pushed_to_meraki`, `wan1_confirmed`
- Foreign keys: Match primary key name (e.g., `site_name`, `network_name`)

## Script-to-Table Mapping

### nightly_dsr_pull_db_with_override.py → update_circuits_from_tracking_with_override_working.py
**Tables Used:**
- WRITES: `circuits`, `daily_summaries`
- READS: `circuits` (for manual_override check)
- Purpose: Import DSR Global CSV data with manual override protection

### nightly_meraki_db.py
**Tables Used:**
- WRITES: `meraki_inventory`, `rdap_cache`, `network_vlans`, `network_dhcp_options`, `network_wan_ports`, `firewall_rules`, `new_stores`
- READS: `rdap_cache`, `new_stores`
- Purpose: Collect Meraki data via API, ARIN lookups, network configurations

### nightly_inventory_db.py
**Tables Used:**
- WRITES: `inventory_devices`, `inventory_summary`
- READS: `meraki_eol_enhanced`
- CREATES: `inventory_devices`, `inventory_summary` (if not exist)
- Purpose: Full Meraki inventory across all organizations with EOL data

### nightly_enriched_db.py
**Tables Used:**
- WRITES: `enriched_circuits` (TRUNCATE then INSERT)
- READS: `circuits`, `meraki_inventory`
- Purpose: Combine DSR, Meraki, and ARIN data into enriched view

### nightly_enablement_db.py
**Tables Used:**
- WRITES: `daily_enablements`, `enablement_summary`, `ready_queue_daily`, `enablement_trends`
- READS: `circuits`
- CREATES: All four tables if not exist
- Purpose: Track Ready→Enabled transitions from historical CSV files

### nightly_circuit_history.py
**Tables Used:**
- WRITES: `circuit_history`
- READS: `circuits`, `circuit_history`
- Purpose: Detect and log circuit changes by comparing daily CSV files

### nightly_switch_visibility_db.py
**Tables Used:**
- WRITES: `switch_port_clients`
- READS: None (Meraki API only)
- Purpose: Collect switch port client data (Note: Script not found in nightly/)

### hourly_api_performance.py
**Tables Used:**
- WRITES: `performance_metrics`
- READS: `performance_metrics` (for cleanup)
- Purpose: Monitor API endpoint performance hourly

### confirm_meraki_notes_db.py
**Tables Used:**
- READS: `circuits`, `meraki_inventory`, `enriched_circuits`
- Purpose: Provide modal confirmation data

### push_meraki_notes_db.py
**Tables Used:**
- READS: `enriched_circuits`
- UPDATES: `enriched_circuits` (pushed_to_meraki, pushed_date)
- Purpose: Push notes to Meraki devices

## SQL Queries by Script

### Nightly Scripts SQL Queries

#### nightly_dsr_pull_db_with_override.py
```sql
-- Check for manual overrides before updating
SELECT site_name, circuit_purpose, manual_override, notes 
FROM circuits 
WHERE site_name = %s AND circuit_purpose = %s;

-- Bulk insert/update circuits (respecting manual overrides)
INSERT INTO circuits (
    site_name, circuit_purpose, status, provider_name, circuit_type,
    bandwidth_down, bandwidth_up, monthly_cost, ip, 
    date_requested, date_ordered, date_installed, date_turned_up,
    assigned_to, sctask, last_updated
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (site_name, circuit_purpose) DO UPDATE SET
    status = EXCLUDED.status,
    provider_name = EXCLUDED.provider_name,
    circuit_type = EXCLUDED.circuit_type,
    bandwidth_down = EXCLUDED.bandwidth_down,
    bandwidth_up = EXCLUDED.bandwidth_up,
    monthly_cost = EXCLUDED.monthly_cost,
    ip = EXCLUDED.ip,
    date_requested = EXCLUDED.date_requested,
    date_ordered = EXCLUDED.date_ordered,
    date_installed = EXCLUDED.date_installed,
    date_turned_up = EXCLUDED.date_turned_up,
    assigned_to = EXCLUDED.assigned_to,
    sctask = EXCLUDED.sctask,
    last_updated = EXCLUDED.last_updated
WHERE circuits.manual_override = FALSE;

-- Update daily summary
INSERT INTO daily_summaries (
    summary_date, total_circuits, enabled_count, ready_count,
    customer_action_count, construction_count, planning_count,
    csv_file_processed, processing_time_seconds, created_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

#### nightly_enablement_db.py
```sql
-- Find circuits that transitioned to "Enabled" status
WITH previous_day AS (
    SELECT site_id, circuit_purpose, status
    FROM circuits_history
    WHERE DATE(change_date) = CURRENT_DATE - INTERVAL '1 day'
),
current_day AS (
    SELECT site_name as site_id, circuit_purpose, status, assigned_to
    FROM circuits
    WHERE status = 'Enabled'
)
SELECT c.site_id, c.circuit_purpose, c.assigned_to
FROM current_day c
LEFT JOIN previous_day p 
    ON c.site_id = p.site_id 
    AND c.circuit_purpose = p.circuit_purpose
WHERE p.status IS NULL OR p.status != 'Enabled';

-- Insert daily enablements
INSERT INTO daily_enablements (enablement_date, site_id, circuit_purpose, assigned_to)
VALUES (%s, %s, %s, %s)
ON CONFLICT (enablement_date, site_id) DO NOTHING;

-- Update enablement summary
INSERT INTO enablement_summary (
    summary_date, total_enabled, week_total, month_total, assigned_breakdown
) VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (summary_date) DO UPDATE SET
    total_enabled = EXCLUDED.total_enabled,
    week_total = EXCLUDED.week_total,
    month_total = EXCLUDED.month_total,
    assigned_breakdown = EXCLUDED.assigned_breakdown;
```

#### nightly_meraki_db.py
```sql
-- RDAP cache lookup
SELECT provider, last_lookup 
FROM rdap_cache 
WHERE ip_address = %s AND last_lookup > NOW() - INTERVAL '30 days';

-- Insert/update RDAP cache
INSERT INTO rdap_cache (ip_address, provider, last_lookup)
VALUES (%s, %s, %s)
ON CONFLICT (ip_address) DO UPDATE SET
    provider = EXCLUDED.provider,
    last_lookup = EXCLUDED.last_lookup;

-- Insert/update Meraki inventory
INSERT INTO meraki_inventory (
    network_name, device_model, device_serial, device_name, device_status,
    device_tags, device_notes, wan1_ip, wan1_arin_provider, 
    wan2_ip, wan2_arin_provider, last_updated
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (network_name) DO UPDATE SET
    device_model = EXCLUDED.device_model,
    device_serial = EXCLUDED.device_serial,
    device_name = EXCLUDED.device_name,
    device_status = EXCLUDED.device_status,
    device_tags = EXCLUDED.device_tags,
    device_notes = EXCLUDED.device_notes,
    wan1_ip = EXCLUDED.wan1_ip,
    wan1_arin_provider = EXCLUDED.wan1_arin_provider,
    wan2_ip = EXCLUDED.wan2_ip,
    wan2_arin_provider = EXCLUDED.wan2_arin_provider,
    last_updated = EXCLUDED.last_updated;

-- Store firewall rules
INSERT INTO firewall_rules (
    network_name, rule_number, name, protocol, src_cidr, src_port,
    dest_cidr, dest_port, policy, comment
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

#### nightly_enriched_db.py
```sql
-- Match circuits with Meraki inventory by IP
SELECT 
    c.site_name, c.circuit_purpose, c.status, c.provider_name, c.ip,
    m.network_name, m.device_notes, m.wan1_ip, m.wan2_ip,
    m.wan1_arin_provider, m.wan2_arin_provider
FROM circuits c
LEFT JOIN meraki_inventory m ON (
    (c.ip = m.wan1_ip OR c.ip = m.wan2_ip) 
    AND c.site_name = m.network_name
)
WHERE c.status = 'Enabled';

-- Insert/update enriched circuits
INSERT INTO enriched_circuits (
    network_name, device_tags, 
    wan1_provider, wan1_speed, wan1_monthly_cost, wan1_circuit_role, wan1_confirmed,
    wan2_provider, wan2_speed, wan2_monthly_cost, wan2_circuit_role, wan2_confirmed,
    wan1_ip, wan2_ip, wan1_arin_org, wan2_arin_org,
    pushed_to_meraki, pushed_date, last_updated, created_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (network_name) DO UPDATE SET
    device_tags = EXCLUDED.device_tags,
    wan1_provider = EXCLUDED.wan1_provider,
    wan1_speed = EXCLUDED.wan1_speed,
    wan1_monthly_cost = EXCLUDED.wan1_monthly_cost,
    wan1_circuit_role = EXCLUDED.wan1_circuit_role,
    wan1_confirmed = EXCLUDED.wan1_confirmed,
    wan2_provider = EXCLUDED.wan2_provider,
    wan2_speed = EXCLUDED.wan2_speed,
    wan2_monthly_cost = EXCLUDED.wan2_monthly_cost,
    wan2_circuit_role = EXCLUDED.wan2_circuit_role,
    wan2_confirmed = EXCLUDED.wan2_confirmed,
    wan1_ip = EXCLUDED.wan1_ip,
    wan2_ip = EXCLUDED.wan2_ip,
    wan1_arin_org = EXCLUDED.wan1_arin_org,
    wan2_arin_org = EXCLUDED.wan2_arin_org,
    last_updated = EXCLUDED.last_updated;
```

#### nightly_switch_visibility_db.py
```sql
-- Bulk insert switch port clients
INSERT INTO switch_port_clients (
    store_name, switch_name, switch_serial, port_id, hostname,
    ip_address, mac_address, vlan, manufacturer, description, last_seen
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (switch_serial, port_id, mac_address) DO UPDATE SET
    store_name = EXCLUDED.store_name,
    switch_name = EXCLUDED.switch_name,
    hostname = EXCLUDED.hostname,
    ip_address = EXCLUDED.ip_address,
    vlan = EXCLUDED.vlan,
    manufacturer = EXCLUDED.manufacturer,
    description = EXCLUDED.description,
    last_seen = EXCLUDED.last_seen;

-- Clean up old entries
DELETE FROM switch_port_clients 
WHERE last_seen < NOW() - INTERVAL '7 days';
```

### Flask Routes SQL Queries

#### Main Circuit Routes (dsrcircuits.py)
```sql
-- Search circuits with filters (SQLAlchemy)
circuits = Circuit.query.filter(
    Circuit.status == 'Enabled',
    Circuit.site_name.ilike(f'%{search_term}%')
).order_by(Circuit.site_name).all()

-- Get ready for turn up circuits
SELECT * FROM circuits 
WHERE status IN ('Ready for Turn-up', 'Customer Action Required')
ORDER BY date_requested DESC;

-- Update circuit with manual override
UPDATE circuits SET
    provider_name = %s,
    circuit_type = %s,
    bandwidth_down = %s,
    bandwidth_up = %s,
    manual_override = TRUE,
    manual_override_date = NOW(),
    manual_override_by = %s
WHERE site_name = %s AND circuit_purpose = %s;
```

#### Enablement Report Routes
```sql
-- Daily enablement data with date series
WITH date_series AS (
    SELECT generate_series(
        '2025-04-29'::date,
        CURRENT_DATE,
        '1 day'::interval
    )::date AS date
)
SELECT 
    ds.date,
    COALESCE(COUNT(de.site_id), 0) as count
FROM date_series ds
LEFT JOIN daily_enablements de ON ds.date = de.enablement_date
GROUP BY ds.date
ORDER BY ds.date;

-- Team attribution query
SELECT 
    COALESCE(assigned_to, 'Unknown') as team,
    COUNT(*) as count
FROM daily_enablements
WHERE enablement_date BETWEEN %s AND %s
GROUP BY assigned_to
ORDER BY count DESC;

-- Ready queue tracking
SELECT 
    rq.queue_date,
    rq.ready_count,
    rq.customer_action_count,
    rq.total_queue
FROM ready_queue_daily rq
WHERE queue_date BETWEEN %s AND %s
ORDER BY queue_date;
```

#### New Stores TOD Management
```sql
-- Get stores by TOD month
SELECT * FROM new_stores
WHERE EXTRACT(YEAR FROM tod) = %s 
  AND EXTRACT(MONTH FROM tod) = %s
ORDER BY tod, store_number;

-- Update store with conflict handling
INSERT INTO new_stores (
    store_number, region, status, tod, address,
    primary_provider, primary_speed, secondary_provider, secondary_speed
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (store_number) DO UPDATE SET
    region = EXCLUDED.region,
    status = EXCLUDED.status,
    tod = EXCLUDED.tod,
    address = EXCLUDED.address,
    primary_provider = EXCLUDED.primary_provider,
    primary_speed = EXCLUDED.primary_speed,
    secondary_provider = EXCLUDED.secondary_provider,
    secondary_speed = EXCLUDED.secondary_speed,
    last_updated = NOW();
```

#### Switch Visibility Routes
```sql
-- Get switch ports by store with filtering
SELECT 
    store_name, switch_name, port_id, hostname,
    ip_address, mac_address, vlan, manufacturer,
    description, last_seen
FROM switch_port_clients
WHERE store_name = %s
  AND (%s IS NULL OR hostname ILIKE %s)
  AND (%s IS NULL OR ip_address::text LIKE %s)
  AND (%s IS NULL OR manufacturer ILIKE %s)
ORDER BY switch_name, CAST(port_id AS INTEGER);

-- Summary statistics
SELECT 
    COUNT(DISTINCT store_name) as store_count,
    COUNT(DISTINCT switch_serial) as switch_count,
    COUNT(DISTINCT mac_address) as client_count,
    COUNT(*) as port_count
FROM switch_port_clients
WHERE last_seen > NOW() - INTERVAL '24 hours';
```

#### Performance Monitoring
```sql
-- Insert performance metrics
INSERT INTO performance_metrics (
    endpoint, method, response_time_ms, response_size_bytes,
    status_code, timestamp
) VALUES (%s, %s, %s, %s, %s, %s);

-- Get performance summary
SELECT 
    endpoint,
    AVG(response_time_ms) as avg_response_time,
    MAX(response_time_ms) as max_response_time,
    COUNT(*) as request_count,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
FROM performance_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY endpoint
ORDER BY avg_response_time DESC;
```

## Common Queries

### Get Circuit with Enriched Data
```sql
SELECT 
    c.site_name,
    c.circuit_purpose,
    c.status,
    c.provider_name,
    e.wan1_provider,
    e.wan1_speed,
    e.wan2_provider,
    e.wan2_speed,
    m.device_notes,
    m.wan1_arin_provider,
    m.wan2_arin_provider
FROM circuits c
LEFT JOIN enriched_circuits e ON c.site_name = e.network_name
LEFT JOIN meraki_inventory m ON c.site_name = m.network_name
WHERE c.site_name = 'AZP 08';
```

### Check Enablement History
```sql
-- Daily enablements (correct table)
SELECT 
    enablement_date,
    COUNT(*) as daily_count,
    STRING_AGG(site_id || ' (' || circuit_purpose || ')', ', ') as sites
FROM daily_enablements
WHERE enablement_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY enablement_date
ORDER BY enablement_date DESC;
```

### Find Manual Override Circuits
```sql
SELECT site_name, circuit_purpose, manual_override_date, manual_override_by
FROM circuits
WHERE manual_override = TRUE
ORDER BY manual_override_date DESC;
```

### Check Device Notes Format
```sql
-- Find sites with literal \n in notes
SELECT network_name, device_notes
FROM meraki_inventory
WHERE device_notes LIKE '%\\n%'
LIMIT 10;

-- Check enriched circuits column
SELECT network_name, wan1_provider, wan1_arin_org
FROM enriched_circuits
WHERE network_name = 'AZP 08';
```

## Known Issues & Gotchas

### 1. Site Name vs Network Name
**Issue:** Different tables use different column names for the same store identifier
- `circuits` table: `site_name`
- `meraki_inventory` table: `network_name`
- `enriched_circuits` table: `network_name`

**Solution:** Always check which column name to use when joining or updating

### 2. Device Notes Format
**Issue:** Notes may contain literal `\n` instead of actual newlines
- Correct: `"WAN 1\nCox Business\n300M"`
- Wrong: `"WAN 1\\nCox Business\\n300M"`

**Solution:** Use proper string formatting when storing notes

### 3. Enablement Table Confusion
**Issue:** Two tables track enablements, but only one is correct
- `daily_enablements` - CORRECT (Ready→Enabled only)
- `circuit_enablements` - INCORRECT (all status changes)

**Solution:** Always use `daily_enablements` for reporting

### 4. ARIN Provider Storage
**Issue:** ARIN data stored in multiple places
- `meraki_inventory`: `wan1_arin_provider`, `wan2_arin_provider`
- `enriched_circuits`: `wan1_arin_org`, `wan2_arin_org`

**Solution:** Keep both in sync during updates

### 5. Array vs String for Tags
**Issue:** Device tags stored differently
- `meraki_inventory.device_tags`: String (space-separated)
- `enriched_circuits.device_tags`: Array

**Solution:** Handle conversion when moving between tables

## Maintenance Commands

### Check Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Find Missing Indexes
```sql
-- Check for missing indexes on frequently queried columns
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND tablename IN ('circuits', 'meraki_inventory', 'enriched_circuits')
AND n_distinct > 100
ORDER BY tablename, n_distinct DESC;
```

### Vacuum and Analyze
```sql
-- Keep statistics up to date
VACUUM ANALYZE circuits;
VACUUM ANALYZE meraki_inventory;
VACUUM ANALYZE enriched_circuits;
```

---

## Additional Tables Summary

### Remaining Tables (29 of 68 total)

**Backup/Test Tables (5):**
- `device_notes_backup` (1,047 rows) - Backup of device notes
- `enriched_circuits_backup_20250627` (1,294 rows) - Backup table from June 27, 2025
- `enriched_circuits_backup_20250627_v2` (1,384 rows) - Second backup from June 27, 2025
- `enriched_circuits_test` (1,304 rows) - Test table for enriched circuits
- `snmp_test_results` (0 rows) - SNMP testing results

**Hardware Collection Tables (6):**
- `collected_fex_modules` (12 rows) - FEX module collection
- `collected_raw_inventory` (3 rows) - Raw inventory collection
- `hardware_components` (2 rows) - Hardware component data
- `inventory_collections` (9 rows) - Collection metadata
- `inventory_collection_history` (2 rows) - Collection history
- `nexus_fex_relationships` (2 rows) - Nexus FEX relationships

**Network Analysis Tables (4):**
- `enriched_networks` (1,239 rows) - Network enrichment data
- `network_devices` (84 rows) - Network device list
- `nexus_vdc_mapping` (16 rows) - VDC mapping
- `sfp_modules` (89 rows) - SFP module inventory

**Security/Access Tables (2):**
- `device_snmp_credentials` (68 rows) - SNMP credentials
- `snmp_credentials` (6 rows) - SNMP credential store

**System/Maintenance Tables (12):**
- `api_performance` (0 rows) - API performance metrics
- `cellular_carrier_detection` (0 rows) - Cellular carrier detection
- `corporate_eol` (32 rows) - Corporate EOL data
- `device_inventory` (0 rows) - Device inventory (empty)
- `enrichment_change_log` (2 rows) - Enrichment change log
- `eol_tracker_state` (4 rows) - EOL tracker state
- `firewall_rule_revisions` (0 rows) - Firewall rule revisions
- `l7_firewall_rules` (0 rows) - Layer 7 firewall rules
- `one_to_one_nat_rules` (0 rows) - 1:1 NAT rules
- `port_forwarding_rules` (0 rows) - Port forwarding rules
- `collected_fans` (0 rows) - Fan collection data
- `collected_power_supplies` (0 rows) - Power supply collection

### Database Views (12 total)
- `device_inventory_summary` - Device inventory summary
- `dhcp_relay_servers` - DHCP relay servers
- `latest_inventory` - Latest inventory data
- `latest_working_snmp_credentials` - Working SNMP credentials
- `network_grouping_by_subnet` - Network grouping by subnet
- `network_parent_mapping` - Network parent mapping
- `network_pattern_analysis` - Network pattern analysis
- `sites_by_16_network` - Sites by /16 network
- `snmp_credentials_list` - SNMP credentials list
- `v_circuit_summary` - Circuit summary view
- `v_enriched_circuits_complete_test` - Complete enriched circuits test
- `vlan_dhcp_summary` - VLAN DHCP summary

---

**Last Updated:** 2025-01-08  
**Version:** 3.0  
**Enhancements:** 
- Added 39 fully documented tables (57% coverage)
- Documented 9 additional major tables with detailed schemas
- Corrected actual table count: 68 tables + 12 views = 80 database objects
- Added remaining 29 tables summary
- Comprehensive SQL query documentation for all nightly scripts and Flask routes  
**Total Database Objects:** 80 (68 tables + 12 views)  
**Documented Tables:** 39 of 68 (57% coverage)  
**Tables with Data:** 50 of 68 (74% have data)  
**Next Review:** When adding new tables or modifying schema