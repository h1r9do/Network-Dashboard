# Complete Inventory Processing Pipeline Documentation

## Overview
This document describes the complete inventory processing pipeline created on July 8, 2025, 
for processing SNMP-collected network device inventory data, applying enhancements, 
removing duplicates, and storing in the database for web display.

## Pipeline Architecture

```
SNMP Collection → JSON Files → Enhancement → Deduplication → CSV → Database → Web Display
```

## Detailed Pipeline Steps

### Step 1: SNMP Collection
**Script**: `/usr/local/bin/Main/nightly_snmp_inventory_collection_final.py`
- **Function**: Collects SNMP data from all network devices
- **Output**: 
  - JSON file: `/var/www/html/network-data/nightly_snmp_collection_{timestamp}.json`
  - Database: `comprehensive_device_inventory` table
- **Key Features**:
  - Collects physical inventory (chassis, modules, FEX, SFPs)
  - Stores raw SNMP data with full component hierarchy
  - Runs nightly at 2 AM via root cron

### Step 2: Web Format Generation
**Script**: `/usr/local/bin/Main/nightly_snmp_inventory_web_format_v2.py`
- **Function**: Converts raw SNMP data to hierarchical web format
- **Input**: `comprehensive_device_inventory` table
- **Output**: `inventory_web_format` table (but without enhancements)
- **Issue**: Does NOT apply model enhancements or deduplication

### Step 3: Model Enhancement
**Script**: `/usr/local/bin/Main/complete_inventory_enhancement.py`
- **Function**: Extracts clean model numbers from descriptions
- **Key Enhancements**:
  - FEX models: "Fabric Extender Module: 48x1GE..." → "N2K-C2248TP-1GE"
  - SFP identification: Maps descriptions to standard models
  - Module cleanup: Removes redundant text
- **Input**: `physical_inventory_stacks_output.json` (intermediate file)
- **Output**: `inventory_complete.csv`

### Step 4: VPC Deduplication
**Script**: `/usr/local/bin/Main/deduplicate_inventory_serials.py`
- **Function**: Removes duplicate components from VPC pairs
- **Logic**:
  - Identifies shared components (same serial on -01 and -02 switches)
  - Assigns shared resources only to -01 switch
  - Adds "shared_with" notation
- **Input**: JSON inventory data
- **Output**: `physical_inventory_deduplicated.json`

### Step 5: VDC Consolidation
**Script**: `/usr/local/bin/Main/consolidate_vdc_devices.py`
- **Function**: Consolidates Virtual Device Contexts
- **Process**: 
  - Combines multiple VDCs into single device entry
  - Preserves all modules and components
- **Output**: `inventory_consolidated_final.csv`

### Step 6: Final CSV Generation
**Script**: `/usr/local/bin/Main/generate_ultimate_final_csv.py`
- **Function**: Creates the final CSV with all enhancements
- **Features**:
  - VDC consolidation
  - No duplicate serials
  - FEX model extraction
  - SFP identification
- **Input**: Multiple JSON files from previous steps
- **Output**: `inventory_ultimate_final.csv` (548 rows)

### Step 7: Database Import
**Script**: `/usr/local/bin/Main/import_ultimate_final_inventory_to_db.py`
- **Function**: Imports the final CSV to database
- **Process**:
  - Clears existing `inventory_web_format` table
  - Imports with proper parent-child relationships
  - Validates no duplicate FEX devices
- **Output**: Updated `inventory_web_format` table

## Current Issues

1. **Disconnected Pipeline**: Steps run independently, not as a unified process
2. **Intermediate Files**: Relies on JSON files that may be outdated
3. **Manual Process**: No single script to run the complete pipeline
4. **No Fresh Data**: Enhancement uses old JSON files, not current database

## Files Created During Processing

### Input Files
- `/var/www/html/network-data/nightly_snmp_collection_{timestamp}.json`
- `physical_inventory_stacks_output.json` (intermediate)

### Output Files  
- `inventory_complete.csv` (after enhancement)
- `physical_inventory_deduplicated.json` (after dedup)
- `inventory_consolidated_final.csv` (after VDC consolidation)
- `inventory_ultimate_final.csv` (final output - 548 rows)

### Database Tables
- `comprehensive_device_inventory` - Raw SNMP data
- `inventory_web_format` - Final processed data for web display

## Key Features of Final Data

1. **No Duplicates**: FEX devices appear only once (under -01 switches)
2. **Clean Models**: 
   - N2K-C2232PP-10GE (not "Fabric Extender Module...")
   - N2K-C2248TP-1GE
   - N2K-B22DELL-P
3. **Proper Hierarchy**: Parent-child relationships maintained
4. **EOL Integration**: Joins with `corporate_eol` table for dates

## Web Display (Tab 4)

The processed data is displayed at `/inventory` Tab 4 with:
- Hierarchical tree view
- EOL/EOS dates with color coding
- No duplicate FEX devices
- Clean model numbers

## Cron Job

Current cron (root):
```
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_inventory_db.py >> /var/log/nightly-inventory-db.log 2>&1
```

This runs a different inventory script, not the complete pipeline.

## Next Steps

1. Create unified script that runs all steps in sequence
2. Use fresh SNMP data instead of old JSON files  
3. Add error handling and logging
4. Test complete pipeline with fresh collection
5. Update cron job to run unified script

---
Last Updated: July 10, 2025
Created by: Claude (based on July 8, 2025 development work)