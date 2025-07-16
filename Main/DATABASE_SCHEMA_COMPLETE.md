# Complete Database Schema Documentation

**Total Tables:** 68  
**Total Views:** 12  
**Database:** dsrcircuits (PostgreSQL)  
**Last Updated:** July 8, 2025

## Table of Contents

1. [Priority Tables (High Volume)](#priority-tables-high-volume)
2. [Collected_* Tables](#collected_-tables)
3. [Device_* Tables](#device_-tables)
4. [Network_* Tables](#network_-tables)
5. [SNMP_* Tables](#snmp_-tables)
6. [Circuit Management Tables](#circuit-management-tables)
7. [EOL Tracking Tables](#eol-tracking-tables)
8. [Inventory Tables](#inventory-tables)
9. [Firewall and Security Tables](#firewall-and-security-tables)
10. [Performance and Monitoring Tables](#performance-and-monitoring-tables)
11. [Other Tables](#other-tables)
12. [Database Views](#database-views)

---

## Priority Tables (High Volume)

### comprehensive_device_inventory (169 rows)
**Purpose:** Stores comprehensive device inventory data collected via SNMP
```sql
id                   INTEGER NOT NULL PRIMARY KEY (auto-increment)
hostname             VARCHAR(255) NOT NULL
ip_address           INET NOT NULL
collection_timestamp TIMESTAMP NOT NULL
system_info          JSONB NULL
physical_components  JSONB NULL
interfaces           JSONB NULL
environmental_data   JSONB NULL
cisco_specific       JSONB NULL
stack_info           JSONB NULL
summary              JSONB NULL
created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### corporate_eol (32 rows)
**Purpose:** Tracks corporate-wide End-of-Life information for network equipment
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
model             VARCHAR(100) NOT NULL
vendor            VARCHAR(50) NULL
device_type       VARCHAR(50) NULL
category          VARCHAR(100) NULL
total_devices     INTEGER DEFAULT 0
announcement_date DATE NULL
end_of_sale_date  DATE NULL
end_of_support_date DATE NULL
source            VARCHAR(50) DEFAULT 'excel_import'
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### datacenter_inventory (225 rows)
**Purpose:** Maintains inventory of datacenter network devices
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
site              VARCHAR(100) NULL
hostname          VARCHAR(100) NULL
vendor            VARCHAR(50) NULL
mgmt_ip           VARCHAR(45) NULL
device_type       VARCHAR(50) NULL
model             VARCHAR(100) NULL
software_version  VARCHAR(200) NULL
serial_number     VARCHAR(100) NULL
announcement_date DATE NULL
end_of_sale_date  DATE NULL
end_of_support_date DATE NULL
source            VARCHAR(50) DEFAULT 'excel_import'
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### device_access (168 rows)
**Purpose:** Stores device access credentials and methods
```sql
id                     INTEGER NOT NULL PRIMARY KEY (auto-increment)
hostname               VARCHAR(255) NOT NULL
mgmt_ip                VARCHAR(50) NOT NULL
access_method          VARCHAR(20) NOT NULL
username               VARCHAR(100) NULL
password               VARCHAR(255) NULL
snmp_community         VARCHAR(100) NULL
snmp_version           VARCHAR(10) NULL
ssh_port               INTEGER DEFAULT 22
enable_password        VARCHAR(255) NULL
last_successful_access TIMESTAMP NULL
last_failed_access     TIMESTAMP NULL
failure_count          INTEGER DEFAULT 0
notes                  TEXT NULL
created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### device_components (22,973 rows)
**Purpose:** Detailed hardware component inventory from devices
```sql
id                  INTEGER NOT NULL PRIMARY KEY (auto-increment)
hostname            VARCHAR(255) NOT NULL
ip_address          INET NOT NULL
component_index     VARCHAR(50) NOT NULL
component_class     VARCHAR(50) NULL
description         TEXT NULL
serial_number       VARCHAR(255) NULL
model_name          VARCHAR(255) NULL
manufacturer        VARCHAR(255) NULL
hardware_revision   VARCHAR(100) NULL
firmware_revision   VARCHAR(100) NULL
software_revision   VARCHAR(100) NULL
physical_name       VARCHAR(255) NULL
asset_id            VARCHAR(100) NULL
is_fru              BOOLEAN NULL
collection_timestamp TIMESTAMP NOT NULL
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### ip_assignment_history (3,912 rows)
**Purpose:** Tracks IP address assignments and changes for WAN interfaces
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
site_name        VARCHAR(100) NOT NULL
wan1_ip          VARCHAR(45) NULL
wan2_ip          VARCHAR(45) NULL
snapshot_date    TIMESTAMP NOT NULL
ip_flip_detected BOOLEAN DEFAULT false
flip_handled     BOOLEAN DEFAULT false
created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Collected_* Tables

### collected_chassis (1,312 rows)
**Purpose:** Chassis information collected from network devices
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
name           VARCHAR(255) NULL
description    TEXT NULL
pid            VARCHAR(100) NULL
vid            VARCHAR(50) NULL
serial_number  VARCHAR(100) NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_fans (0 rows)
**Purpose:** Fan module information from network devices
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
name           VARCHAR(255) NULL
description    TEXT NULL
pid            VARCHAR(100) NULL
serial_number  VARCHAR(100) NULL
status         VARCHAR(50) NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_fex_modules (12 rows)
**Purpose:** Fabric Extender (FEX) module information
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id    INTEGER NULL
parent_hostname  VARCHAR(255) NOT NULL
fex_number       VARCHAR(10) NULL
fex_hostname     VARCHAR(255) NULL
description      TEXT NULL
model            VARCHAR(100) NULL
serial_number    VARCHAR(100) NULL
extender_serial  VARCHAR(100) NULL
state            VARCHAR(50) NULL
created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_modules (1,501 rows)
**Purpose:** Network device module inventory
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
module_number  VARCHAR(50) NULL
module_name    VARCHAR(255) NULL
module_type    VARCHAR(100) NULL
model          VARCHAR(100) NULL
serial_number  VARCHAR(100) NULL
status         VARCHAR(50) NULL
ports          INTEGER NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_power_supplies (0 rows)
**Purpose:** Power supply information from devices
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
name           VARCHAR(255) NULL
description    TEXT NULL
pid            VARCHAR(100) NULL
serial_number  VARCHAR(100) NULL
status         VARCHAR(50) NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_raw_inventory (3 rows)
**Purpose:** Raw command output from inventory collection
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
command        VARCHAR(255) NULL
output         TEXT NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

### collected_sfps (1,643 rows)
**Purpose:** SFP module inventory
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_id  INTEGER NULL
hostname       VARCHAR(255) NOT NULL
interface      VARCHAR(100) NULL
sfp_type       VARCHAR(100) NULL
vendor         VARCHAR(100) NULL
part_number    VARCHAR(100) NULL
serial_number  VARCHAR(100) NULL
wavelength     VARCHAR(50) NULL
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- collection_id -> inventory_collections(id)
```

---

## Device_* Tables

### device_inventory (0 rows)
**Purpose:** General device inventory tracking
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
organization_name VARCHAR(200) NULL
device_serial     VARCHAR(50) NOT NULL
model             VARCHAR(50) NULL
network_id        VARCHAR(100) NULL
eol_announced     DATE NULL
end_of_sale       DATE NULL
end_of_support    DATE NULL
last_seen         TIMESTAMP NULL
created_at        TIMESTAMP DEFAULT now()
```

### device_notes_backup (1,047 rows)
**Purpose:** Backup of device notes before modifications
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_serial    VARCHAR(50) NOT NULL
network_name     VARCHAR(100) NULL
backup_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
original_notes   TEXT NULL
fixed_notes      TEXT NULL
backup_reason    VARCHAR(100) DEFAULT 'Test fix 5 devices'
restored         BOOLEAN DEFAULT false
```

### device_snmp_credentials (68 rows)
**Purpose:** SNMP credentials for device access
```sql
id                      INTEGER NOT NULL PRIMARY KEY (auto-increment)
hostname                VARCHAR(255) NOT NULL
ip_address              VARCHAR(50) NOT NULL
snmp_version            VARCHAR(10) NOT NULL
snmp_community          VARCHAR(255) NULL
snmp_v3_username        VARCHAR(255) NULL
snmp_v3_auth_protocol   VARCHAR(50) NULL
snmp_v3_auth_password   VARCHAR(255) NULL
snmp_v3_priv_protocol   VARCHAR(50) NULL
snmp_v3_priv_password   VARCHAR(255) NULL
snmp_v3_security_level  VARCHAR(50) NULL
snmp_port               INTEGER DEFAULT 161
snmp_timeout            INTEGER DEFAULT 10
snmp_retries            INTEGER DEFAULT 3
working                 BOOLEAN DEFAULT false
last_tested             TIMESTAMP NULL
last_success            TIMESTAMP NULL
system_description      TEXT NULL
created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Network_* Tables

### network_devices (84 rows)
**Purpose:** Network device inventory from SSH/SNMP collection
```sql
id                   INTEGER NOT NULL PRIMARY KEY (auto-increment)
ip_address           VARCHAR(45) NOT NULL
hostname             VARCHAR(100) NULL
collection_timestamp TIMESTAMP NULL
data_source          VARCHAR(50) DEFAULT 'ssh_inventory'
device_type          VARCHAR(50) NULL
interfaces_count     INTEGER DEFAULT 0
created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### network_dhcp_options (0 rows)
**Purpose:** DHCP options configuration for network VLANs
```sql
id         INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id VARCHAR(50) NOT NULL
vlan_id    INTEGER NOT NULL
code       INTEGER NOT NULL
type       VARCHAR(50) NULL
value      TEXT NULL

Foreign Keys:
- network_id, vlan_id -> network_vlans(network_id, vlan_id)
```

### network_vlans (4,863 rows)
**Purpose:** VLAN configuration for Meraki networks
```sql
id                        INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id                VARCHAR(50) NOT NULL
network_name              VARCHAR(100) NULL
vlan_id                   INTEGER NOT NULL
name                      VARCHAR(100) NULL
appliance_ip              VARCHAR(50) NULL
subnet                    VARCHAR(50) NULL
subnet_mask               VARCHAR(50) NULL
dhcp_handling             VARCHAR(50) NULL
dhcp_lease_time           VARCHAR(20) NULL
dhcp_boot_options_enabled BOOLEAN DEFAULT false
dhcp_boot_next_server     VARCHAR(50) NULL
dhcp_boot_filename        VARCHAR(255) NULL
dhcp_relay_server_ips     TEXT NULL
dns_nameservers           TEXT NULL
reserved_ip_ranges        TEXT NULL
fixed_ip_assignments      TEXT NULL
updated_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
parent_network            CIDR NULL
```

### network_wan_ports (0 rows)
**Purpose:** WAN port configuration for network devices
```sql
id                        INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id                VARCHAR(50) NOT NULL
network_name              VARCHAR(100) NULL
port_number               INTEGER NOT NULL
enabled                   BOOLEAN DEFAULT true
wan_enabled               BOOLEAN DEFAULT true
access_policy             VARCHAR(50) NULL
vlan                      INTEGER NULL
allowed_vlans             TEXT NULL
udld                      VARCHAR(50) NULL
link_negotiation          VARCHAR(50) NULL
poe_enabled               BOOLEAN DEFAULT false
peer_sgt_capable          BOOLEAN DEFAULT false
flexible_stacking_enabled BOOLEAN DEFAULT false
dai_trusted               BOOLEAN DEFAULT false
profile                   TEXT NULL
updated_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## SNMP_* Tables

### snmp_credentials (6 rows)
**Purpose:** Centralized SNMP credential storage
```sql
id                      INTEGER NOT NULL PRIMARY KEY (auto-increment)
credential_name         VARCHAR(50) NOT NULL
credential_type         VARCHAR(10) NOT NULL
community_encrypted     BYTEA NULL
username_encrypted      BYTEA NULL
auth_protocol           VARCHAR(10) NULL
auth_password_encrypted BYTEA NULL
priv_protocol           VARCHAR(10) NULL
priv_password_encrypted BYTEA NULL
description             TEXT NULL
created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
is_active               BOOLEAN DEFAULT true
```

### snmp_test_results (0 rows)
**Purpose:** SNMP connectivity test results
```sql
id                 INTEGER NOT NULL PRIMARY KEY (auto-increment)
hostname           VARCHAR(255) NOT NULL
ip_address         VARCHAR(50) NOT NULL
snmp_version       VARCHAR(10) NOT NULL
snmp_community     VARCHAR(255) NULL
snmp_v3_username   VARCHAR(255) NULL
test_timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
success            BOOLEAN NOT NULL
response_time_ms   DOUBLE PRECISION NULL
error_message      TEXT NULL
system_description TEXT NULL
system_uptime      BIGINT NULL
system_name        VARCHAR(255) NULL
system_location    VARCHAR(255) NULL
system_contact     VARCHAR(255) NULL
entity_count       INTEGER NULL
```

---

## Circuit Management Tables

### circuits (2,697 rows)
**Purpose:** Main circuit tracking table
```sql
id                             INTEGER NOT NULL PRIMARY KEY (auto-increment)
record_number                  VARCHAR(50) NULL
site_name                      VARCHAR(100) NOT NULL
site_id                        VARCHAR(50) NULL
circuit_purpose                VARCHAR(50) NULL
status                         VARCHAR(100) NULL
substatus                      VARCHAR(100) NULL
provider_name                  VARCHAR(100) NULL
details_service_speed          VARCHAR(100) NULL
details_ordered_service_speed  VARCHAR(100) NULL
billing_monthly_cost           NUMERIC(10,2) NULL
ip_address_start               VARCHAR(45) NULL
date_record_updated            TIMESTAMP NULL
milestone_service_activated    TIMESTAMP NULL
assigned_to                    VARCHAR(100) NULL
sctask                         VARCHAR(50) NULL
created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
data_source                    VARCHAR(50) DEFAULT 'csv_import'
address_1                      VARCHAR(200) NULL
city                           VARCHAR(100) NULL
state                          VARCHAR(10) NULL
zipcode                        VARCHAR(20) NULL
primary_contact_name           VARCHAR(100) NULL
primary_contact_email          VARCHAR(100) NULL
billing_install_cost           NUMERIC(10,2) NULL
milestone_enabled              TIMESTAMP NULL
target_enablement_date         DATE NULL
details_provider               VARCHAR(100) NULL
details_provider_phone         VARCHAR(50) NULL
billing_account                VARCHAR(100) NULL
fingerprint                    VARCHAR(255) NULL
last_csv_file                  VARCHAR(100) NULL
target_service_activation_date DATE NULL
order_status                   VARCHAR(100) NULL
jeopardy                       VARCHAR(50) NULL
attention_required             VARCHAR(10) NULL
project_type                   VARCHAR(100) NULL
circuit_type                   VARCHAR(100) NULL
phase                          VARCHAR(50) NULL
order_number_provider          VARCHAR(100) NULL
manual_override                BOOLEAN DEFAULT false
manual_override_date           TIMESTAMP NULL
manual_override_by             VARCHAR(100) NULL
notes                          TEXT NULL
```

### circuit_history (692 rows)
**Purpose:** Tracks changes to circuit records
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
circuit_id      INTEGER NULL
change_date     DATE NOT NULL
change_type     VARCHAR(50) NULL
field_changed   VARCHAR(100) NULL
old_value       TEXT NULL
new_value       TEXT NULL
csv_file_source VARCHAR(100) NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- circuit_id -> circuits(id)
```

### circuit_assignments (8 rows)
**Purpose:** Manual circuit assignments to technicians
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
site_name       VARCHAR(100) NOT NULL
sctask          VARCHAR(50) NULL
assigned_to     VARCHAR(100) NULL
assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
status          VARCHAR(50) DEFAULT 'active'
notes           TEXT NULL
created_by      VARCHAR(100) NULL
site_id         VARCHAR(100) NULL
circuit_purpose VARCHAR(100) NULL
sctask_number   VARCHAR(50) NULL
sctask_sys_id   VARCHAR(100) NULL
updated_by      VARCHAR(100) DEFAULT 'system'
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### circuit_enablements (723 rows)
**Purpose:** Tracks circuit enablement events
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
site_name        VARCHAR(200) NULL
circuit_purpose  VARCHAR(100) NULL
provider_name    VARCHAR(100) NULL
enablement_date  DATE NULL
previous_status  VARCHAR(100) NULL
current_status   VARCHAR(100) NULL
service_speed    VARCHAR(50) NULL
monthly_cost     NUMERIC(10,2) NULL
detected_at      TIMESTAMP NULL
```

### daily_enablements (41 rows)
**Purpose:** Daily circuit enablement tracking
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
date             DATE NULL
site_name        VARCHAR(200) NULL
circuit_purpose  VARCHAR(100) NULL
provider_name    VARCHAR(100) NULL
service_speed    VARCHAR(50) NULL
monthly_cost     NUMERIC(10,2) NULL
previous_status  VARCHAR(100) NULL
current_status   VARCHAR(100) NULL
assigned_to      VARCHAR(100) NULL
sctask           VARCHAR(50) NULL
created_at       TIMESTAMP DEFAULT now()
record_number    VARCHAR(50) NULL
site_id          VARCHAR(50) NULL
```

### enablement_summary (53 rows)
**Purpose:** Aggregated enablement statistics
```sql
id           INTEGER NOT NULL PRIMARY KEY (auto-increment)
summary_date DATE NULL
daily_count  INTEGER NULL
created_at   TIMESTAMP DEFAULT now()
```

### enablement_trends (14 rows)
**Purpose:** Enablement trend analysis
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
period_type      VARCHAR(20) NULL
period_start     DATE NULL
period_end       DATE NULL
enablement_count INTEGER NULL
created_at       TIMESTAMP DEFAULT now()
```

### enriched_circuits (1,323 rows)
**Purpose:** Enriched circuit data with provider details
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_name      VARCHAR(255) NOT NULL
device_tags       ARRAY NULL
wan1_provider     VARCHAR(255) NULL
wan1_speed        VARCHAR(100) NULL
wan1_circuit_role VARCHAR(50) DEFAULT 'Primary'
wan1_confirmed    BOOLEAN DEFAULT false
wan2_provider     VARCHAR(255) NULL
wan2_speed        VARCHAR(100) NULL
wan2_circuit_role VARCHAR(50) DEFAULT 'Secondary'
wan2_confirmed    BOOLEAN DEFAULT false
last_updated      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
pushed_to_meraki  BOOLEAN DEFAULT false
pushed_date       TIMESTAMP NULL
wan1_ip           VARCHAR(45) NULL
wan2_ip           VARCHAR(45) NULL
wan1_arin_org     VARCHAR(200) NULL
wan2_arin_org     VARCHAR(200) NULL
```

### enriched_networks (1,239 rows)
**Purpose:** Network enrichment data
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_serial     VARCHAR(50) NOT NULL
network_name      VARCHAR(100) NULL
site_name         VARCHAR(100) NULL
status            VARCHAR(100) NULL
provider_name     VARCHAR(100) NULL
circuit_purpose   VARCHAR(100) NULL
service_speed     VARCHAR(50) NULL
monthly_cost      NUMERIC(10,2) NULL
date_record_updated VARCHAR(50) NULL
ip_address_start  VARCHAR(45) NULL
last_enriched     TIMESTAMP NULL
created_at        TIMESTAMP DEFAULT now()
```

### enrichment_change_log (2 rows)
**Purpose:** Logs changes during enrichment process
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
site_name     VARCHAR(100) NOT NULL
change_type   VARCHAR(50) NULL
wan_affected  VARCHAR(10) NULL
field_changed VARCHAR(100) NULL
old_value     TEXT NULL
new_value     TEXT NULL
change_reason TEXT NULL
change_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### enrichment_change_tracking (1,322 rows)
**Purpose:** Tracks enrichment process changes
```sql
network_name           VARCHAR(255) NOT NULL PRIMARY KEY
last_device_notes_hash VARCHAR(64) NULL
last_wan1_ip           VARCHAR(45) NULL
last_wan2_ip           VARCHAR(45) NULL
last_enrichment_run    TIMESTAMP NULL
dsr_circuits_hash      VARCHAR(64) NULL
```

---

## EOL Tracking Tables

### eol_tracker_state (4 rows)
**Purpose:** Tracks EOL information update state
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
last_page_hash  VARCHAR(64) NULL
last_csv_hash   VARCHAR(64) NULL
last_check_time TIMESTAMP NULL
pdf_inventory   JSONB NULL
created_at      TIMESTAMP DEFAULT now()
updated_at      TIMESTAMP DEFAULT now()
```

### meraki_eol (0 rows)
**Purpose:** Meraki EOL information (deprecated)
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
model             VARCHAR(100) NOT NULL
announcement_date DATE NULL
end_of_sale       DATE NULL
end_of_support    DATE NULL
source            VARCHAR(50) NULL
pdf_url           VARCHAR(500) NULL
pdf_name          VARCHAR(200) NULL
confidence        VARCHAR(20) NULL
created_at        TIMESTAMP DEFAULT now()
updated_at        TIMESTAMP DEFAULT now()
```

### meraki_eol_enhanced (424 rows)
**Purpose:** Enhanced Meraki EOL tracking
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
model             VARCHAR(50) NOT NULL
announcement_date DATE NULL
end_of_sale       DATE NULL
end_of_support    DATE NULL
source            VARCHAR(100) NULL
method            VARCHAR(50) NULL
updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
confidence        VARCHAR(20) DEFAULT 'high'
```

### meraki_eol_pdf (650 rows)
**Purpose:** EOL data extracted from PDF documents
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
model             VARCHAR(100) NOT NULL
model_family      VARCHAR(100) NULL
announcement_date DATE NULL
end_of_sale       DATE NULL
end_of_support    DATE NULL
source_pdf        VARCHAR(200) NULL
pdf_url           VARCHAR(500) NULL
pdf_hash          VARCHAR(64) NULL
extracted_text    TEXT NULL
confidence        VARCHAR(20) DEFAULT 'high'
created_at        TIMESTAMP DEFAULT now()
updated_at        TIMESTAMP DEFAULT now()
```

### netdisco_eol_mapping (102 rows)
**Purpose:** Maps Netdisco models to EOL data
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
vendor            VARCHAR(100) NULL
model             VARCHAR(200) NOT NULL
normalized_model  VARCHAR(200) NULL
device_type       VARCHAR(50) NULL
announcement_date DATE NULL
end_of_sale       DATE NULL
end_of_support    DATE NULL
source            VARCHAR(50) NULL
last_updated      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
notes             TEXT NULL
```

---

## Inventory Tables

### inventory_collections (9 rows)
**Purpose:** Tracks inventory collection runs
```sql
id                 INTEGER NOT NULL PRIMARY KEY (auto-increment)
collection_date    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
total_devices      INTEGER NOT NULL
successful_devices INTEGER NOT NULL
collection_type    VARCHAR(50) NULL
notes              TEXT NULL
created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### inventory_devices (13,092 rows)
**Purpose:** Device inventory from various sources
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
serial        VARCHAR(50) NOT NULL
model         VARCHAR(50) NOT NULL
organization  VARCHAR(100) NOT NULL
network_id    VARCHAR(50) NULL
network_name  VARCHAR(100) NULL
name          VARCHAR(100) NULL
mac           VARCHAR(20) NULL
lan_ip        VARCHAR(45) NULL
firmware      VARCHAR(50) NULL
product_type  VARCHAR(50) NULL
tags          TEXT NULL
notes         TEXT NULL
details       TEXT NULL
```

### inventory_summary (65 rows)
**Purpose:** Aggregated inventory statistics
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
model             VARCHAR(50) NOT NULL
total_count       INTEGER DEFAULT 0
org_counts        TEXT NULL
announcement_date VARCHAR(20) NULL
end_of_sale       VARCHAR(20) NULL
end_of_support    VARCHAR(20) NULL
highlight         VARCHAR(20) NULL
```

### meraki_inventory (1,330 rows)
**Purpose:** Meraki-specific device inventory
```sql
id                      INTEGER NOT NULL PRIMARY KEY (auto-increment)
organization_name       VARCHAR(255) NULL
network_id              VARCHAR(100) NULL
network_name            VARCHAR(255) NULL
device_serial           VARCHAR(100) NULL
device_model            VARCHAR(100) NULL
device_name             VARCHAR(255) NULL
device_tags             ARRAY NULL
last_updated            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
wan1_ip                 VARCHAR(45) NULL
wan2_ip                 VARCHAR(45) NULL
wan1_assignment         VARCHAR(20) NULL
wan2_assignment         VARCHAR(20) NULL
wan1_arin_provider      VARCHAR(100) NULL
wan2_arin_provider      VARCHAR(100) NULL
wan1_provider_comparison VARCHAR(20) NULL
wan2_provider_comparison VARCHAR(20) NULL
wan1_provider_label     VARCHAR(255) NULL
wan1_speed_label        VARCHAR(100) NULL
wan2_provider_label     VARCHAR(255) NULL
wan2_speed_label        VARCHAR(100) NULL
device_notes            TEXT NULL
```

### meraki_live_data (60 rows)
**Purpose:** Real-time Meraki data snapshot
```sql
id                       INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_name             VARCHAR(255) NOT NULL
network_id               VARCHAR(100) NULL
device_serial            VARCHAR(100) NULL
device_model             VARCHAR(50) NULL
device_name              VARCHAR(255) NULL
device_tags              TEXT NULL
wan1_provider_label      VARCHAR(255) NULL
wan1_speed               VARCHAR(100) NULL
wan1_ip                  VARCHAR(45) NULL
wan1_provider            VARCHAR(255) NULL
wan1_provider_comparison VARCHAR(50) NULL
wan2_provider_label      VARCHAR(255) NULL
wan2_speed               VARCHAR(100) NULL
wan2_ip                  VARCHAR(45) NULL
wan2_provider            VARCHAR(255) NULL
wan2_provider_comparison VARCHAR(50) NULL
raw_notes                TEXT NULL
last_updated             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### netdisco_inventory_summary (29 rows)
**Purpose:** Summary of Netdisco inventory
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
vendor           VARCHAR(100) NULL
model            VARCHAR(200) NULL
device_type      VARCHAR(50) NULL
logical_devices  INTEGER DEFAULT 0
physical_devices INTEGER DEFAULT 0
announcement_date DATE NULL
end_of_sale      DATE NULL
end_of_support   DATE NULL
last_updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Firewall and Security Tables

### firewall_rules (75,355 rows)
**Purpose:** Layer 3/4 firewall rules
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id        VARCHAR(100) NOT NULL
network_name      VARCHAR(100) NOT NULL
rule_order        INTEGER NOT NULL
comment           VARCHAR(500) NULL
policy            VARCHAR(20) NOT NULL
protocol          VARCHAR(20) NOT NULL
src_port          VARCHAR(100) NULL
src_cidr          TEXT NULL
dest_port         VARCHAR(100) NULL
dest_cidr         TEXT NULL
syslog_enabled    BOOLEAN NULL
rule_type         VARCHAR(20) NULL
is_template       BOOLEAN NULL
template_source   VARCHAR(100) NULL
created_at        TIMESTAMP NULL
updated_at        TIMESTAMP NULL
last_synced       TIMESTAMP NULL
revision_number   INTEGER DEFAULT 1
last_modified_by  VARCHAR(100) NULL
last_modified_at  TIMESTAMP DEFAULT now()
```

### firewall_deployment_log (0 rows)
**Purpose:** Tracks firewall rule deployments
```sql
id                   INTEGER NOT NULL PRIMARY KEY (auto-increment)
template_network_id  VARCHAR(100) NOT NULL
template_network_name VARCHAR(100) NOT NULL
target_network_id    VARCHAR(100) NOT NULL
target_network_name  VARCHAR(100) NOT NULL
deployment_type      VARCHAR(50) NOT NULL
rules_deployed       INTEGER NULL
deployment_status    VARCHAR(20) NOT NULL
error_message        TEXT NULL
deployed_by          VARCHAR(100) NULL
deployment_time      TIMESTAMP NULL
```

### firewall_rule_revisions (0 rows)
**Purpose:** Firewall rule version control
```sql
id                 INTEGER NOT NULL PRIMARY KEY (auto-increment)
template_source    VARCHAR(50) NOT NULL
rule_id            INTEGER NULL
revision_number    INTEGER NOT NULL
action             VARCHAR(20) NOT NULL
rule_order         INTEGER NULL
comment            TEXT NULL
policy             VARCHAR(10) NULL
protocol           VARCHAR(20) NULL
src_port           VARCHAR(100) NULL
src_cidr           TEXT NULL
dest_port          VARCHAR(100) NULL
dest_cidr          TEXT NULL
syslog_enabled     BOOLEAN NULL
changed_by         VARCHAR(100) NULL
changed_at         TIMESTAMP DEFAULT now()
change_description TEXT NULL
```

### l7_firewall_rules (0 rows)
**Purpose:** Layer 7 application firewall rules
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id      VARCHAR(100) NOT NULL
network_name    VARCHAR(100) NOT NULL
rule_order      INTEGER NOT NULL
policy          VARCHAR(20) NOT NULL
rule_type       VARCHAR(50) NULL
value           TEXT NULL
is_template     BOOLEAN NULL
template_source VARCHAR(100) NULL
created_at      TIMESTAMP NULL
updated_at      TIMESTAMP NULL
last_synced     TIMESTAMP NULL
```

### one_to_one_nat_rules (0 rows)
**Purpose:** 1:1 NAT mappings
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id      VARCHAR(100) NOT NULL
network_name    VARCHAR(100) NOT NULL
rule_order      INTEGER NOT NULL
name            VARCHAR(100) NULL
public_ip       VARCHAR(45) NULL
lan_ip          VARCHAR(45) NULL
uplink          VARCHAR(20) NULL
allowed_inbound ARRAY NULL
is_template     BOOLEAN NULL
template_source VARCHAR(100) NULL
created_at      TIMESTAMP NULL
updated_at      TIMESTAMP NULL
last_synced     TIMESTAMP NULL
```

### port_forwarding_rules (0 rows)
**Purpose:** Port forwarding configurations
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_id      VARCHAR(100) NOT NULL
network_name    VARCHAR(100) NOT NULL
rule_order      INTEGER NOT NULL
name            VARCHAR(100) NULL
protocol        VARCHAR(20) NOT NULL
public_port     VARCHAR(50) NULL
local_ip        VARCHAR(45) NULL
local_port      VARCHAR(50) NULL
allowed_ips     ARRAY NULL
uplink          VARCHAR(20) NULL
is_template     BOOLEAN NULL
template_source VARCHAR(100) NULL
created_at      TIMESTAMP NULL
updated_at      TIMESTAMP NULL
last_synced     TIMESTAMP NULL
```

---

## Performance and Monitoring Tables

### api_performance (0 rows)
**Purpose:** API endpoint performance metrics
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
endpoint      VARCHAR(255) NOT NULL
method        VARCHAR(10) NOT NULL
category      VARCHAR(50) NULL
response_time DOUBLE PRECISION NULL
status_code   INTEGER NULL
response_size INTEGER NULL
success       BOOLEAN NULL
error_message TEXT NULL
timestamp     TIMESTAMP NULL
```

### performance_metrics (2,352 rows)
**Purpose:** Detailed performance tracking
```sql
id                     INTEGER NOT NULL PRIMARY KEY (auto-increment)
endpoint_name          VARCHAR(255) NOT NULL
endpoint_method        VARCHAR(10) NULL
endpoint_params        TEXT NULL
query_execution_time_ms INTEGER NOT NULL
data_size_bytes        INTEGER NULL
data_rows_returned     INTEGER NULL
response_status        INTEGER NOT NULL
error_message          TEXT NULL
timestamp              TIMESTAMP NULL
module_category        VARCHAR(100) NULL
db_query_count         INTEGER NULL
cache_hit              BOOLEAN NULL
user_agent             VARCHAR(255) NULL
is_monitoring          BOOLEAN NULL
```

---

## Other Tables

### cellular_carrier_detection (0 rows)
**Purpose:** Cellular carrier identification
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
network_name     VARCHAR(255) NOT NULL
device_serial    VARCHAR(255) NOT NULL
wan_interface    VARCHAR(10) NOT NULL
private_ip       VARCHAR(45) NOT NULL
public_ip        VARCHAR(45) NULL
detected_carrier VARCHAR(255) NULL
detection_method VARCHAR(255) NULL
confidence_score INTEGER NULL
traceroute_hops  JSONB NULL
created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### chassis_blades (149 rows)
**Purpose:** Blade information for chassis-based switches
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_id     INTEGER NULL
module_number VARCHAR(10) NULL
ports         VARCHAR(10) NULL
card_type     VARCHAR(255) NULL
model         VARCHAR(100) NULL
serial_number VARCHAR(50) NULL
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- device_id -> network_devices(id)
```

### daily_summaries (865 rows)
**Purpose:** Daily processing summaries
```sql
id                       INTEGER NOT NULL PRIMARY KEY (auto-increment)
summary_date             DATE NOT NULL
total_circuits           INTEGER NULL
enabled_count            INTEGER NULL
ready_count              INTEGER NULL
customer_action_count    INTEGER NULL
construction_count       INTEGER NULL
planning_count           INTEGER NULL
csv_file_processed       VARCHAR(100) NULL
processing_time_seconds  NUMERIC(10,3) NULL
created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### hardware_components (2 rows)
**Purpose:** Hardware component tracking
```sql
id             INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_id      INTEGER NULL
name           VARCHAR(100) NULL
description    VARCHAR(255) NULL
pid            VARCHAR(50) NULL
vid            VARCHAR(50) NULL
serial_number  VARCHAR(50) NULL
component_type VARCHAR(50) DEFAULT 'SFP'
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- device_id -> network_devices(id)
```

### inventory_collection_history (2 rows)
**Purpose:** Tracks inventory collection attempts
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_id        INTEGER NULL
hostname         VARCHAR(255) NULL
collection_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
access_method    VARCHAR(20) NULL
status           VARCHAR(20) NULL
items_collected  INTEGER NULL
error_message    TEXT NULL
collection_data  JSONB NULL
```

### new_stores (133 rows)
**Purpose:** Tracks new store openings
```sql
id                       INTEGER NOT NULL PRIMARY KEY (auto-increment)
site_name                VARCHAR(100) NOT NULL
added_date               TIMESTAMP NULL
added_by                 VARCHAR(100) NULL
notes                    TEXT NULL
is_active                BOOLEAN NULL
meraki_network_found     BOOLEAN NULL
meraki_found_date        TIMESTAMP NULL
created_at               TIMESTAMP NULL
updated_at               TIMESTAMP NULL
target_opening_date      DATE NULL
target_opening_date_text VARCHAR(50) NULL
region                   VARCHAR(100) NULL
city                     VARCHAR(100) NULL
state                    VARCHAR(10) NULL
project_status           VARCHAR(100) NULL
```

### nexus_fex_relationships (2 rows)
**Purpose:** Nexus switch FEX relationships
```sql
id              INTEGER NOT NULL PRIMARY KEY (auto-increment)
parent_hostname VARCHAR(255) NOT NULL
parent_ip       VARCHAR(50) NULL
fex_number      INTEGER NOT NULL
fex_description VARCHAR(255) NULL
fex_model       VARCHAR(100) NULL
fex_serial      VARCHAR(100) NULL
fex_state       VARCHAR(50) NULL
ports           INTEGER NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### nexus_vdc_mapping (16 rows)
**Purpose:** Nexus Virtual Device Context mapping
```sql
id                INTEGER NOT NULL PRIMARY KEY (auto-increment)
physical_hostname VARCHAR(255) NOT NULL
vdc_hostname      VARCHAR(255) NOT NULL
vdc_context       VARCHAR(50) NULL
mgmt_ip           VARCHAR(50) NULL
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### provider_mappings (10 rows)
**Purpose:** Maps provider names to canonical names
```sql
id               INTEGER NOT NULL PRIMARY KEY (auto-increment)
original_name    VARCHAR(200) NULL
canonical_name   VARCHAR(100) NULL
mapping_type     VARCHAR(50) NULL
confidence_score NUMERIC(3,2) NULL
created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
network_id       VARCHAR(100) NULL
providers_flipped BOOLEAN NULL
```

### rdap_cache (2,378 rows)
**Purpose:** Caches RDAP (ARIN) lookup results
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
ip_address    VARCHAR(45) NOT NULL
provider_name VARCHAR(200) NULL
rdap_response JSONB NULL
last_queried  TIMESTAMP DEFAULT now()
created_at    TIMESTAMP DEFAULT now()
```

### ready_queue_daily (53 rows)
**Purpose:** Daily ready queue metrics
```sql
id           INTEGER NOT NULL PRIMARY KEY (auto-increment)
summary_date DATE NULL
ready_count  INTEGER DEFAULT 0
created_at   TIMESTAMP DEFAULT now()
```

### sfp_modules (89 rows)
**Purpose:** SFP module inventory
```sql
id           INTEGER NOT NULL PRIMARY KEY (auto-increment)
device_id    INTEGER NULL
interface    VARCHAR(100) NULL
module_type  VARCHAR(255) NULL
status       VARCHAR(50) NULL
product_id   VARCHAR(100) NULL
created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Foreign Keys:
- device_id -> network_devices(id)
```

### switch_port_clients (74,350 rows)
**Purpose:** Switch port client tracking
```sql
id            INTEGER NOT NULL PRIMARY KEY (auto-increment)
store_name    VARCHAR(100) NULL
switch_name   VARCHAR(100) NULL
switch_serial VARCHAR(50) NULL
port_id       VARCHAR(20) NULL
hostname      VARCHAR(200) NULL
ip_address    VARCHAR(45) NULL
mac_address   VARCHAR(17) NULL
vlan          INTEGER NULL
manufacturer  VARCHAR(100) NULL
description   TEXT NULL
last_seen     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Backup Tables

#### enriched_circuits_backup_20250627 (1,294 rows)
**Purpose:** Backup of enriched_circuits table from June 27, 2025

#### enriched_circuits_backup_20250627_v2 (1,384 rows)
**Purpose:** Second backup of enriched_circuits table from June 27, 2025

#### enriched_circuits_test (1,304 rows)
**Purpose:** Test version of enriched_circuits table

---

## Database Views

### device_inventory_summary
**Purpose:** Summarizes device inventory by hostname
```sql
SELECT hostname, module_count, sfp_count, fex_count, last_collected
FROM inventory_collections with collected_modules, collected_sfps, collected_fex_modules
GROUP BY hostname
```

### dhcp_relay_servers
**Purpose:** Extracts DHCP relay server configurations
```sql
SELECT network_id, network_name, vlan_id, vlan_name, relay_server_ip
FROM network_vlans
WHERE dhcp_handling = 'Relay DHCP to another server'
```

### latest_inventory
**Purpose:** Shows latest inventory collection data
```sql
SELECT chassis data FROM most recent successful inventory collection
```

### latest_working_snmp_credentials
**Purpose:** Latest working SNMP credentials per device
```sql
SELECT DISTINCT ON (hostname, ip_address) credentials
WHERE working = true
ORDER BY last_success DESC
```

### network_grouping_by_subnet
**Purpose:** Groups networks by parent subnet
```sql
Shows networks sharing same parent subnet, excluding hubs/voice/lab
```

### network_parent_mapping
**Purpose:** Maps networks to parent networks
```sql
Shows network to parent network relationships with VLAN details
```

### network_pattern_analysis
**Purpose:** Analyzes network IP patterns
```sql
Analyzes parent networks by site usage patterns
```

### sites_by_16_network
**Purpose:** Groups sites by /16 network blocks
```sql
Groups sites by /16 network blocks for IP management
```

### snmp_credentials_list
**Purpose:** Lists SNMP credentials (without passwords)
```sql
SELECT id, credential_name, credential_type, description, dates, is_active
FROM snmp_credentials
```

### v_circuit_summary
**Purpose:** Circuit summary with cost information
```sql
Joins enriched_circuits with circuits table for cost data
Excludes hubs, labs, voice networks
```

### v_enriched_circuits_complete_test
**Purpose:** Test view for complete enriched circuit data
```sql
Complex view joining enriched_circuits_test with meraki_inventory and circuits
Includes cost calculations and role assignments
```

### vlan_dhcp_summary
**Purpose:** Summarizes DHCP configuration by network
```sql
Counts VLANs by DHCP type (server/relay/disabled) per network
```

---

**Total Database Objects:** 80 (68 tables + 12 views)  
**Total Records:** ~250,000+ across all tables  
**Primary Data Categories:**
- Circuit Management
- Network Inventory
- EOL Tracking
- Security/Firewall Rules
- Performance Monitoring
- VLAN/DHCP Configuration