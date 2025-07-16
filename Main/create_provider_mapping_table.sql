-- Provider Mapping Table for 100% DSR-ARIN Matching
-- This table handles known provider name variations, rebrands, and aliases

-- Drop existing table if it exists
DROP TABLE IF EXISTS provider_mappings;

-- Create provider mappings table
CREATE TABLE provider_mappings (
    id SERIAL PRIMARY KEY,
    dsr_provider VARCHAR(255) NOT NULL,
    arin_provider VARCHAR(255) NOT NULL,
    mapping_type VARCHAR(50) NOT NULL, -- 'rebrand', 'division', 'alias', 'eb2_prefix', 'service_suffix'
    notes TEXT,
    confidence_score INTEGER DEFAULT 100, -- 0-100 confidence in the mapping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast lookups
CREATE INDEX idx_provider_mappings_dsr ON provider_mappings(LOWER(dsr_provider));
CREATE INDEX idx_provider_mappings_arin ON provider_mappings(LOWER(arin_provider));
CREATE INDEX idx_provider_mappings_type ON provider_mappings(mapping_type);

-- Insert known provider mappings based on analysis

-- 1. Rebranding Cases
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('Brightspeed', 'CenturyLink', 'rebrand', 'Brightspeed acquired CenturyLink assets in 2022', 100),
('Sparklight', 'Cable One, Inc.', 'rebrand', 'Cable One rebranded to Sparklight in 2019', 100),
('Cincinnati Bell', 'Altafiber Inc', 'rebrand', 'Cincinnati Bell rebranded to Altafiber in 2022', 100),
('Lumen', 'CenturyLink', 'rebrand', 'CenturyLink rebranded to Lumen in 2020', 100),
('Altice West', 'Optimum', 'division', 'Altice operates Optimum brand', 100),
('Lightpath', 'Optimum', 'division', 'Lightpath is enterprise division of Altice/Optimum', 90);

-- 2. EB2- Prefix Patterns
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('EB2-CenturyLink DSL', 'CenturyLink', 'eb2_prefix', 'EB2 prefix indicates internal designation', 100),
('EB2-Centurylink DSL', 'CenturyLink', 'eb2_prefix', 'EB2 prefix with lowercase variation', 100),
('EB2-Lumen DSL', 'CenturyLink', 'eb2_prefix', 'EB2-Lumen maps to CenturyLink (Lumen rebrand)', 100),
('EB2-Frontier Fiber', 'Frontier Communications', 'eb2_prefix', 'EB2 prefix for Frontier', 100),
('EB2-Spectrum', 'Charter Communications', 'eb2_prefix', 'EB2 prefix for Spectrum/Charter', 100),
('EB2-CableOne Cable', 'Cable One, Inc.', 'eb2_prefix', 'EB2 prefix for Cable One', 100),
('EB2-Windstream Kinetic', 'Windstream Communications', 'eb2_prefix', 'EB2 prefix for Windstream', 100),
('EB2-Consolidated Communications Fiber', 'Consolidated Communications', 'eb2_prefix', 'EB2 prefix for Consolidated', 100),
('EB2-Cox Cable', 'Cox Communications', 'eb2_prefix', 'EB2 prefix for Cox', 100),
('EB2-TDS DSL', 'TDS TELECOM', 'eb2_prefix', 'EB2 prefix for TDS', 100),
('EB2-Suddenlink Cable', 'Optimum', 'eb2_prefix', 'EB2 prefix for Suddenlink (now Optimum)', 95);

-- 3. Business Division Naming
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('Comcast Workplace', 'Comcast', 'division', 'Comcast Workplace is business division', 100),
('Comcast Workplace Cable', 'Comcast', 'division', 'Comcast Workplace Cable variant', 100),
('Cox Business/BOI', 'Cox Communications', 'division', 'Cox Business/BOI is business division', 100),
('Cox Business BOI | Extended Cable |', 'Cox Communications', 'division', 'Cox Business extended format', 100),
('Cox Business BOI Extended Cable', 'Cox Communications', 'division', 'Cox Business extended variant', 100),
('Cox Business', 'Cox Communications', 'division', 'Cox Business short form', 100),
('AT&T Broadband II', 'AT&T', 'division', 'AT&T Broadband II service tier', 100),
('AT&T ABF', 'AT&T', 'division', 'AT&T ABF variant', 100),
('AT&T ADI', 'AT&T', 'division', 'AT&T ADI variant', 100),
('Verizon Business', 'Verizon', 'division', 'Verizon Business division', 100);

-- 4. Known Aliases and DBA
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('TransWorld', 'FAIRNET LLC', 'alias', 'TransWorld operates as FAIRNET LLC', 95),
('Yelcot Communications', 'YELCOT TELEPHONE COMPANY', 'alias', 'Formal vs informal name', 95),
('Orbitel Communications', 'Orbitel Communications, LLC', 'alias', 'Missing LLC suffix', 100),
('Charter', 'Charter Communications', 'alias', 'Short form', 100),
('Spectrum', 'Charter Communications', 'alias', 'Spectrum is Charter brand', 100),
('CenturyLink/Embarq', 'CenturyLink', 'alias', 'Embarq was acquired by CenturyLink', 100),
('CenturyLink/Qwest', 'CenturyLink', 'alias', 'Qwest was acquired by CenturyLink', 100),
('Mediacom/BOI', 'Mediacom', 'alias', 'Mediacom BOI variant', 100),
('Allo Communications', 'ALLO Communications LLC', 'alias', 'Missing LLC suffix', 100);

-- 5. Service Type Suffixes
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('CenturyLink Fiber Plus', 'CenturyLink', 'service_suffix', 'Fiber Plus is service type', 95),
('AGG Comcast', 'Comcast', 'service_suffix', 'AGG prefix variant', 95),
('ComcastAGG CLink DSL', 'CenturyLink', 'service_suffix', 'Comcast aggregated CenturyLink DSL', 90),
('ComcastAGG Comcast', 'Comcast', 'service_suffix', 'Comcast aggregated service', 95),
('Wyyerd Fiber', 'Wyyerd Group LLC', 'service_suffix', 'Fiber is service type', 95);

-- 6. Cellular/Wireless Variants  
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('Verizon Cell', 'Verizon', 'alias', 'Cellular service variant', 100),
('Cell', 'Verizon', 'alias', 'Generic cell often means Verizon', 80),
('Digi Cellular', 'Digi', 'service_suffix', 'Cellular service variant', 95),
('Starlink', 'SpaceX Services, Inc.', 'alias', 'Starlink is SpaceX service', 100);

-- Special handling for tricky cases
INSERT INTO provider_mappings (dsr_provider, arin_provider, mapping_type, notes, confidence_score) VALUES
('EB2-Centurylink DSL', 'Ocotillo Technologies, Inc.', 'special', 'Some CenturyLink DSL resold by Ocotillo in AZ', 70),
('Accelerated', '', 'ignore', 'Hardware vendor, not ISP', 100),
('DSR Comcast', 'Comcast', 'service_suffix', 'DSR prefix variant', 95),
('Not DSR AT&T | AT&T ADI |', 'AT&T', 'special', 'Complex AT&T variant', 90);

-- Add update trigger
CREATE OR REPLACE FUNCTION update_provider_mappings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_provider_mappings_timestamp
BEFORE UPDATE ON provider_mappings
FOR EACH ROW
EXECUTE FUNCTION update_provider_mappings_timestamp();

-- Grant permissions
GRANT SELECT ON provider_mappings TO PUBLIC;
GRANT INSERT, UPDATE, DELETE ON provider_mappings TO meraki_user;

-- Add comments
COMMENT ON TABLE provider_mappings IS 'Maps DSR provider names to ARIN provider names for 100% matching';
COMMENT ON COLUMN provider_mappings.mapping_type IS 'Type of mapping: rebrand, division, alias, eb2_prefix, service_suffix, special, ignore';
COMMENT ON COLUMN provider_mappings.confidence_score IS 'Confidence in the mapping accuracy (0-100)';