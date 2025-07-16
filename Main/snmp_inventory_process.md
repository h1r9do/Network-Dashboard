# SNMP Inventory Processing Scripts Documentation
## Created: July 10, 2025

This document catalogs all scripts created in the past 48 hours (July 8-10, 2025) for the SNMP inventory processing pipeline.

## Overview
A comprehensive inventory processing system was developed to collect SNMP data from network devices, apply model enhancements, remove duplicates, and generate clean CSV outputs for database import and web display.

## Scripts by Category

### **INVENTORY PROCESSING PIPELINE SCRIPTS (9 scripts)**

1. **`complete_inventory_enhancement.py`**
   - Purpose: FEX model extraction and SFP identification
   - Key Features: Converts "Fabric Extender Module: 48x1GE..." → "N2K-C2248TP-1GE"
   - Input: JSON inventory data
   - Output: Enhanced models with clean part numbers

2. **`consolidate_vdc_devices.py`**
   - Purpose: VDC (Virtual Device Context) consolidation logic
   - Function: Combines multiple VDC entries into single device records
   - Preserves all modules and components while eliminating VDC duplicates

3. **`deduplicate_inventory_serials.py`**
   - Purpose: VPC duplicate removal for shared resources
   - Logic: Assigns shared FEX devices only to -01 switches, removes from -02
   - Critical for Nexus 5K/6K VPC pairs that report same FEX on both switches

4. **`generate_ultimate_final_csv.py`**
   - Purpose: Final CSV generation (548 rows)
   - Features: VDC consolidation, no duplicate serials, FEX model extraction, SFP identification
   - Input: Multiple processed JSON files
   - Output: `inventory_ultimate_final.csv` - the gold standard

5. **`import_ultimate_final_inventory_to_db.py`**
   - Purpose: Database import of final processed CSV
   - Process: Clears existing `inventory_web_format` table, imports with parent-child relationships
   - Validation: Ensures no duplicate FEX devices in final database

6. **`nightly_inventory_complete_pipeline.py`**
   - Purpose: Unified pipeline script (current development version)
   - Combines all processing steps into single executable
   - Database-driven approach using fresh SNMP data

7. **`nightly_inventory_complete_pipeline_original.py`**
   - Purpose: Original version of unified pipeline
   - Backup of initial implementation before modifications

8. **`test_complete_inventory_pipeline.py`**
   - Purpose: Test version of complete pipeline
   - Safety features for testing without affecting production data

9. **`process_inventory_with_dedup_and_enhancement.py`**
   - Purpose: Combined processing script
   - Integrates deduplication and enhancement in single step

### **SNMP COLLECTION SCRIPTS (3 scripts)**

10. **`nightly_snmp_inventory_collection_final.py`**
    - Purpose: Main SNMP collector using encrypted credentials
    - Features: Multi-threading, database storage, entity MIB collection
    - Output: Raw SNMP data in `comprehensive_device_inventory` table
    - Schedule: Runs nightly at 2:00 AM

11. **`nightly_snmp_inventory_web_format_v2.py`**
    - Purpose: Converts raw SNMP data to hierarchical web format
    - Input: `comprehensive_device_inventory` table
    - Output: `inventory_web_format` table (but without enhancements)
    - Issue: Does NOT apply model enhancements or deduplication

12. **`clean_inventory_database.py`**
    - Purpose: Database cleanup and maintenance
    - Removes old/stale inventory records

### **ANALYSIS AND TESTING SCRIPTS (4 scripts)**

13. **`inventory_format_analysis.py`**
    - Purpose: Format comparison between different processing stages
    - Compares JSON vs CSV vs database formats

14. **`test_duplicate_serials.py`**
    - Purpose: Testing duplicate serial number detection
    - Validates VPC duplicate identification logic

15. **`test_enhanced_inventory.py`**
    - Purpose: Testing model enhancement functions
    - Validates FEX and SFP model extraction

16. **`inventory_tabs_functions.py`**
    - Purpose: Web display functions for inventory tabs
    - Generates hierarchical tree view for web interface

### **GENERATION AND IMPORT SCRIPTS (4 scripts)**

17. **`generate_final_enhanced_csv.py`**
    - Purpose: Enhanced CSV generation (intermediate step)
    - Applies model enhancements without full deduplication

18. **`generate_inventory_web_format.py`**
    - Purpose: Web format generation for display
    - Creates parent-child relationship structure for UI

19. **`import_enhanced_inventory_to_db.py`**
    - Purpose: Import enhanced (but not deduplicated) data
    - Intermediate import step in processing chain

20. **`update_inventory_table_structure.py`**
    - Purpose: Database schema updates
    - Modifies table structure to support new features

### **NIGHTLY AUTOMATION SCRIPTS (2 scripts)**

21. **`nightly/nightly_inventory_db.py`**
    - Purpose: Nightly database processing script
    - Current production cron job runner

22. **`run_nightly_inventory_complete.py`**
    - Purpose: Complete pipeline runner
    - Orchestrates entire processing sequence

## Processing Flow

### Original JSON-Based Process (548 rows)
```
SNMP Collection → JSON Files → Enhancement → Deduplication → VDC Consolidation → Final CSV → Database
```

1. `nightly_snmp_inventory_collection_final.py` - Collect SNMP data
2. `complete_inventory_enhancement.py` - Apply model enhancements
3. `deduplicate_inventory_serials.py` - Remove VPC duplicates  
4. `consolidate_vdc_devices.py` - Consolidate VDC devices
5. `generate_ultimate_final_csv.py` - Generate final 548-row CSV
6. `import_ultimate_final_inventory_to_db.py` - Import to database

### New Database-Driven Process (6,336 rows)
```
SNMP Collection → Database → Enhancement → Deduplication → CSV → Database
```

1. `nightly_snmp_inventory_collection_final.py` - Collect to database
2. `nightly_inventory_complete_pipeline.py` - Process from database
   - Export from `comprehensive_device_inventory`
   - Apply model enhancements  
   - Remove VPC duplicates
   - Generate site-grouped CSV
   - Import to `inventory_web_format`

## Key Differences

### Data Volume
- **Original Process**: 548 rows (from processed JSON files)
- **New Process**: 6,336 rows (from full database)

### Filtering Logic
- **Original**: Multiple filtering stages, SFP limits (10 per device), empty serial removal
- **New**: Needs same filtering applied to match original output

### Input Sources
- **Original**: July 8, 2025 processed JSON files (static)
- **New**: Current SNMP database (dynamic, fresh data)

## Current Issue

The new pipeline generates 6,336 rows vs the expected 548 rows because:
1. Uses full database instead of filtered JSON files
2. Missing component filtering (empty serials, FwdEngine modules)
3. No SFP limiting per device
4. Includes devices that were filtered out in original process

## Next Steps

1. Apply original filtering logic to new pipeline
2. Match device selection criteria from JSON processing
3. Implement SFP limiting and empty serial filtering
4. Test against known good 548-row output
5. Deploy unified pipeline for production use

## Files Referenced

### Input Files
- `/var/www/html/network-data/nightly_snmp_collection_{timestamp}.json`
- `physical_inventory_stacks_output.json`
- `physical_inventory_consolidated.json`
- `physical_inventory_deduplicated.json`

### Output Files
- `inventory_ultimate_final.csv` (548 rows - gold standard)
- `inventory_complete.csv` (after enhancement)
- `inventory_consolidated_final.csv` (after VDC consolidation)

### Database Tables
- `comprehensive_device_inventory` - Raw SNMP data
- `inventory_web_format` - Processed data for web display

---
**Total Scripts Created**: 22 scripts in past 48 hours  
**Last Updated**: July 10, 2025  
**Status**: Pipeline development in progress, filtering logic alignment needed