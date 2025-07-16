-- Create provider matching test table with unique name

-- Drop test table if it exists
DROP TABLE IF EXISTS provider_match_test CASCADE;

-- Create test table with provider matching columns
CREATE TABLE provider_match_test (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(50),
    site_name VARCHAR(255),
    circuit_purpose VARCHAR(50),
    dsr_provider VARCHAR(255),
    arin_provider VARCHAR(255),
    wan_port VARCHAR(10),
    
    -- PROVIDER MATCHING COLUMNS
    provider_match_status VARCHAR(50),        -- 'matched', 'no_match', 'no_data'
    provider_match_confidence INTEGER,        -- 0-100
    provider_canonical VARCHAR(255),          -- Standardized provider name
    match_reason TEXT,                        -- Explanation of match
    
    -- Additional enrichment data
    dsr_ip VARCHAR(50),
    matched_ip VARCHAR(50),
    speed VARCHAR(100),
    cost DECIMAL(10,2),
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique entries per site/circuit
    UNIQUE(site_id, circuit_purpose)
);

-- Create indexes for performance
CREATE INDEX idx_provider_test_site_name ON provider_match_test(site_name);
CREATE INDEX idx_provider_test_match_status ON provider_match_test(provider_match_status);
CREATE INDEX idx_provider_test_confidence ON provider_match_test(provider_match_confidence);

-- Create test view for easy querying
CREATE OR REPLACE VIEW provider_match_test_display AS
SELECT 
    e.site_id,
    e.site_name,
    e.circuit_purpose,
    e.dsr_provider,
    e.arin_provider,
    e.provider_canonical,
    e.provider_match_status,
    e.provider_match_confidence,
    e.match_reason,
    e.wan_port,
    -- Generate display icon based on match status
    CASE 
        WHEN e.provider_match_status = 'matched' AND e.provider_match_confidence >= 90 THEN '✓'
        WHEN e.provider_match_status = 'matched' AND e.provider_match_confidence >= 70 THEN '⚠'
        WHEN e.provider_match_status = 'no_match' THEN '✗'
        WHEN e.provider_match_status = 'no_data' THEN '?'
        ELSE ''
    END as match_icon,
    -- Generate match quality description
    CASE 
        WHEN e.provider_match_confidence >= 95 THEN 'Excellent'
        WHEN e.provider_match_confidence >= 80 THEN 'Good'
        WHEN e.provider_match_confidence >= 70 THEN 'Fair'
        WHEN e.provider_match_confidence > 0 THEN 'Poor'
        ELSE 'No Match'
    END as match_quality,
    -- Color coding for web display
    CASE 
        WHEN e.provider_match_confidence >= 90 THEN 'success'
        WHEN e.provider_match_confidence >= 70 THEN 'warning'
        WHEN e.provider_match_status = 'no_match' THEN 'danger'
        ELSE 'secondary'
    END as match_color,
    e.speed,
    e.cost,
    e.last_updated
FROM provider_match_test e
WHERE e.site_name IS NOT NULL
ORDER BY e.site_name, e.circuit_purpose;

-- Test statistics view
CREATE OR REPLACE VIEW provider_test_statistics AS
SELECT 
    COUNT(*) as total_circuits,
    COUNT(CASE WHEN provider_match_status = 'matched' THEN 1 END) as matched_circuits,
    COUNT(CASE WHEN provider_match_status = 'no_match' THEN 1 END) as no_match_circuits,
    COUNT(CASE WHEN provider_match_status = 'no_data' THEN 1 END) as no_data_circuits,
    ROUND(COUNT(CASE WHEN provider_match_status = 'matched' THEN 1 END)::numeric / COUNT(*) * 100, 2) as match_rate,
    ROUND(AVG(CASE WHEN provider_match_status = 'matched' THEN provider_match_confidence END), 1) as avg_match_confidence,
    COUNT(CASE WHEN provider_match_confidence >= 90 THEN 1 END) as excellent_matches,
    COUNT(CASE WHEN provider_match_confidence BETWEEN 70 AND 89 THEN 1 END) as good_matches,
    COUNT(CASE WHEN provider_match_confidence < 70 AND provider_match_confidence > 0 THEN 1 END) as poor_matches
FROM provider_match_test;

-- Add some sample test data to verify the table works
INSERT INTO provider_match_test (
    site_id, site_name, circuit_purpose, dsr_provider, arin_provider, 
    provider_match_status, provider_match_confidence, provider_canonical, match_reason
) VALUES 
('TEST01', 'TEST 01', 'Primary', 'Spectrum', 'Charter Communications', 'matched', 95, 'Charter Communications', 'Mapped provider'),
('TEST01', 'TEST 01', 'Secondary', 'AT&T Broadband II', 'AT&T', 'matched', 100, 'AT&T', 'Direct match'),
('TEST02', 'TEST 02', 'Primary', 'Brightspeed', 'CenturyLink', 'matched', 90, 'CenturyLink', 'Rebrand mapping'),
('TEST03', 'TEST 03', 'Primary', 'Unknown Provider', 'Some ISP', 'no_match', 0, 'Unknown Provider', 'No mapping found')
ON CONFLICT (site_id, circuit_purpose) DO UPDATE SET
    dsr_provider = EXCLUDED.dsr_provider,
    arin_provider = EXCLUDED.arin_provider,
    provider_match_status = EXCLUDED.provider_match_status,
    provider_match_confidence = EXCLUDED.provider_match_confidence,
    provider_canonical = EXCLUDED.provider_canonical,
    match_reason = EXCLUDED.match_reason;