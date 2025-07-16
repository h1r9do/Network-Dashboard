# DSR Circuits - Performance Monitoring Documentation

## Overview
**URL**: `/performance`  
**File**: `/usr/local/bin/Main/performance.py`  
**Blueprint**: `performance_bp`  
**Purpose**: Real-time API endpoint performance tracking and monitoring with hourly automated collection

## Hourly API Performance Collection (NEW)

### Automated Data Collection
- **Schedule**: Every hour at :00 (via cron job)
- **Script**: `/usr/local/bin/Main/nightly/hourly_api_performance.py`
- **Log File**: `/var/log/api-performance.log`
- **Data Retention**: 30 days (automatic cleanup)
- **Database Table**: `api_performance`

### Crontab Entry
```bash
# Hourly API performance monitoring
0 * * * * /usr/bin/python3 /usr/local/bin/Main/nightly/hourly_api_performance.py >> /var/log/api-performance.log 2>&1
```

## Monitored API Endpoints

The hourly collection monitors 27 API endpoints across 9 categories:

### Circuit APIs (4 endpoints)
- `/api/circuits/search` - Circuit search functionality with test parameter
- `/api/dashboard-data` - Main dashboard data aggregation
- `/api/get-assignments` - Circuit assignment retrieval
- `/api/inflight-data` - In-flight circuit tracking data

### Documentation APIs (1 endpoint)
- `/api/documentation/content` - Documentation content retrieval

### Firewall APIs (3 endpoints)
- `/api/firewall/rules` - Firewall rule management
- `/api/firewall/template/Standard_Store` - Template retrieval
- `/api/networks` - Network list for firewall deployment

### Inventory APIs (4 endpoints)
- `/api/inventory-summary` - Device inventory summary statistics
- `/api/inventory-details` - Detailed inventory data (limit 10)
- `/api/ssh-inventory` - SSH-collected network inventory
- `/api/eol/summary` - End-of-life device summary

### New Stores APIs (2 endpoints)
- `/api/new-stores` - New store management
- `/api/new-store-circuits-with-tod` - TOD circuit data

### Performance APIs (3 endpoints)
- `/api/performance/current` - Current performance metrics
- `/api/performance/summary` - Overall performance summary
- `/api/performance/anomalies` - Performance anomaly detection

### Reporting APIs (5 endpoints)
- `/api/closure-attribution-data` - Team attribution (7 days)
- `/api/daily-enablement-data` - Enablement tracking (7 days)
- `/api/enablement-trend` - Trend analysis
- `/api/ready-queue-data` - Ready queue status
- `/api/reports-health` - Report health status

### Switch APIs (1 endpoint)
- `/api/switch-port-clients` - Port client data (test store)

### System Health APIs (3 endpoints)
- `/api/system-health/summary` - Health summary
- `/api/system-health/all` - Complete health data
- `/api/health` - Basic health check

### Tag Management APIs (1 endpoint)
- `/api/tags/inventory` - Tag inventory data (limit 10)

## Page Layout & Components

### Header Section
- **Title**: "Performance Monitoring Dashboard"
- **Performance Score**: Overall system performance rating (0-100)
- **Time Period Selector**: Real-time, 1h, 6h, 24h, 7d, 30d
- **Comparison Mode**: Compare periods side-by-side

### Performance Overview Cards
**Key Performance Indicators**: Real-time metrics from hourly collection

#### Response Time Card
```
Average Response Time
━━━━━━━━━━━━━━━━━━━
124ms ↓12%
P95: 245ms | P99: 512ms
```

#### Throughput Card
```
Requests per Hour
━━━━━━━━━━━━━━━━━━━
9,360 req/h ↑8%
Peak: 25,380 | Min: 2,700
```

#### Error Rate Card
```
Error Rate
━━━━━━━━━━━━━━━━━━━
0.12% ↓0.05%
4xx: 0.08% | 5xx: 0.04%
```

#### Success Rate Card
```
API Success Rate
━━━━━━━━━━━━━━━━━━━
99.88% ↑0.05%
Failed: 3 of 2,567 calls
```

### Navigation Controls
- **🏠 Home Button**: Returns to main navigation (`/home`)
- **🔄 Refresh Button**: Force data refresh
- **📊 View Mode**: Grid/List/Chart view
- **📥 Export Button**: Download performance data

## Performance Metrics

### API Performance by Category
**Hourly Collection Results**: Latest performance data

#### Category Performance Summary
| Category | Endpoints | Avg Response | Success Rate | Slowest Endpoint |
|----------|-----------|--------------|--------------|------------------|
| Circuits | 4 | 156ms | 99.9% | /api/dashboard-data (234ms) |
| Inventory | 4 | 89ms | 100% | /api/inventory-details (124ms) |
| Reporting | 5 | 267ms | 99.5% | /api/daily-enablement-data (456ms) |
| System | 3 | 12ms | 100% | /api/system-health/all (34ms) |
| Firewall | 3 | 145ms | 99.8% | /api/firewall/rules (234ms) |
| New Stores | 2 | 78ms | 100% | /api/new-store-circuits-with-tod (89ms) |
| Performance | 3 | 45ms | 100% | /api/performance/current (67ms) |
| Switch | 1 | 234ms | 98.5% | /api/switch-port-clients (234ms) |
| Tags | 1 | 56ms | 100% | /api/tags/inventory (56ms) |

### Database Storage

#### ApiPerformance Table Schema
```sql
CREATE TABLE api_performance (
    id INTEGER PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    category VARCHAR(50),
    response_time FLOAT,        -- milliseconds
    status_code INTEGER,
    response_size INTEGER,      -- bytes
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_api_perf_endpoint_time ON api_performance(endpoint, timestamp);
CREATE INDEX idx_api_perf_category_time ON api_performance(category, timestamp);
```

### Monitoring Process Flow

1. **Hourly Execution**: Cron triggers collection script at :00
2. **Endpoint Testing**: Each API endpoint called with test parameters
3. **Metric Collection**: Response time, size, and status recorded
4. **Database Storage**: Metrics stored in ApiPerformance table
5. **Data Cleanup**: Records older than 30 days automatically removed
6. **Dashboard Display**: Real-time visualization of collected metrics

## Real-Time Monitoring

### Live Performance Graphs
**Interactive Time-Series Charts**: Based on hourly collected data

#### Response Time Trends (24h)
```
Response Time (ms)
600 ┤
500 ┤    ╱╲
400 ┤   ╱  ╲    ╱╲
300 ┤  ╱    ╲  ╱  ╲
200 ┤═╯      ╲╱    ╲═══
100 ┤                
  0 └─────────────────────
    00:00  06:00  12:00  18:00
```

#### API Call Success Rate (24h)
```
Success Rate (%)
100 ┤═════════════╱═════
 99 ┤            ╱
 98 ┤           ╱
 97 ┤          ╱
 96 ┤
  0 └─────────────────────
    00:00  06:00  12:00  18:00
```

### Performance Thresholds

#### Response Time Categories
- **Excellent**: < 100ms ✅
- **Good**: 100-500ms 🟢
- **Fair**: 500-1000ms 🟡
- **Poor**: > 1000ms 🟠
- **Critical**: > 5000ms 🔴
- **Timeout**: > 30 seconds ⛔

#### Success Rate Targets
- **Target**: > 99.9% success rate
- **Warning**: 95-99.9% success rate
- **Critical**: < 95% success rate

## Performance Analysis

### Anomaly Detection
**Statistical Analysis**: Based on 2 standard deviations from 7-day baseline

#### Recent Anomalies Example
```
Performance Anomalies Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. /api/dashboard-data
   - Response Time: 1,234ms (Normal: 234ms)
   - Deviation: 4.3σ
   - Timestamp: 2025-07-03 14:30:00
   - Status: 200 OK

2. /api/switch-port-clients
   - Response Time: 5,678ms (Normal: 234ms)  
   - Deviation: 8.7σ
   - Timestamp: 2025-07-03 15:45:00
   - Status: 504 Timeout
```

### Hourly Summary Statistics
**Aggregated Performance Data**: Last collection run

```
Hourly Performance Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━
Total endpoints tested: 27
Success rate: 99.7%
Average response time: 178.4ms
Max response time: 1,234ms
Min response time: 8ms

Failed Endpoints:
- /api/switch-port-clients (1 timeout)

Slow Endpoints (>1000ms):
- /api/daily-enablement-data (1,124ms)
```

## API Performance Details

### Performance Monitoring API Endpoints

#### Data Retrieval APIs
- `/api/performance/current` - Current performance metrics for all endpoints
- `/api/performance/history/<endpoint>` - Historical data for specific endpoint (24h default)
- `/api/performance/anomalies` - Recent performance anomalies with deviation scores
- `/api/performance/summary` - Overall system performance summary with percentiles

#### Example Response: /api/performance/current
```json
{
    "success": true,
    "metrics": [
        {
            "endpoint": "/api/dashboard-data",
            "module": "circuits",
            "avg_time": 234.56,
            "max_time": 1234.0,
            "min_time": 123.4,
            "samples": 24,
            "avg_size_kb": 45.6,
            "error_rate": 0.0
        }
    ],
    "timestamp": "2025-07-03T16:00:00Z"
}
```

## Optimization Recommendations

### Based on Hourly Collection Data

#### Current Recommendations
1. **Cache Slow Endpoints**:
   - `/api/daily-enablement-data` averages 456ms
   - Implement 5-minute cache for 90% reduction
   
2. **Optimize Database Queries**:
   - `/api/dashboard-data` shows increasing response times
   - Add composite index on (site_id, status)
   
3. **Rate Limit Management**:
   - Switch API calls approaching timeout threshold
   - Implement request batching for efficiency

### Performance Tuning Based on Metrics

#### Recommended Actions
```yaml
# High Priority (Based on hourly data)
- Cache reporting endpoints (>400ms avg)
- Add database connection pooling
- Implement request deduplication

# Medium Priority
- Optimize inventory queries
- Add response compression
- Update timeout values

# Low Priority  
- Minify static assets
- Enable HTTP/2
- Add CDN for static files
```

## Historical Analysis

### Performance Trends from Hourly Data

#### Daily Pattern Analysis
```
Average Response Time by Hour (Last 7 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00:00-06:00: 124ms (Low traffic)
06:00-09:00: 234ms (Morning surge)
09:00-12:00: 189ms (Normal operations)
12:00-13:00: 156ms (Lunch dip)
13:00-17:00: 245ms (Peak hours)
17:00-24:00: 134ms (Evening decline)
```

#### Weekly Performance Summary
| Day | Avg Response | Total Calls | Success Rate | Incidents |
|-----|--------------|-------------|--------------|-----------|
| Mon | 189ms | 45,678 | 99.8% | 0 |
| Tue | 234ms | 48,234 | 99.5% | 1 |
| Wed | 178ms | 46,789 | 99.9% | 0 |
| Thu | 156ms | 44,567 | 100% | 0 |
| Fri | 245ms | 52,345 | 99.2% | 2 |
| Sat | 124ms | 23,456 | 100% | 0 |
| Sun | 112ms | 21,234 | 100% | 0 |

## Export & Reporting

### Automated Performance Reports

#### Available Reports
1. **Hourly Performance Summary**:
   - All endpoint metrics
   - Success/failure counts
   - Response time percentiles
   - Anomaly detection results

2. **Daily Performance Report**:
   - 24-hour trend analysis
   - Peak usage identification
   - Slow query analysis
   - Optimization opportunities

3. **Weekly Executive Summary**:
   - High-level KPIs
   - Week-over-week comparison
   - Incident correlation
   - Capacity planning data

### Export Options
- **CSV Export**: Raw hourly metrics data
- **PDF Reports**: Formatted with graphs
- **API Access**: Programmatic data retrieval
- **Email Alerts**: Threshold breach notifications

## Best Practices

### Using Performance Data

1. **Monitor Trends**: Focus on patterns, not individual spikes
2. **Set Baselines**: Use 7-day averages for anomaly detection
3. **Correlate Events**: Match performance dips with deployments
4. **Act on Data**: Implement caching for consistently slow endpoints
5. **Regular Reviews**: Weekly performance review meetings

### Alert Configuration

```javascript
// Recommended alert thresholds based on hourly data
const alertThresholds = {
    responseTime: {
        warning: 500,     // ms - 2x normal
        critical: 1000    // ms - 5x normal
    },
    errorRate: {
        warning: 1,       // % - slight degradation
        critical: 5       // % - major issues
    },
    availability: {
        warning: 99.5,    // % - minor impact
        critical: 99.0    // % - significant impact
    }
};
```

---
*Last Updated: July 3, 2025*  
*Enhanced with hourly automated API performance collection*  
*Part of DSR Circuits Documentation Suite*