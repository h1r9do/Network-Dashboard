# SNMP Data Collection and Processing Pipeline Documentation

## Overview
The SNMP inventory collection system is designed to collect hardware inventory from network devices, process and enhance the data with proper model identification, and import it into the database for web display.

## Data Collection Pipeline

### 1. **Primary Collection Scripts**

#### `nightly_snmp_inventory_collection.py`
- **Purpose**: Main SNMP collection script that runs nightly
- **Function**: Collects raw SNMP data from devices using encrypted credentials
- **Output**: Raw SNMP data stored in database
- **Key Features**:
  - Uses multiprocessing for parallel collection
  - Encrypted credential management
  - Stores results in PostgreSQL

#### `nightly_snmp_inventory_enhanced.py`
- **Purpose**: Enhanced version with FEX model extraction and SFP identification
- **Key Features**:
  - FEX pattern matching for model extraction (N2K-C2232PP-10GE, N2K-C2248TP-1GE, etc.)
  - SFP description to model mapping (GLC-SX-MMD, SFP-10G-SR, etc.)
  - Vendor identification by serial prefix

### 2. **Data Processing and Enhancement**

#### `nightly_snmp_inventory_web_format.py` / `nightly_snmp_inventory_web_format_v2.py`
- **Purpose**: Processes collected data for web display format
- **Key Processing**:
  - VDC consolidation (7K devices appear once)
  - FEX model extraction from descriptive text
  - SFP identification and vendor mapping
  - Hierarchical structure creation (master devices with components)

#### Model Enhancement Rules:
```python
# FEX Pattern Matching
- "48x1GE.*4x10GE.*N2K-C2248TP" → "N2K-C2248TP-1GE"
- "32x10GE.*8x10GE.*N2K-C2232PP" → "N2K-C2232PP-10GE"
- "16x10GE.*8x10GE.*N2K-B22" → "N2K-B22DELL-P"

# SFP Model Mapping
- "1000BaseSX SFP" → "GLC-SX-MMD"
- "SFP-10Gbase-SR" → "SFP-10G-SR"
- "SFP+ 10GBASE-LR" → "SFP-10G-LR"

# Vendor Identification by Serial Prefix
- "AGM/AGS" → "Avago"
- "FNS" → "Finisar"
- "MTC" → "MikroTik"
```

### 3. **CSV Generation Scripts**

#### `generate_ultimate_final_csv.py`
- **Purpose**: Creates the final CSV with all enhancements
- **Input**: `physical_inventory_consolidated.json`
- **Output**: `inventory_ultimate_final.csv`
- **Features**:
  - VDC consolidation
  - No duplicate serials
  - FEX model extraction
  - SFP identification
  - Hierarchical structure (master devices with empty components)

#### CSV Format:
```csv
hostname,ip_address,position,model,serial_number,port_location,vendor,notes
ALA-3130-Rack3-ENC3-A.dtc_phx.com,10.101.255.120,Standalone,WS-CBS3130X-S,FOC1420H01S,,,
,,Module,800-27645-02,FDO141815M2,Switch 1 - Slot 1 - TwinGig Converter Module,,
```

### 4. **Database Import Scripts**

#### `import_consolidated_inventory.py`
- **Purpose**: Imports processed data into PostgreSQL
- **Tables Updated**:
  - `comprehensive_device_inventory` - Full SNMP collection data
  - `inventory_web_format` - Web display format from CSV
- **Note**: Currently tries to use wrong database (`network_inventory` vs `dsrcircuits`)

### 5. **Data Flow Summary**

```
1. SNMP Collection (nightly_snmp_inventory_collection.py)
   ↓
2. Data Enhancement (nightly_snmp_inventory_enhanced.py)
   ↓
3. Web Format Processing (nightly_snmp_inventory_web_format.py)
   ↓
4. JSON Files Created:
   - physical_inventory_consolidated.json
   - physical_inventory_deduplicated.json
   ↓
5. CSV Generation (generate_ultimate_final_csv.py)
   → inventory_ultimate_final.csv (549 records)
   ↓
6. Database Import (import_consolidated_inventory.py)
   → inventory_web_format table
```

## Current Issues

1. **Missing EOL/EOS Data**: The CSV doesn't include EOL dates, needs to be joined with `corporate_eol` table
2. **Database Mismatch**: Import script uses wrong database connection
3. **Incomplete Import**: CSV has 549 records but `inventory_web_format` has 1896 (includes other data)
4. **Model Number Issues**: FEX devices show descriptive text instead of clean model numbers in some cases

## Required Fixes

1. Update `get_datacenter_inventory()` to use proper data source with EOL joins
2. Fix import script to use correct database
3. Ensure nightly process runs complete pipeline
4. Add EOL data enhancement during processing or at display time

## Nightly Process Orchestration

### Master Script: `run_nightly_inventory_complete.py`
Runs two scripts in sequence:
1. `nightly_snmp_inventory_collection_final.py` - SNMP collection
2. `nightly_snmp_inventory_web_format_v2.py` - Web format processing

### Web Format Processing (`nightly_snmp_inventory_web_format_v2.py`)
- **Input**: Reads from `comprehensive_device_inventory` table
- **Processing**:
  - Site determination from hostname/IP patterns
  - Hierarchical structure creation (parent device + components)
  - Component processing:
    - Modules (line cards, supervisors)
    - FEX units (Fabric Extenders)
    - SFPs/Transceivers
    - Stack members (Master/Slave)
- **Output**: Writes to `inventory_web_format` table with:
  - `parent_hostname` field maintained for all rows
  - `row_order` for hierarchical display
  - `site` field based on IP/hostname patterns

### Data Structure in Database
```sql
inventory_web_format:
- hostname (empty for components)
- ip_address (empty for components)
- parent_hostname (always populated - self for master, parent for components)
- relationship (Standalone, Master, Component, Slave)
- position (Module, FEX-101, SFP, etc.)
- model
- serial_number
- site
- row_order (for hierarchical display)
```

## Key Processing Rules

### Site Determination
- IP-based: 10.0.x → Scottsdale, 10.101.x → Alameda, 10.44.x → Equinix
- Hostname-based: ALA-* → Alameda, MDF-* → Scottsdale

### Component Hierarchy
1. Master device (has hostname and IP)
2. Components (no hostname/IP, linked by parent_hostname):
   - Modules
   - FEX units
   - SFPs
   - Stack slaves

### Model Enhancement (Not currently in v2)
The enhancement logic exists in other scripts but is not applied in v2:
- FEX model extraction from descriptive text
- SFP model identification from description
- Vendor identification from serial prefix