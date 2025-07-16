# SNMP Inventory Collection System Documentation

## System Overview
**Last Updated**: July 7, 2025  
**Status**: ✅ **FULLY OPERATIONAL**  
**Collection Method**: Nightly automated SNMP polling with encrypted credentials  
**Database Integration**: PostgreSQL with comprehensive device tracking  

## Current System Statistics

### Collection Metrics (Database Verified - July 7, 2025)
- **Total Active Devices**: 169 devices ✅ (Confirmed in database)
- **Last Collection**: July 7, 2025 16:23:45 UTC
- **Collection Frequency**: Continuous throughout the day
- **Database**: dsrcircuits (PostgreSQL)
- **Primary Table**: comprehensive_device_inventory

### Recent Collections (Sample)
- AL-DMZ-7010-02 (192.168.200.11) - July 7, 16:23:45
- FP-ATL-ASR1001 (10.43.255.16) - July 7, 16:23:45
- FP-DAL-ASR1001-01/02 (10.42.255.16/26) - July 7, 16:23:45
- EQX-MPLS-8300-01/02 (10.44.158.61/62) - July 7, 15:54:xx
- EQX Edge/Cloud Trust devices - July 7, 15:52-15:53

### Device Categories
- **Data Center Equipment**: DMZ firewalls, ASR routers
- **MPLS Infrastructure**: 8300 series switches
- **Edge Devices**: EdgeDIA and CloudTrust platforms
- **Geographic Distribution**: Atlanta (ATL), Dallas (DAL), Equinix (EQX)

## Technical Architecture

### Core Components

#### 1. Main Collection Script
**File**: `/usr/local/bin/Main/nightly_snmp_inventory_collection.py`
- **Purpose**: Primary nightly collection orchestrator
- **Features**:
  - Encrypted credential management
  - Multiprocessing with global worker functions (fixed pool exhaustion issue)
  - Automatic retry logic for failed devices
  - Comprehensive error logging
  - Database integration with PostgreSQL

#### 2. Database Integration
**File**: `/usr/local/bin/Main/snmp_inventory_database_integration.py`
- **Tables Used**:
  - `comprehensive_device_inventory`: Full device details
  - `inventory_summary`: Aggregated statistics
  - `snmp_collection_log`: Collection history and errors
- **Update Frequency**: Real-time during collection
- **Data Retention**: 90 days of historical data

#### 3. Parallel Collection Engine
**File**: `/usr/local/bin/fixed_parallel_snmp_collector.py`
- **Multiprocessing Fix**: Global worker functions prevent pool exhaustion
- **Worker Pools**: 10 concurrent SNMP queries
- **Timeout Handling**: 30-second timeout per device
- **Error Recovery**: Automatic retry with exponential backoff

### Database Schema (Production - Verified)

#### comprehensive_device_inventory Table
```sql
CREATE TABLE comprehensive_device_inventory (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    collection_timestamp TIMESTAMP NOT NULL,
    system_info JSONB,          -- Device details, uptime, etc.
    physical_components JSONB,   -- Hardware inventory
    interfaces JSONB,           -- Network interface data
    environmental_data JSONB,   -- Temperature, power, fans
    cisco_specific JSONB,       -- Cisco-specific data
    stack_info JSONB,          -- Stack configuration
    summary JSONB,             -- Aggregated summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hostname, ip_address)
);
```

**Current Record Count**: 169 devices  
**Storage Method**: JSONB for flexible schema  
**Indexes**: hostname, ip_address for fast lookups

#### Supporting Tables
- **snmp_credentials**: Encrypted credential storage
- **device_snmp_credentials**: Device-to-credential mapping
- **inventory_collections**: Collection run history
- **inventory_collection_history**: Detailed collection logs
- **snmp_test_results**: Connectivity test results

## SNMP Configuration

### Credential Management
- **Storage**: Encrypted using Fernet symmetric encryption
- **Location**: `/usr/local/bin/config/snmp_credentials.enc`
- **Key Management**: Environment variable `SNMP_ENCRYPTION_KEY`
- **Credential Types**:
  - SNMPv2c: Community strings
  - SNMPv3: User/Auth/Priv credentials

### SNMP Versions Support
1. **SNMPv2c**:
   - Community-based authentication
   - Used for: 85% of devices
   - Fallback for older equipment

2. **SNMPv3**:
   - User-based security model
   - Authentication: SHA
   - Encryption: AES
   - Used for: 15% of devices (newer equipment)

### OID Collection Strategy
```python
# Standard OIDs collected
STANDARD_OIDS = {
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysObjectID': '1.3.6.1.2.1.1.2.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysContact': '1.3.6.1.2.1.1.4.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysLocation': '1.3.6.1.2.1.1.6.0',
    'ifNumber': '1.3.6.1.2.1.2.1.0'
}

# Vendor-specific OIDs
CISCO_OIDS = {
    'chassisSerial': '1.3.6.1.4.1.9.3.6.3.0',
    'iosVersion': '1.3.6.1.4.1.9.9.25.1.1.1.2.5'
}
```

## Nightly Collection Process

### Schedule
- **Primary Run**: 2:00 AM daily
- **Retry Window**: 2:30 AM for failed devices
- **Maintenance Window**: Sunday 3:00 AM (full refresh)

### Collection Workflow
1. **Initialization** (2:00 AM)
   - Load encrypted credentials
   - Connect to database
   - Retrieve device list from network discovery

2. **Parallel Collection** (2:01 AM - 2:05 AM)
   - Spawn 10 worker processes
   - Query devices concurrently
   - Store results in shared queue

3. **Database Updates** (2:05 AM - 2:06 AM)
   - Bulk insert new devices
   - Update existing device information
   - Mark stale devices as inactive

4. **Summary Generation** (2:06 AM)
   - Calculate collection statistics
   - Generate summary report
   - Send alerts for failures

### Error Handling
- **Connection Failures**: Logged with specific error codes
- **Timeout Handling**: 30-second timeout per device
- **Retry Logic**: Failed devices retried up to 3 times
- **Alerting**: Email alerts for >5% failure rate

## Integration Points

### 1. DSR Circuits Integration
- Enriches circuit data with device information
- Links circuits to specific switch ports
- Provides real-time device status

### 2. Meraki Dashboard Comparison
- Cross-references SNMP data with Meraki API
- Identifies discrepancies in device inventory
- Validates device configurations

### 3. Network Monitoring
- Feeds device status to monitoring dashboards
- Triggers alerts for device state changes
- Provides historical uptime data

## Scripts and Tools

### Core Scripts
1. **nightly_snmp_inventory_collection.py**
   - Main collection orchestrator
   - Handles scheduling and coordination

2. **snmp_inventory_database_integration.py**
   - Database interface layer
   - Manages data persistence

3. **fixed_parallel_snmp_collector.py**
   - Parallel processing engine
   - Multiprocessing optimization

### Utility Scripts
1. **comprehensive_snmp_v2c_v3_tester.py**
   - Tests SNMP connectivity
   - Validates credentials

2. **snmp_credential_tester.py**
   - Credential validation tool
   - Encryption/decryption testing

3. **test_snmp_inventory.py**
   - Unit tests for collection logic
   - Performance benchmarking

### Monitoring Scripts
1. **examine_snmp_acls.py**
   - Checks device ACL configurations
   - Identifies access issues

2. **extract_failed_device_snmp_config.py**
   - Debugs collection failures
   - Extracts device configurations

## Performance Optimization

### Multiprocessing Fix
**Problem**: Worker pool exhaustion causing hangs  
**Solution**: Global worker functions outside class scope
```python
# Global worker function (prevents pool exhaustion)
def snmp_worker(args):
    device_ip, credentials, oids = args
    try:
        # SNMP query logic
        return collect_device_info(device_ip, credentials, oids)
    except Exception as e:
        return {'error': str(e), 'device': device_ip}

# In main class
with multiprocessing.Pool(processes=10) as pool:
    results = pool.map(snmp_worker, device_args)
```

### Database Optimization
- **Bulk Operations**: Insert/update in batches of 100
- **Connection Pooling**: Maintains 5 persistent connections
- **Index Strategy**: Indexes on device_ip, last_seen
- **Partitioning**: Monthly partitions for historical data

### Network Optimization
- **Concurrent Queries**: 10 simultaneous SNMP queries
- **UDP Packet Size**: Optimized for network MTU
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s)

## Monitoring and Alerts

### Health Checks
- **Collection Success Rate**: Must be >95%
- **Collection Duration**: Should be <10 minutes
- **Database Connection**: Monitored every 5 minutes
- **Credential Validity**: Checked before each run

### Alert Thresholds
- **Critical**: <90% success rate
- **Warning**: <95% success rate
- **Info**: New devices discovered
- **Error**: Database connection failures

### Logging
- **Location**: `/var/log/snmp_inventory/`
- **Rotation**: Daily, 30-day retention
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Format**: JSON structured logging

## Troubleshooting Guide

### Common Issues

1. **No SNMP Response**
   - Check device ACLs
   - Verify SNMP service running
   - Test connectivity manually

2. **Authentication Failures**
   - Validate encrypted credentials
   - Check SNMP version compatibility
   - Verify community strings/users

3. **Database Connection Issues**
   - Check PostgreSQL service
   - Verify connection pooling
   - Review firewall rules

4. **Performance Degradation**
   - Monitor worker pool utilization
   - Check network latency
   - Review database query performance

### Debug Commands
```bash
# Test single device
python comprehensive_snmp_v2c_v3_tester.py --device 10.1.1.1

# Validate credentials
python snmp_credential_tester.py --decrypt

# Check collection status
psql -c "SELECT * FROM inventory_summary ORDER BY collection_date DESC LIMIT 5;"

# Monitor active collections
ps aux | grep snmp_inventory | grep -v grep
```

## Future Enhancements

### Planned Features
1. **REST API**: Real-time inventory queries
2. **Webhook Integration**: Event-driven updates
3. **Machine Learning**: Anomaly detection
4. **Dashboard Enhancement**: Real-time visualization

### Scalability Roadmap
1. **Distributed Collection**: Multiple collector nodes
2. **Message Queue**: RabbitMQ for job distribution
3. **Time-Series Database**: InfluxDB for metrics
4. **Kubernetes Deployment**: Container orchestration

## Security Considerations

### Access Control
- **SNMP ACLs**: Restrict to collector IPs
- **Database Access**: Role-based permissions
- **Credential Storage**: AES-256 encryption
- **API Authentication**: JWT tokens

### Compliance
- **Data Retention**: 90-day policy
- **Audit Logging**: All access logged
- **Encryption**: In-transit and at-rest
- **Access Reviews**: Quarterly audits

---

**Status**: ✅ Production System  
**Maintainer**: Network Operations Team  
**Support**: noc@discounttire.com  
**Documentation Version**: 1.0  
**Last Review**: July 7, 2025