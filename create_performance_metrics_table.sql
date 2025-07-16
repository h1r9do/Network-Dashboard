-- SQL script to create performance_metrics table for DSR Circuits monitoring

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    endpoint_name VARCHAR(255) NOT NULL,
    endpoint_method VARCHAR(10) DEFAULT 'GET',
    endpoint_params TEXT,  -- JSON string of parameters used
    query_execution_time_ms INTEGER NOT NULL,  -- Time in milliseconds
    data_size_bytes INTEGER,  -- Response size in bytes
    data_rows_returned INTEGER,  -- Number of rows/records returned
    response_status INTEGER NOT NULL,  -- HTTP status code
    error_message TEXT,  -- Error details if any
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    module_category VARCHAR(100),  -- Group endpoints by module (dashboard, inventory, etc.)
    db_query_count INTEGER,  -- Number of database queries executed
    cache_hit BOOLEAN DEFAULT FALSE,  -- Whether response was served from cache
    user_agent VARCHAR(255),  -- To track if monitoring or user request
    is_monitoring BOOLEAN DEFAULT TRUE,  -- Distinguish monitoring from actual usage
    
    -- Indexes for performance
    CONSTRAINT idx_performance_timestamp_endpoint 
        INDEX (timestamp DESC, endpoint_name),
    CONSTRAINT idx_performance_endpoint_status 
        INDEX (endpoint_name, response_status),
    CONSTRAINT idx_performance_module_timestamp 
        INDEX (module_category, timestamp DESC)
);

-- Create summary view for quick stats
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    endpoint_name,
    module_category,
    COUNT(*) as total_requests,
    AVG(query_execution_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY query_execution_time_ms) as median_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY query_execution_time_ms) as p95_response_time_ms,
    MAX(query_execution_time_ms) as max_response_time_ms,
    AVG(data_size_bytes) as avg_data_size_bytes,
    SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count,
    ROUND(100.0 * SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate,
    MAX(timestamp) as last_checked
FROM performance_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY endpoint_name, module_category;

-- Create alerts view for anomaly detection
CREATE OR REPLACE VIEW performance_alerts AS
WITH recent_metrics AS (
    SELECT 
        endpoint_name,
        AVG(query_execution_time_ms) as recent_avg,
        STDDEV(query_execution_time_ms) as recent_stddev
    FROM performance_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY endpoint_name
),
baseline_metrics AS (
    SELECT 
        endpoint_name,
        AVG(query_execution_time_ms) as baseline_avg,
        STDDEV(query_execution_time_ms) as baseline_stddev
    FROM performance_metrics
    WHERE timestamp BETWEEN NOW() - INTERVAL '7 days' AND NOW() - INTERVAL '1 hour'
    GROUP BY endpoint_name
)
SELECT 
    r.endpoint_name,
    r.recent_avg,
    b.baseline_avg,
    ROUND(((r.recent_avg - b.baseline_avg) / b.baseline_avg * 100)::numeric, 2) as percent_change,
    CASE 
        WHEN r.recent_avg > b.baseline_avg + (2 * b.baseline_stddev) THEN 'DEGRADED'
        WHEN r.recent_avg > b.baseline_avg + b.baseline_stddev THEN 'WARNING'
        ELSE 'NORMAL'
    END as alert_status
FROM recent_metrics r
JOIN baseline_metrics b ON r.endpoint_name = b.endpoint_name
WHERE b.baseline_avg > 0;

-- Create index for cleanup operations
CREATE INDEX idx_performance_metrics_cleanup ON performance_metrics(timestamp)
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Add comment
COMMENT ON TABLE performance_metrics IS 'Stores performance monitoring data for all DSR Circuits API endpoints';