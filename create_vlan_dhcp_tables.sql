-- Create VLAN/DHCP/Network Configuration Tables
-- For DSR Circuits Network Infrastructure Management System
-- Date: 2025-07-04

-- 1. Network VLANs Table
CREATE TABLE IF NOT EXISTS network_vlans (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(50) NOT NULL,
    network_name VARCHAR(100) NOT NULL,
    vlan_id INTEGER NOT NULL,
    vlan_name VARCHAR(100),
    appliance_ip INET,
    subnet VARCHAR(50),
    group_policy_id VARCHAR(20),
    dns_nameservers TEXT,
    dhcp_handling VARCHAR(50),
    dhcp_lease_time VARCHAR(20),
    dhcp_boot_options_enabled BOOLEAN DEFAULT FALSE,
    dhcp_relay_server_ips TEXT[], -- PostgreSQL array for multiple IPs
    interface_id VARCHAR(50),
    ipv6_enabled BOOLEAN DEFAULT FALSE,
    mandatory_dhcp_enabled BOOLEAN DEFAULT FALSE,
    reserved_ip_ranges JSONB DEFAULT '[]'::jsonb, -- Store as JSON for flexibility
    fixed_ip_assignments JSONB DEFAULT '{}'::jsonb, -- Store as JSON for flexibility
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(network_id, vlan_id)
);

-- Create indexes for network_vlans
CREATE INDEX IF NOT EXISTS idx_network_vlans_network_id ON network_vlans(network_id);
CREATE INDEX IF NOT EXISTS idx_network_vlans_network_name ON network_vlans(network_name);
CREATE INDEX IF NOT EXISTS idx_network_vlans_vlan_id ON network_vlans(vlan_id);
CREATE INDEX IF NOT EXISTS idx_network_vlans_subnet ON network_vlans(subnet);

-- 2. Network DHCP Options Table
CREATE TABLE IF NOT EXISTS network_dhcp_options (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(50) NOT NULL,
    vlan_id INTEGER NOT NULL,
    option_code VARCHAR(10) NOT NULL,
    option_type VARCHAR(20) NOT NULL, -- 'ip', 'text', etc.
    option_value TEXT NOT NULL,
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id, vlan_id) REFERENCES network_vlans(network_id, vlan_id) ON DELETE CASCADE
);

-- Create indexes for network_dhcp_options
CREATE INDEX IF NOT EXISTS idx_dhcp_options_network_vlan ON network_dhcp_options(network_id, vlan_id);
CREATE INDEX IF NOT EXISTS idx_dhcp_options_code ON network_dhcp_options(option_code);

-- 3. Network WAN Ports Table
CREATE TABLE IF NOT EXISTS network_wan_ports (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(50) NOT NULL,
    network_name VARCHAR(100) NOT NULL,
    port_number INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    port_type VARCHAR(20), -- 'trunk', 'access', etc.
    drop_untagged_traffic BOOLEAN DEFAULT FALSE,
    vlan_id INTEGER,
    allowed_vlans TEXT, -- Comma-separated VLAN list
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(network_id, port_number)
);

-- Create indexes for network_wan_ports
CREATE INDEX IF NOT EXISTS idx_wan_ports_network_id ON network_wan_ports(network_id);
CREATE INDEX IF NOT EXISTS idx_wan_ports_network_name ON network_wan_ports(network_name);
CREATE INDEX IF NOT EXISTS idx_wan_ports_port_number ON network_wan_ports(port_number);

-- 4. Enhance existing firewall_rules table (if it exists)
-- Add columns to track per-site firewall rules
ALTER TABLE firewall_rules ADD COLUMN IF NOT EXISTS network_id VARCHAR(50);
ALTER TABLE firewall_rules ADD COLUMN IF NOT EXISTS rule_order INTEGER;
ALTER TABLE firewall_rules ADD COLUMN IF NOT EXISTS is_site_specific BOOLEAN DEFAULT TRUE;
ALTER TABLE firewall_rules ADD COLUMN IF NOT EXISTS collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index for network-specific firewall rules
CREATE INDEX IF NOT EXISTS idx_firewall_rules_network_id ON firewall_rules(network_id);

-- 5. Create a summary view for quick network configuration overview
CREATE OR REPLACE VIEW v_network_config_summary AS
SELECT 
    nv.network_id,
    nv.network_name,
    COUNT(DISTINCT nv.vlan_id) as vlan_count,
    COUNT(DISTINCT CASE WHEN nv.dhcp_handling = 'Run a DHCP server' THEN nv.vlan_id END) as dhcp_server_count,
    COUNT(DISTINCT CASE WHEN nv.dhcp_handling = 'Relay DHCP to another server' THEN nv.vlan_id END) as dhcp_relay_count,
    COUNT(DISTINCT ndo.id) as dhcp_options_count,
    COUNT(DISTINCT wp.port_number) as wan_port_count,
    MAX(nv.collection_timestamp) as last_collected
FROM network_vlans nv
LEFT JOIN network_dhcp_options ndo ON nv.network_id = ndo.network_id AND nv.vlan_id = ndo.vlan_id
LEFT JOIN network_wan_ports wp ON nv.network_id = wp.network_id
GROUP BY nv.network_id, nv.network_name;

-- 6. Create a detailed VLAN configuration view
CREATE OR REPLACE VIEW v_vlan_details AS
SELECT 
    nv.*,
    ARRAY_AGG(
        DISTINCT jsonb_build_object(
            'code', ndo.option_code,
            'type', ndo.option_type,
            'value', ndo.option_value
        )
    ) FILTER (WHERE ndo.id IS NOT NULL) as dhcp_options
FROM network_vlans nv
LEFT JOIN network_dhcp_options ndo ON nv.network_id = ndo.network_id AND nv.vlan_id = ndo.vlan_id
GROUP BY nv.id, nv.network_id, nv.network_name, nv.vlan_id, nv.vlan_name, 
         nv.appliance_ip, nv.subnet, nv.group_policy_id, nv.dns_nameservers,
         nv.dhcp_handling, nv.dhcp_lease_time, nv.dhcp_boot_options_enabled,
         nv.dhcp_relay_server_ips, nv.interface_id, nv.ipv6_enabled,
         nv.mandatory_dhcp_enabled, nv.reserved_ip_ranges, nv.fixed_ip_assignments,
         nv.collection_timestamp, nv.last_updated;

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON network_vlans TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON network_dhcp_options TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON network_wan_ports TO your_app_user;
-- GRANT SELECT ON v_network_config_summary TO your_app_user;
-- GRANT SELECT ON v_vlan_details TO your_app_user;

-- Comments for documentation
COMMENT ON TABLE network_vlans IS 'Stores VLAN configurations for each Meraki network including DHCP settings';
COMMENT ON TABLE network_dhcp_options IS 'Stores individual DHCP options (codes 42, 66, 150, etc.) for each VLAN';
COMMENT ON TABLE network_wan_ports IS 'Stores WAN port configurations for each network';
COMMENT ON VIEW v_network_config_summary IS 'Summary view of network configurations for quick overview';
COMMENT ON VIEW v_vlan_details IS 'Detailed VLAN configuration view with aggregated DHCP options';