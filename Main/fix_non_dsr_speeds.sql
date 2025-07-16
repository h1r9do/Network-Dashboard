-- Find Non-DSR circuits with missing speeds in enriched table
SELECT 
    c.site_name,
    c.provider_name,
    c.details_ordered_service_speed as circuit_speed,
    e.wan1_speed as enriched_wan1_speed,
    e.wan2_speed as enriched_wan2_speed,
    e.wan1_provider,
    e.wan2_provider
FROM circuits c
JOIN enriched_circuits e ON c.site_name = e.network_name
WHERE c.data_source = 'Non-DSR' 
    AND c.details_ordered_service_speed IS NOT NULL 
    AND c.details_ordered_service_speed <> ''
    AND (
        (c.provider_name = e.wan1_provider AND (e.wan1_speed IS NULL OR e.wan1_speed = '')) OR
        (c.provider_name = e.wan2_provider AND (e.wan2_speed IS NULL OR e.wan2_speed = ''))
    )
ORDER BY c.site_name;