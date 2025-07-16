-- Update enriched_circuits table to store provider match information
-- This way the web interface just displays pre-calculated results

-- Add new columns to enriched_circuits table
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_match_status VARCHAR(50);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_match_confidence INTEGER;
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS provider_canonical VARCHAR(255);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS dsr_ip VARCHAR(50);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS matched_ip VARCHAR(50);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS speed VARCHAR(100);
ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS cost DECIMAL(10,2);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_enriched_match_status ON enriched_circuits(provider_match_status);
CREATE INDEX IF NOT EXISTS idx_enriched_confidence ON enriched_circuits(provider_match_confidence);

-- Create a view for the web interface to easily query
CREATE OR REPLACE VIEW circuit_match_display AS
SELECT 
    e.site_id,
    e.site_name,
    e.circuit_purpose,
    e.dsr_provider,
    e.arin_provider,
    e.provider_canonical,
    e.provider_match_status,
    e.provider_match_confidence,
    e.wan_port,
    -- Generate display icon based on match status
    CASE 
        WHEN e.provider_match_status = 'matched' AND e.provider_match_confidence >= 90 THEN '✓'
        WHEN e.provider_match_status = 'matched' AND e.provider_match_confidence >= 70 THEN '✓'
        WHEN e.provider_match_status = 'no_match' THEN '✗'
        WHEN e.provider_match_status = 'no_data' THEN '?'
        ELSE ''
    END as match_icon,
    -- Generate match quality
    CASE 
        WHEN e.provider_match_confidence >= 95 THEN 'Excellent'
        WHEN e.provider_match_confidence >= 80 THEN 'Good'
        WHEN e.provider_match_confidence >= 70 THEN 'Fair'
        WHEN e.provider_match_confidence > 0 THEN 'Poor'
        ELSE 'No Match'
    END as match_quality,
    -- Show if this is a special case
    CASE
        WHEN e.circuit_purpose = 'Secondary' AND e.provider_match_confidence = 70 THEN 'Secondary Circuit Conflict'
        WHEN e.provider_match_status = 'matched' AND e.dsr_provider != e.arin_provider THEN 'Mapped Provider'
        WHEN e.provider_match_status = 'matched' AND e.dsr_provider = e.arin_provider THEN 'Direct Match'
        ELSE ''
    END as match_note,
    e.speed,
    e.cost,
    e.last_updated
FROM enriched_circuits e
WHERE e.site_name IS NOT NULL
ORDER BY e.site_name, e.circuit_purpose;

-- Create summary statistics view
CREATE OR REPLACE VIEW provider_match_statistics AS
SELECT 
    COUNT(*) as total_circuits,
    COUNT(CASE WHEN provider_match_status = 'matched' THEN 1 END) as matched_circuits,
    COUNT(CASE WHEN provider_match_status = 'no_match' THEN 1 END) as no_match_circuits,
    COUNT(CASE WHEN provider_match_status = 'no_data' THEN 1 END) as no_data_circuits,
    ROUND(COUNT(CASE WHEN provider_match_status = 'matched' THEN 1 END)::numeric / COUNT(*) * 100, 2) as match_rate,
    AVG(CASE WHEN provider_match_status = 'matched' THEN provider_match_confidence END)::integer as avg_match_confidence
FROM enriched_circuits;

-- Function to get circuit match info for a specific site
CREATE OR REPLACE FUNCTION get_site_circuit_matches(p_site_name VARCHAR)
RETURNS TABLE (
    circuit_purpose VARCHAR,
    dsr_provider VARCHAR,
    arin_provider VARCHAR,
    match_status VARCHAR,
    match_confidence INTEGER,
    match_icon TEXT,
    speed VARCHAR,
    cost DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.circuit_purpose,
        e.dsr_provider,
        e.arin_provider,
        e.provider_match_status,
        e.provider_match_confidence,
        CASE 
            WHEN e.provider_match_status = 'matched' THEN '✓'
            WHEN e.provider_match_status = 'no_match' THEN '✗'
            ELSE '?'
        END as match_icon,
        e.speed,
        e.cost
    FROM enriched_circuits e
    WHERE e.site_name = p_site_name
    ORDER BY e.circuit_purpose;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON circuit_match_display TO PUBLIC;
GRANT SELECT ON provider_match_statistics TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_site_circuit_matches(VARCHAR) TO PUBLIC;