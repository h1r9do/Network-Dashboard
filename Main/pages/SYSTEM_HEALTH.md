# DSR Circuits - System Health Monitor Documentation

## Overview
**URL**: `/system-health`  
**File**: `/usr/local/bin/Main/system_health.py`  
**Blueprint**: `system_health_bp`  
**Purpose**: Infrastructure monitoring, diagnostics, and system health tracking

## Page Layout & Components

### Header Section
- **Title**: "System Health Monitor"
- **Overall Health Score**: 0-100% system health indicator
- **Status Badge**: 🟢 Healthy | 🟡 Warning | 🔴 Critical
- **Last Check**: Timestamp of most recent health check

### Quick Status Dashboard
**Real-time System Metrics**: At-a-glance health indicators

#### Status Cards
```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Database      │ │   Web Server    │ │   API Status    │ │   Disk Space    │
│   🟢 Healthy    │ │   🟢 Running    │ │   🟡 Degraded   │ │   🟢 78% Free   │
│   4ms latency   │ │   0.3s response │ │   2 errors/min  │ │   45GB/200GB    │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Navigation Controls
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **Auto-Refresh Toggle**: Enable/disable live updates
- **Time Range**: 1h, 6h, 24h, 7d, 30d views
- **Export Report**: Download health report

## System Components Monitoring

### Database Health
**PostgreSQL Monitoring**: Database performance and health

#### Metrics Tracked
- **Connection Pool**: Active/idle connections
- **Query Performance**: Slow query log
- **Table Size**: Growth monitoring
- **Index Health**: Fragmentation check
- **Replication Lag**: If applicable

#### Visual Display
```
Database Connections
████████████░░░░░░░░ 60% (60/100)

Query Response Time
Avg: 4ms | P95: 12ms | P99: 45ms

Top Slow Queries:
1. SELECT * FROM circuits... (850ms)
2. UPDATE meraki_inventory... (420ms)
```

### Web Application Health
**Flask Application Monitoring**: Service performance

#### Metrics Tracked
- **Response Times**: Page load speeds
- **Error Rates**: 4xx/5xx errors
- **Memory Usage**: Python process memory
- **CPU Usage**: Application CPU load
- **Request Rate**: Requests per second

#### Health Indicators
```javascript
healthScore = {
    responseTime: getScore(avgResponseTime, [100, 500, 1000]), // ms
    errorRate: getScore(errorPercent, [0.1, 1, 5]), // %
    memory: getScore(memoryUsage, [50, 75, 90]), // %
    cpu: getScore(cpuUsage, [40, 70, 90]) // %
};
```

### External Service Health
**API Integration Monitoring**: Third-party service status

#### Monitored Services
1. **Meraki API**:
   - Response time
   - Rate limit usage
   - Error rates
   - API availability

2. **DSR Global**:
   - CSV availability
   - Download success
   - Parse errors
   - Data freshness

3. **ServiceNow**:
   - API connectivity
   - Sync status
   - Queue depth
   - Error count

### Infrastructure Health
**Server and Network Monitoring**: System resources

#### System Metrics
```bash
CPU Usage:        ████████░░░░░░░░ 45%
Memory Usage:     ██████████████░░ 82%
Disk I/O:         ████░░░░░░░░░░░░ 23%
Network I/O:      ██████░░░░░░░░░░ 34%

Load Average:     1.23, 1.45, 1.67
Uptime:          45 days, 3:21:45
```

## Process Monitoring

### Critical Processes
**Service Status Tracking**: Essential system services

#### Process List
| Process | Status | PID | CPU | Memory | Uptime | Restarts |
|---------|---------|-----|-----|---------|---------|-----------|
| nginx | 🟢 Running | 1234 | 0.1% | 125MB | 45d | 0 |
| postgres | 🟢 Running | 2345 | 5.2% | 1.2GB | 45d | 0 |
| python3 (Flask) | 🟢 Running | 3456 | 2.3% | 456MB | 2d | 3 |
| redis | 🔴 Stopped | - | - | - | - | - |

### Scheduled Jobs
**Cron Job Monitoring**: Nightly script health

#### Job Status
```
Nightly DSR Pull      ✅ Last run: 00:05 (Success)
Meraki Inventory      ✅ Last run: 01:03 (Success)
Enrichment Process    ⚠️ Last run: 03:02 (Warning - 10 failures)
Enablement Tracking   ✅ Last run: 04:01 (Success)
Circuit History       ❌ Last run: Failed - Check logs
```

## Alert Management

### Active Alerts
**Current System Issues**: Real-time problem tracking

#### Alert Display
```
┌─ CRITICAL ─────────────────────────────────────┐
│ 🔴 Database connection pool exhausted          │
│    Started: 10:45 AM | Duration: 5 minutes     │
│    Impact: Slow page loads, timeouts           │
│    Action: Restart application or increase pool │
└────────────────────────────────────────────────┘

┌─ WARNING ──────────────────────────────────────┐
│ 🟡 Disk space below 20% on /var               │
│    Current: 18% free (36GB of 200GB)          │
│    Trend: -2GB/day                            │
│    Action: Clean logs or expand disk           │
└────────────────────────────────────────────────┘
```

### Alert Configuration
```javascript
alertRules = {
    database: {
        connectionPool: { warn: 80, crit: 95 },
        queryTime: { warn: 100, crit: 500 }, // ms
        deadlocks: { warn: 1, crit: 5 }
    },
    disk: {
        usage: { warn: 80, crit: 90 }, // percent
        growth: { warn: 5, crit: 10 } // GB/day
    },
    api: {
        errorRate: { warn: 1, crit: 5 }, // percent
        responseTime: { warn: 1000, crit: 5000 } // ms
    }
};
```

## Performance Graphs

### Time Series Metrics
**Historical Performance Data**: Trend visualization

#### Available Graphs
1. **Response Time Graph**:
   - Line chart of average response times
   - P95 and P99 percentiles
   - Anomaly detection overlay

2. **Error Rate Graph**:
   - Stacked area chart by error type
   - 4xx vs 5xx errors
   - Success rate percentage

3. **Resource Usage**:
   - CPU, Memory, Disk I/O
   - Multi-line comparison
   - Threshold indicators

4. **API Performance**:
   - External service response times
   - Rate limit usage
   - Availability percentage

### Interactive Features
- **Zoom**: Click and drag to zoom
- **Pan**: Scroll through time
- **Compare**: Overlay multiple metrics
- **Export**: Download graph data

## Log Viewer

### Integrated Log Access
**Real-time Log Streaming**: View system logs

#### Log Categories
- **Application Logs**: Flask application logs
- **Error Logs**: Python exceptions
- **Access Logs**: nginx access logs
- **Database Logs**: PostgreSQL logs
- **Cron Logs**: Scheduled job output

#### Log Search
```bash
# Search syntax
level:ERROR AND message:"database"
timestamp:">2025-07-03" AND source:"flask"
"connection timeout" AND NOT "retry succeeded"
```

### Log Analysis
- **Pattern Detection**: Recurring errors
- **Frequency Analysis**: Error rate trends
- **Correlation**: Related log entries
- **Export**: Download for analysis

## Diagnostic Tools

### Health Check Endpoints
**System Validation**: Run diagnostic tests

#### Available Tests
1. **Database Connectivity**:
   ```python
   def test_database():
       try:
           db.session.execute('SELECT 1')
           return {'status': 'ok', 'latency': response_time}
       except Exception as e:
           return {'status': 'error', 'message': str(e)}
   ```

2. **API Connectivity**:
   - Meraki API test
   - ServiceNow test
   - DSR Global access

3. **File System**:
   - Write permissions
   - Disk space
   - Log rotation

4. **Network Tests**:
   - DNS resolution
   - External connectivity
   - Port availability

### Performance Profiler
**Application Profiling**: Identify bottlenecks

#### Profiling Options
- **Route Profiling**: Time per endpoint
- **Query Profiling**: Database query analysis
- **Memory Profiling**: Memory leak detection
- **CPU Profiling**: Hot spot identification

## Maintenance Mode

### Maintenance Controls
**System Maintenance**: Controlled downtime

#### Maintenance Features
```javascript
maintenanceMode = {
    enabled: false,
    message: "System maintenance in progress",
    allowedIPs: ["10.0.0.1", "10.0.0.2"],
    estimatedEnd: "2025-07-03 14:00",
    redirectUrl: "/maintenance"
};
```

### Pre-Maintenance Checks
1. **Backup Status**: Verify recent backups
2. **Active Users**: Check current sessions
3. **Running Jobs**: No critical jobs running
4. **Queue Depth**: Process queues empty

## API Endpoints

### Health Check APIs
- `GET /api/health` - Overall health status
- `GET /api/health/database` - Database health
- `GET /api/health/services` - Service status
- `GET /api/health/metrics` - Performance metrics

### Diagnostic APIs
- `POST /api/diagnostics/run` - Run diagnostic test
- `GET /api/logs/stream` - Stream logs
- `GET /api/alerts/active` - Active alerts
- `POST /api/maintenance/toggle` - Maintenance mode

## Notification System

### Alert Channels
```javascript
notifications = {
    email: {
        enabled: true,
        recipients: ["ops@company.com"],
        throttle: 300 // seconds
    },
    sms: {
        enabled: false,
        recipients: ["+1234567890"],
        criticalOnly: true
    },
    slack: {
        enabled: true,
        webhook: "https://hooks.slack.com/...",
        channel: "#ops-alerts"
    }
};
```

### Escalation Rules
1. **Warning**: Email notification
2. **Critical**: Email + SMS + Slack
3. **Repeated**: Escalate to manager
4. **Resolved**: Send all-clear

## Mobile Access

### Mobile Dashboard
- **Simplified View**: Critical metrics only
- **Push Notifications**: Critical alerts
- **Quick Actions**: Restart services
- **On-Call Access**: Emergency controls

### Mobile-Specific Features
- **Status Widget**: Home screen widget
- **Offline Alerts**: Cached alert history
- **Voice Alerts**: Text-to-speech critical
- **Location Based**: On-site features

## Historical Data

### Data Retention
```yaml
metrics:
  1_minute: 24_hours
  5_minute: 7_days
  1_hour: 30_days
  1_day: 1_year

logs:
  application: 30_days
  error: 90_days
  access: 7_days
  audit: 7_years
```

### Trend Analysis
- **Capacity Planning**: Growth projections
- **Performance Baselines**: Normal behavior
- **Anomaly Detection**: Unusual patterns
- **Predictive Alerts**: Before problems

## Integration Points

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Advanced visualization
- **ELK Stack**: Log aggregation
- **PagerDuty**: Incident management

### Automation
- **Auto-Remediation**: Self-healing actions
- **Runbook Automation**: Guided fixes
- **Capacity Scaling**: Auto-scale resources
- **Backup Triggers**: On-demand backups

---
*Last Updated: July 3, 2025*  
*Comprehensive system health monitoring and diagnostics*  
*Part of DSR Circuits Documentation Suite*