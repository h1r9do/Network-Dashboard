# DSR Circuits - New Stores Management Documentation

## Overview
**URL**: `/new-stores`  
**File**: `/usr/local/bin/Main/new_stores.py`  
**Purpose**: Comprehensive store construction and circuit management for new Discount Tire locations

## Page Functionality

### Store Construction Management
Specialized interface for managing new store buildouts, circuit provisioning, and Target Opening Date (TOD) tracking.

### Key Features

1. **Target Opening Date (TOD) Tracking**
   - Store construction timeline management
   - Opening date planning and coordination
   - Milestone tracking and progress monitoring
   - Integration with circuit provisioning schedules

2. **Circuit Creation and Management**
   - Manual circuit creation for new stores
   - **Enhanced Record Number Generation** (July 2025 upgrade)
   - Circuit purpose designation (Primary/Secondary/Backup)
   - Provider and bandwidth specifications

3. **Excel Bulk Upload**
   - Bulk store data import via Excel files
   - Validation and error checking
   - Batch processing capabilities
   - Data mapping and transformation

4. **Meraki Auto-Detection**
   - Automatic removal when stores go live
   - Network activation monitoring
   - Status synchronization
   - Transition tracking from construction to operational

### User Guide

#### Accessing New Stores Management
- Navigate to: `http://neamsatcor1ld01.trtc.com:5052/new-stores`
- Requires administrative access
- Desktop-optimized interface

#### Creating New Store Records

**Important**: For tracking new stores, you must either:
- Upload the latest TOD (Target Opening Date) report, OR
- Manually add a single store, OR  
- Edit the TOD store list for status updates

1. **Upload Latest TOD Report** (Primary Method):
   - Use the most recent TOD Excel report from construction team
   - Contains all upcoming store openings with target dates
   - Bulk imports entire construction schedule
   - Automatically updates existing store statuses
   - Adds new stores not previously in the system
   - Updates milestone dates and progress

2. **Manual Single Store Entry**:
   - Add individual stores not in TOD report
   - Enter store information (name, location, TOD)
   - Specify circuit requirements
   - System auto-generates unique record_number
   - Set construction milestones
   - Use when TOD report doesn't include a specific store

3. **Edit TOD Store List**:
   - Update status for existing TOD stores
   - Modify target opening dates as schedules change
   - Track construction progress milestones
   - Update circuit provisioning status
   - Add notes about delays or issues
   - Mark stores as completed/cancelled

#### TOD Report Workflow
1. **Receive TOD Report**: Weekly/monthly from construction team
2. **Upload to System**: Use the "Upload TOD Report" button
3. **Review Changes**: System shows what will be added/updated
4. **Apply Updates**: Confirm to update database
5. **Manual Adjustments**: Edit individual stores as needed
6. **Track Progress**: Monitor construction through completion

#### TOD Report Format
The TOD Excel report should contain:
- Store Name (e.g., "TXH 97")
- Store ID/Number
- Target Opening Date
- Region/District
- Address Information
- Construction Status
- Any special notes

#### Circuit Management
1. **Add Circuits**: Create primary and backup circuits for new stores
2. **Update Status**: Track provisioning progress
3. **Set TOD**: Manage target opening dates
4. **Monitor Progress**: View construction milestones

#### Record Number Generation (NEW)
When creating circuits manually, the system now generates unique record numbers:
```
Format: DISCOUNT{SITE}{RANDOM}_BR[-I1]
Example: DISCOUNTALB020932013962_BR (Primary)
Example: DISCOUNTALB02926798417_BR-I1 (Secondary)
```

### Technical Implementation

#### Record Number Enhancement (July 2025)
```python
def generate_record_number(site_name, circuit_purpose):
    # Clean site name - remove spaces and special characters
    clean_site = ''.join(c for c in site_name.upper() if c.isalnum())[:10]
    
    # Generate random number (8-10 digits)
    random_num = ''.join([str(random.randint(0, 9)) for _ in range(random.randint(8, 10))])
    
    # Base record number
    record_number = f"DISCOUNT{clean_site}{random_num}_BR"
    
    # Add suffix for non-primary circuits
    if circuit_purpose.lower() != 'primary':
        record_number += "-I1"
        
    return record_number
```

#### Data Protection Features
- **Manual Override Protection**: Prevents DSR pull from overwriting manual entries
- **Data Source Tracking**: `data_source = 'new_stores_manual'`
- **Attribution Tracking**: `manual_override_by = 'new_stores_interface'`

#### Database Integration
- **Primary Tables**: `new_stores`, `circuits`, `circuit_assignments`
- **TOD Tracking**: Comprehensive date management
- **Status Synchronization**: Real-time updates with operational systems

### Excel Upload Process

#### Template Format
- Store Name, Site ID, Target Opening Date
- Circuit specifications and requirements
- Location and contact information
- Construction milestone dates

#### Validation Rules
- Required field checking
- Date format validation
- Duplicate detection
- Business rule enforcement

#### Bulk Processing
- Batch insert operations
- Transaction safety
- Error reporting and rollback
- Progress tracking

### Meraki Integration

#### Auto-Detection Features
- **Live Store Detection**: Automatic identification when stores become operational
- **Circuit Transition**: Seamless handoff from construction to operations
- **Status Updates**: Real-time synchronization with Meraki networks
- **Cleanup Process**: Automatic removal from new stores list

#### Network Monitoring
- Device activation tracking
- Connectivity verification
- Performance baseline establishment
- Alert configuration

### API Endpoints

#### Store Management
- `/api/new-stores`: CRUD operations for store records
- `/api/new-stores/<id>`: Individual store management
- `/api/new-stores/excel-upload`: Bulk upload processing

#### Circuit Management
- `/api/new-circuits`: Create circuits with record_number generation
- `/api/circuits/<id>/status`: Update circuit status
- `/api/circuits/<id>/manual-override`: Manage override protection

#### Data Retrieval
- `/api/new-store-circuits-with-tod`: Comprehensive store and circuit data
- `/api/circuits/update-notes`: Add notes and comments

### User Scenarios

#### Store Construction Manager
1. Upload new store construction schedule via Excel
2. Set target opening dates and milestones
3. Monitor construction progress
4. Coordinate with circuit provisioning teams

#### Network Provisioning Team
1. Create circuits for new stores manually
2. Track provisioning status and assignments
3. Update completion status
4. Coordinate with store opening timelines

#### Operations Team
1. Monitor store transition from construction to operations
2. Verify Meraki auto-detection and cleanup
3. Ensure proper handoff to operational systems
4. Track performance and issues

### Integration Points
- **DSR Dashboard**: Circuit status coordination
- **Meraki API**: Network detection and monitoring
- **ServiceNow**: SCTASK integration for assignments
- **Circuit Enablement Reports**: Analytics and tracking

### Related Pages
- [DSR Dashboard](DSR_DASHBOARD.md)
- [Circuit Enablement Report](CIRCUIT_ENABLEMENT_REPORT.md)
- [Inventory Summary](INVENTORY_SUMMARY.md)

---
*Last Updated: July 3, 2025*  
*Enhanced with record_number auto-generation and manual override protection*  
*Part of DSR Circuits Documentation Suite*