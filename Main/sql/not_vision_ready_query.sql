-- Not Vision Ready Query for DSR Circuits
-- Finds sites that are "Not Vision Ready":
-- 1. Sites with cell/cellular for BOTH WAN1 and WAN2 speeds
-- 2. Sites with speeds under 100.0M x 10.0M on one circuit AND cell/cellular service on the other circuit
-- Only includes Discount-Tire tagged stores and excludes satellite services

WITH circuit_data AS (
    SELECT 
        network_name,
        device_tags,
        wan1_provider,
        wan1_speed,
        wan2_provider,
        wan2_speed,
        -- Parse download speed from wan1_speed (e.g., "100.0M x 10.0M" -> 100.0)
        CASE 
            WHEN wan1_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$' 
            THEN CAST(SUBSTRING(wan1_speed FROM '^([0-9.]+)M') AS NUMERIC)
            ELSE NULL
        END as wan1_download,
        -- Parse upload speed from wan1_speed (e.g., "100.0M x 10.0M" -> 10.0)
        CASE 
            WHEN wan1_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$' 
            THEN CAST(SUBSTRING(wan1_speed FROM '[xX]\s*([0-9.]+)M') AS NUMERIC)
            ELSE NULL
        END as wan1_upload,
        -- Parse download speed from wan2_speed
        CASE 
            WHEN wan2_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$' 
            THEN CAST(SUBSTRING(wan2_speed FROM '^([0-9.]+)M') AS NUMERIC)
            ELSE NULL
        END as wan2_download,
        -- Parse upload speed from wan2_speed
        CASE 
            WHEN wan2_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$' 
            THEN CAST(SUBSTRING(wan2_speed FROM '[xX]\s*([0-9.]+)M') AS NUMERIC)
            ELSE NULL
        END as wan2_upload
    FROM v_circuit_summary
    WHERE 
        -- Must have Discount-Tire tag (or NULL for backward compatibility)
        (device_tags IS NULL OR 'Discount-Tire' = ANY(device_tags))
        -- Exclude satellite services
        AND COALESCE(wan1_speed, '') != 'Satellite'
        AND COALESCE(wan2_speed, '') != 'Satellite'
)
SELECT 
    network_name,
    device_tags,
    wan1_provider,
    wan1_speed,
    wan2_provider,
    wan2_speed,
    CASE 
        WHEN wan1_speed = 'Cell' AND wan2_speed = 'Cell' THEN 'Both circuits cellular'
        WHEN wan1_speed = 'Cell' OR wan1_provider ILIKE '%Cell%' OR wan1_provider ILIKE '%AT&T%' OR wan1_provider ILIKE '%Verizon%' THEN 'Cell on WAN1'
        WHEN wan2_speed = 'Cell' OR wan2_provider ILIKE '%Cell%' OR wan2_provider ILIKE '%AT&T%' OR wan2_provider ILIKE '%Verizon%' THEN 'Cell on WAN2'
    END as cellular_status,
    CASE 
        WHEN wan1_download < 100.0 OR wan1_upload <= 10.0 THEN 'Low speed on WAN1'
        WHEN wan2_download < 100.0 OR wan2_upload <= 10.0 THEN 'Low speed on WAN2'
    END as low_speed_circuit,
    CASE
        WHEN (wan1_speed = 'Cell' AND wan2_speed = 'Cell') OR
             ((wan1_speed = 'Cell' OR wan1_provider ILIKE '%Cell%' OR wan1_provider ILIKE '%AT&T%' OR wan1_provider ILIKE '%Verizon%') AND
              (wan2_speed = 'Cell' OR wan2_provider ILIKE '%Cell%' OR wan2_provider ILIKE '%AT&T%' OR wan2_provider ILIKE '%Verizon%'))
        THEN 'Both cellular'
        WHEN ((wan1_download < 100.0 OR wan1_upload <= 10.0) AND 
              (wan2_speed = 'Cell' OR wan2_provider ILIKE '%Cell%' OR wan2_provider ILIKE '%AT&T%' OR wan2_provider ILIKE '%Verizon%')) OR
             ((wan2_download < 100.0 OR wan2_upload <= 10.0) AND 
              (wan1_speed = 'Cell' OR wan1_provider ILIKE '%Cell%' OR wan1_provider ILIKE '%AT&T%' OR wan1_provider ILIKE '%Verizon%'))
        THEN 'Low speed + cellular'
    END as not_vision_ready_reason
FROM circuit_data
WHERE 
    -- Scenario 1: BOTH circuits are cellular
    -- Scenario 2: One circuit has low speed AND the other is cellular
    (
        -- Scenario 1: Both WAN1 and WAN2 are cellular
        (wan1_speed = 'Cell' AND wan2_speed = 'Cell')
        OR
        (wan1_speed = 'Cell' AND 
         (wan2_provider ILIKE '%AT&T%' OR wan2_provider ILIKE '%Verizon%' OR 
          wan2_provider ILIKE '%VZW%' OR wan2_provider ILIKE '%Cell%' OR 
          wan2_provider ILIKE '%Cellular%' OR wan2_provider ILIKE '%Wireless%'))
        OR
        (wan2_speed = 'Cell' AND 
         (wan1_provider ILIKE '%AT&T%' OR wan1_provider ILIKE '%Verizon%' OR 
          wan1_provider ILIKE '%VZW%' OR wan1_provider ILIKE '%Cell%' OR 
          wan1_provider ILIKE '%Cellular%' OR wan1_provider ILIKE '%Wireless%'))
        OR
        ((wan1_provider ILIKE '%AT&T%' OR wan1_provider ILIKE '%Verizon%' OR 
          wan1_provider ILIKE '%VZW%' OR wan1_provider ILIKE '%Cell%' OR 
          wan1_provider ILIKE '%Cellular%' OR wan1_provider ILIKE '%Wireless%') 
         AND 
         (wan2_provider ILIKE '%AT&T%' OR wan2_provider ILIKE '%Verizon%' OR 
          wan2_provider ILIKE '%VZW%' OR wan2_provider ILIKE '%Cell%' OR 
          wan2_provider ILIKE '%Cellular%' OR wan2_provider ILIKE '%Wireless%'))
        OR
        -- Scenario 2: WAN1 is low speed and WAN2 is cellular
        (wan1_download IS NOT NULL AND wan1_upload IS NOT NULL 
         AND (wan1_download < 100.0 OR wan1_upload <= 10.0)
         AND (wan2_speed = 'Cell' OR wan2_provider ILIKE '%AT&T%' OR 
              wan2_provider ILIKE '%Verizon%' OR wan2_provider ILIKE '%VZW%' OR
              wan2_provider ILIKE '%Cell%' OR wan2_provider ILIKE '%Cellular%' OR 
              wan2_provider ILIKE '%Wireless%'))
        OR
        -- Scenario 2: WAN2 is low speed and WAN1 is cellular
        (wan2_download IS NOT NULL AND wan2_upload IS NOT NULL 
         AND (wan2_download < 100.0 OR wan2_upload <= 10.0)
         AND (wan1_speed = 'Cell' OR wan1_provider ILIKE '%AT&T%' OR 
              wan1_provider ILIKE '%Verizon%' OR wan1_provider ILIKE '%VZW%' OR
              wan1_provider ILIKE '%Cell%' OR wan1_provider ILIKE '%Cellular%' OR 
              wan1_provider ILIKE '%Wireless%'))
    )
ORDER BY network_name;