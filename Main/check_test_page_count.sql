-- Check what the test page should be showing
SELECT 
    COUNT(DISTINCT c.id) as total_enabled_with_dt_tag
FROM circuits c
JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
WHERE c.status = 'Enabled'
AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
AND NOT (
    mi.network_name ILIKE '%hub%' OR
    mi.network_name ILIKE '%lab%' OR
    mi.network_name ILIKE '%voice%' OR
    mi.network_name ILIKE '%test%'
);