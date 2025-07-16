-- SQL statements to insert non-DSR circuits
-- These circuits exist in Meraki but not in DSR tracking


INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZN 04',
    'Primary',
    'Frontier',
    '20.0M x 20.0M',
    '12.39.141.194',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZN 04',
    'Secondary',
    'Digi',
    'Cell',
    '166.128.29.96',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 41',
    'Primary',
    'AT&T',
    '20.0M x 20.0M',
    '12.111.1.74',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 41',
    'Secondary',
    'Starlink',
    'Satellite',
    '143.105.158.34',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 56',
    'Primary',
    'ComcastAgg',
    '10.0M x 10.0M',
    '63.224.146.6',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 56',
    'Secondary',
    'Digi',
    'Cell',
    '108.147.172.60',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 63',
    'Primary',
    'Starlink',
    'Satellite',
    '143.105.158.128',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 63',
    'Secondary',
    'VZG Cell',
    'Cell',
    '174.218.25.166',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 64',
    'Primary',
    'Starlink',
    'Satellite',
    '143.105.59.156',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZP 64',
    'Secondary',
    'AT&T Cell',
    'Cell',
    '166.194.143.6',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZPB 20',
    'Primary',
    'Connected to Desert Ridge MX250',
    '',
    '98.175.209.47',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'AZPB 20',
    'Secondary',
    'Digi',
    'Cell',
    '166.128.221.236',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'BSM Test Network',
    'Primary',
    'BSM Lab in the Test Lab area of Scottsdale HQ',
    '',
    '166.184.132.8',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL_00',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.180.93.139',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL_00',
    'Secondary',
    'Charter Communications',
    '600.0M x 35.0M',
    '98.152.193.10',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 17',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.176.201.18',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 17',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.180.159.133',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 20',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.179.15.126',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 20',
    'Secondary',
    'VZW Cell',
    'Cell',
    '192.168.0.151',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 29',
    'Primary',
    'AT&T',
    '',
    '12.3.118.66',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL 29',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.154.40.59',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL W01',
    'Primary',
    'Frontier Fiber',
    '1000.0M x 1000.0M',
    '47.178.4.124',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAL W01',
    'Secondary',
    'Digi',
    'Cell',
    '107.84.140.107',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN_00',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.81.183.205',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN_00',
    'Secondary',
    'AT&T',
    '300.0M x 300.0M',
    '108.86.147.217',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN 16',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.176.225.2',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN 16',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.156.31',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN 40',
    'Primary',
    'VZW Cell',
    'Cell',
    '166.253.101.36',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN 40',
    'Secondary',
    'Starlink',
    'Satellite',
    '143.105.116.247',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAN W02',
    'Primary',
    'AT&T Enterprises, LLC',
    '',
    '107.84.138.33',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS_00',
    'Primary',
    'AT&T',
    '300.0M x 300.0M',
    '76.210.250.113',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS_00',
    'Secondary',
    'Cox Communications',
    '300.0M x 30.0M',
    '98.178.226.110',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 35',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.176.206.178',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 35',
    'Secondary',
    'VZW Cell',
    'Cell',
    '192.168.0.151',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 40',
    'Primary',
    'Frontier Communications',
    '500.0M x 50.0M',
    '47.179.21.123',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 40',
    'Secondary',
    'Digi',
    'Cell',
    '107.84.138.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 41',
    'Primary',
    'Frontier Communications',
    '500.0M x 500.0M',
    '47.176.225.10',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 41',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.9.55',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 42',
    'Primary',
    'Cox Communications',
    '',
    '72.211.52.244',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 42',
    'Secondary',
    'VZW Cell',
    'Cell',
    '107.84.133.124',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 46',
    'Primary',
    'AT&T',
    '20.0M x 20.0M',
    '12.111.1.98',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'CAS 46',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.10.66',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Central Store Test',
    'Primary',
    'Unknown',
    '',
    '162.223.245.93',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD_00',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '173.164.63.45',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD_00',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '166.195.38.181',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 01',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.78.2.33',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 01',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.248.10.6',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 03',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.75.122.169',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 08',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.75.124.5',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 09',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.75.102.5',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 13',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.76.170.93',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 13',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.10.163',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 15',
    'Primary',
    'Comcast',
    '',
    '96.90.174.117',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 15',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.248.10.149',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 17',
    'Primary',
    'Comcast',
    '',
    '96.76.168.233',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 17',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.10.102',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 22',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '74.92.221.65',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 22',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.246.91.127',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 41',
    'Primary',
    'Lumen',
    '300.0M x 300.0M',
    '65.56.84.242',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'COD 41',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.156.147.159',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Cog 02',
    'Primary',
    'Comcast',
    '750.0M x 35.0M',
    '50.198.210.201',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Cog 02',
    'Secondary',
    'Community Broadband Network',
    '100.0 M',
    '74.114.7.176',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Corporate Store0',
    'Primary',
    'Corporate Store 0 Replica requested by Paul Higel Located in Endpoint Room Named MAR_01 in AD TEST STORE',
    '',
    '184.183.25.158',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Desert Ridge',
    'Primary',
    'Cox Network 500 Circuit ID 23.HMXX.126497 Acct 2318296-02 AT&T ADI',
    '100.0 M',
    '98.175.209.47',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'DR VTV Test Lab II',
    'Primary',
    'Unknown',
    '',
    '98.175.209.47',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'East Store Test',
    'Primary',
    'Unknown',
    '',
    '73.7.36.236',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'EQX-DataCenter-WA',
    'Primary',
    'Unknown',
    '',
    '149.97.240.36',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'EQX-DataCenter-WA',
    'Primary',
    'Unknown',
    '',
    '149.97.240.36',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'EQX-OOB-WA-02',
    'Primary',
    'Unknown',
    '',
    '0.0.0.0',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Flight Department',
    'Primary',
    'Cox Communications Inc.',
    '',
    '70.175.22.38',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Flight Department',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.246.93.56',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Flight Department - Pilot',
    'Primary',
    'Cox Communications',
    '',
    '68.227.44.114',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'FP-DAL-OOBMGMT-01',
    'Primary',
    'Unknown',
    '',
    '107.80.162.243',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'FP-DAL-OOBMGMT-02',
    'Primary',
    'Unknown',
    '',
    '107.80.179.161',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'FP-iSeries-ATL',
    'Primary',
    'Unknown',
    '',
    '209.51.139.244',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'FP-iSeries-DAL',
    'Primary',
    'Unknown',
    '',
    '162.223.245.92',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'FP-iSeries-DAL',
    'Primary',
    'Unknown',
    '',
    '162.223.245.92',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'GAACALLCNTR',
    'Primary',
    'AT&T',
    '300.0M x 300.0M',
    '104.184.151.49',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'GAACALLCNTR',
    'Secondary',
    'Charter Communications',
    '100.0M x 30.0M',
    '47.46.162.82',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'GAA W00',
    'Primary',
    'AT&T Broadband II',
    '300.0M x 30.0M',
    '45.22.51.193',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'GAA W00',
    'Secondary',
    'Digi',
    'Cell',
    '107.85.128.174',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'HPL_00',
    'Primary',
    'This is a one man office for Todd Richards.',
    '',
    '24.43.139.54',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Igor Lab',
    'Primary',
    'Unknown',
    '',
    '107.127.197.67',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC_00',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.74.249.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC_00',
    'Secondary',
    'AT&T',
    '300.0M x 300.0M',
    '107.209.6.145',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 11',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.74.196.161',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 12',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.68.37.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 12',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.246.93.70',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 41',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '162.17.62.145',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 41',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.169.67.209',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 42',
    'Primary',
    'Oswego Static /32',
    '',
    '104.254.223.132',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 42',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.168.180.169',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 43',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '50.77.166.229',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 43',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.168.184.46',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 44',
    'Primary',
    'Static pool - Cinergy MetroNet',
    '',
    '217.180.239.153',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 44',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.151.178.22',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 45',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '96.84.93.81',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 45',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.7.243',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 46',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '96.70.60.26',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILC 46',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.253.101.118',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ILR 01',
    'Primary',
    'Comcast',
    '600.0M x 35.0M',
    '74.94.116.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INI_00',
    'Primary',
    'DSR Cincinnati Bell ADSL',
    '400.0M x 200.0M',
    '66.42.186.206',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INI_00',
    'Secondary',
    'Charter Communications',
    '600.0M x 35.0M',
    '71.66.89.90',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INI W01',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '50.195.198.237',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INI W01',
    'Secondary',
    'Private Customer - AT&T Internet Services',
    '',
    '99.33.34.9',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INW 02',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.72.115.9',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'INW 02',
    'Secondary',
    'Digi',
    'Cell',
    '107.85.135.19',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'KSK_00',
    'Primary',
    'Charter Communications',
    '600.0M x 35.0M',
    '150.220.245.70',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'KSK_00',
    'Secondary',
    'AT&T',
    '300.0M x 300.0M',
    '76.201.157.129',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MID W00',
    'Primary',
    'DSR - MIHW00',
    '',
    '173.167.236.165',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MIF 05',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.76.231.33',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MIF 05',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.246.93.149',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MIG 25',
    'Primary',
    'Comcast',
    '',
    '96.76.237.21',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MIG 25',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.163.165.215',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 02',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.75.157.169',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 02',
    'Secondary',
    'Starlink',
    'Satellite',
    '143.105.57.230',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 03',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.75.153.5',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 03',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.180.46.137',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 09',
    'Primary',
    'DSR Comcast',
    '750.0M x 35.0M',
    '73.228.210.242',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 09',
    'Secondary',
    'Digi',
    'Cell',
    '107.80.171.26',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 11',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.75.149.153',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 11',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.180.159.153',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 24',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.72.38.153',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 24',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.180.159.110',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 25',
    'Primary',
    'ComcastAgg',
    '',
    '73.94.13.48',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 25',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.246.93.76',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 29',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.75.159.233',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM 29',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.246.93.68',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MNM W01',
    'Primary',
    'Comcast',
    '',
    '50.211.20.237',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOO 01',
    'Primary',
    'ComcastAgg CableOne',
    '300.0M x 35.0M',
    '24.119.128.250',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOO 01',
    'Secondary',
    'Digi',
    'Cell',
    '107.127.155.138',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOO 04',
    'Primary',
    'Level 3',
    '300.0M x 300.0M',
    '4.35.182.162',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOO 04',
    'Secondary',
    'Verizon',
    'Cell',
    '63.43.232.131',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOSW 01',
    'Primary',
    'arco trucking08162011143812942',
    '',
    '108.192.139.225',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'MOSW 01',
    'Secondary',
    'Charter Communications LLC',
    '',
    '47.50.140.114',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Mt. Prospect Voice',
    'Primary',
    'AT&T BVOIP Asset ID IZEC561522ATI',
    '',
    '208.83.9.194',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NCC_00',
    'Primary',
    'Charter Communications',
    '600.0M x 35.0M',
    '66.57.166.218',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NMA_00',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.64.151.241',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NMA_00',
    'Secondary',
    'CenturyLink',
    '100.0M x 10.0M',
    '168.103.98.137',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NMA 10',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.77.22.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NMA 10',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.7.28',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NMACALLCNTR',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '74.92.206.225',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVL_00',
    'Primary',
    'Cox Communications',
    '',
    '24.234.187.243',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVL_00',
    'Secondary',
    'Digi',
    'Cell',
    '107.84.130.99',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVL 16',
    'Primary',
    'VZW Cell',
    'Cell',
    '174.205.97.122',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVL 16',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.129.138',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVL W01',
    'Primary',
    'Cox Communications',
    '',
    '24.120.171.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NVRB04',
    'Primary',
    'TEST STORE NOT PRODUCTION',
    '',
    '67.40.71.2',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 01',
    'Primary',
    'DUNN TIRE',
    '',
    '208.105.133.178',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 01',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.80',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 02',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.218',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 02',
    'Secondary',
    'VZW Cell',
    'Cell',
    '71.186.165.101',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 03',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.1.218',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 03',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.93',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 04',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.1.162',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 04',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.81',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 05',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.1.226',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 05',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.95',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 06',
    'Primary',
    'DUNN TIRE',
    '',
    '208.105.133.130',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 06',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.71',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 07',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.74',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 07',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.94',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 08',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.58',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYB 08',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 01',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.11.226',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 01',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.84',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 02',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.7.226',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 02',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.74',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 03',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.66',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYF 03',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.88',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 02',
    'Primary',
    'Charter Communications Inc',
    '',
    '69.193.88.50',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 02',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.85',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 03',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.50',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 03',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.90',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 04',
    'Primary',
    'DUNN TIRE',
    '',
    '198.179.114.202',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 04',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.86',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 05',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.8.202',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 05',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.92',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 06',
    'Primary',
    'DUNN TIRE',
    '',
    '208.105.133.146',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 06',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.89',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 07',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.0.42',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYR 07',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.91',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 01',
    'Primary',
    'DUNN TIRE',
    '',
    '208.105.133.234',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 01',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.96',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 02',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.3.218',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 02',
    'Secondary',
    'VZW Cell',
    'Cell',
    '71.115.157.125',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 03',
    'Primary',
    'DUNN TIRE',
    '',
    '50.75.1.82',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 03',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.246.91.126',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 04',
    'Primary',
    'DUNN TIRE',
    '',
    '24.97.155.210',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'NYS 04',
    'Secondary',
    'VZW Cell',
    'Cell',
    '96.238.150.152',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ORP 01',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.95.155.237',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ORP 01',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.132.163',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ORP 05',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.71.178.237',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'ORP 05',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.253.100.70',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 03',
    'Primary',
    'DUNN TIRE',
    '',
    '162.155.223.226',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 03',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.87',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 04',
    'Primary',
    'DUNN TIRE',
    '',
    '198.24.105.90',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 04',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.77',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 05',
    'Primary',
    'DUNN TIRE',
    '',
    '96.11.200.42',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'PAN 05',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.127.197.82',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Strike Team Lab',
    'Primary',
    'Connected to 1B.4.4.10 Uplink to IDF1B-Core VLAN 200',
    '',
    '184.183.25.158',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TNM 01',
    'Primary',
    'Comcast',
    '',
    '96.87.191.129',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TNM 01',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.168.231.131',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TNN_00',
    'Primary',
    'AT&T',
    '300.0M x 300.0M',
    '162.203.252.161',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TNN_00',
    'Secondary',
    'Comcast',
    '300.0M x 30.0M',
    '96.69.101.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH_00',
    'Primary',
    'AT&T',
    '300.0M x 300.0M',
    '162.201.19.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH_00',
    'Secondary',
    'Comcast',
    '300.0M x 30.0M',
    '96.85.28.9',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 14',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '96.95.234.13',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 14',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.9.212',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 25',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '50.209.123.141',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 25',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.168.231.150',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 28',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.77.135.141',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 44',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '50.194.161.17',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 44',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.168.184.33',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 64',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.73.126.69',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 70',
    'Primary',
    'Comcast',
    '300.0M x 35.0M',
    '96.91.38.197',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 70',
    'Secondary',
    'Digi',
    'Cell',
    '107.80.163.194',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 86',
    'Primary',
    'Comcast',
    '300.0M x 25.0M',
    '96.73.122.161',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH 86',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.180.159.109',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXHT00',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '75.148.163.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH W00',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '50.210.214.114',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'TXH W00',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '76.200.214.154',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 02',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.73.19.25',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 02',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.137.240',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 13',
    'Primary',
    'Comcast',
    '',
    '96.73.28.153',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 13',
    'Secondary',
    'VZW Cell',
    'Cell',
    '107.84.137.94',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 15',
    'Primary',
    'Comcast',
    '600.0M x 35.0M',
    '50.77.46.93',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 15',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.10.40',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 17',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.73.31.129',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 17',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.248.10.39',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 19',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '173.14.230.17',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS 19',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.9.53',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS W01',
    'Primary',
    'Comcast',
    '600.0M x 35.0M',
    '50.208.244.41',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS W01',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.158.66',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS W02',
    'Primary',
    'DSR Comcast Cable',
    '600.0M x 35.0M',
    '50.215.217.150',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'UTS W02',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.168.231.163',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAF 01 - appliance',
    'Primary',
    'Comcast',
    '250.0M x 25.0M',
    '50.211.60.57',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAF 01 - appliance',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.103.92',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAR 01',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '75.150.59.61',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAR 01',
    'Secondary',
    'VZW Cell',
    'Cell',
    '107.85.158.120',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAR 08',
    'Primary',
    'Verizon',
    'Cell',
    '74.110.158.210',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VAR 08',
    'Secondary',
    'Comcast',
    '',
    '50.217.201.18',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VISION_Store0',
    'Primary',
    'Cox Communications',
    '',
    '174.79.27.198',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'VISION_Test_Lab_MinesW',
    'Primary',
    'SW03 relocated to the Vison test lab',
    '',
    '98.186.252.234',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAE 01',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '50.245.147.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAE 01',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.248.7.34',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAE 02',
    'Primary',
    'Comcast',
    '300.0M x 300.0M',
    '173.160.129.105',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAE 02',
    'Secondary',
    'Verizon Business',
    'Cell',
    '166.248.10.12',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS_00',
    'Primary',
    'Ziply Fiber',
    '',
    '50.34.4.82',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS_00',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.84.139.175',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 03',
    'Primary',
    'Comcast',
    '',
    '75.151.125.173',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 03',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.9.44',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 05',
    'Primary',
    'VZW Cell',
    'Cell',
    '98.97.97.110',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 05',
    'Secondary',
    '- Accelerated AT&T',
    '',
    '166.180.159.131',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 09',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '173.160.199.17',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 09',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.138.128',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 11',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '96.74.20.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 11',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.132.102',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 12',
    'Primary',
    'Starlink',
    'Satellite',
    '98.97.101.40',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 12',
    'Secondary',
    'Digi',
    'Cell',
    '0.0.0.0',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 14',
    'Primary',
    'Comcast',
    '300.0M x 30.0M',
    '75.151.126.225',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 14',
    'Secondary',
    'Digi',
    'Cell',
    '166.184.131.38',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 23',
    'Primary',
    'ComcastAgg CLink',
    '10.0M x 1.0M',
    '65.101.138.25',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 23',
    'Secondary',
    'Digi',
    'Cell',
    '107.84.141.91',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 24',
    'Primary',
    'Comcast',
    '',
    '96.76.50.129',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS 24',
    'Secondary',
    'VZW Cell',
    'Cell',
    '166.248.9.37',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS W00',
    'Primary',
    'Comcast',
    '200.0M x 200.0M',
    '50.210.47.185',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WAS W00',
    'Secondary',
    'Digi Cell',
    'Cell',
    '166.184.139.176',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDCA 01',
    'Primary',
    'Frontier Communications Corporation',
    '',
    '47.176.153.146',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDCA 01',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.84.137.79',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDGA01',
    'Primary',
    'Private Customer - AT&T Internet Services',
    '',
    '104.61.91.209',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDGA01',
    'Secondary',
    'AT&T Enterprises, LLC',
    '',
    '107.85.142.107',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDIL 01',
    'Primary',
    'Comcast Cable Communications, LLC',
    '',
    '173.165.103.213',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDIL 01',
    'Secondary',
    'Private Customer - AT&T Internet Services',
    '',
    '104.185.193.161',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDTD 01',
    'Primary',
    'AT&T',
    '1000.0M x 1000.0M',
    '107.132.157.73',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'WDTD 01',
    'Secondary',
    'ATT',
    '100.0M x 10.0M',
    '166.168.180.168',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'West Store Test',
    'Primary',
    'Unknown',
    '',
    '184.183.25.158',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);

INSERT INTO circuits (
    site_name,
    circuit_purpose,
    provider_name,
    details_ordered_service_speed,
    ip_address_start,
    status,
    billing_monthly_cost,
    source_system,
    created_at,
    updated_at
) VALUES (
    'Wyomissing Voice',
    'Primary',
    'AT&T BVOIP Asset ID IZEC561531ATI',
    '',
    '208.75.157.194',
    'Enabled',
    0.00,
    'Non-DSR',
    NOW(),
    NOW()
);
