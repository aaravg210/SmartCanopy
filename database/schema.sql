-- SmartCanopy Database Schema
-- PostgreSQL 16+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================================================
-- PLANT SPECIES TABLE
-- ============================================================================
CREATE TABLE plant_species (
    species_id VARCHAR(10) PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    common_name VARCHAR(255) NOT NULL,
    family VARCHAR(100),

    -- Growth characteristics
    mature_height_ft_min INTEGER,
    mature_height_ft_max INTEGER,
    mature_spread_ft_min INTEGER,
    mature_spread_ft_max INTEGER,
    growth_rate VARCHAR(20) CHECK (growth_rate IN ('slow', 'medium', 'fast')),

    -- Hardiness
    hardiness_zone_min INTEGER CHECK (hardiness_zone_min >= 1 AND hardiness_zone_min <= 13),
    hardiness_zone_max INTEGER CHECK (hardiness_zone_max >= 1 AND hardiness_zone_max <= 13),

    -- Environmental preferences
    sunlight VARCHAR(50) CHECK (sunlight IN ('full_sun', 'partial_shade', 'shade', 'full_sun_partial_shade')),
    soil_types JSONB,  -- ["clay", "loam", "sandy"]
    moisture_tolerance VARCHAR(50),
    drought_tolerant BOOLEAN DEFAULT FALSE,

    -- Environmental benefits (from i-Tree)
    co2_sequestration_kg_year FLOAT,
    air_pollution_removal_kg_year FLOAT,
    stormwater_gallons_year FLOAT,
    energy_savings_kwh_year FLOAT,

    -- Classification
    native_regions JSONB,  -- ["california", "pacific_northwest", "southeast"]
    tree_type VARCHAR(50) CHECK (tree_type IN ('deciduous', 'evergreen', 'conifer')),
    purposes JSONB,  -- ["shade", "ornamental", "wildlife", "street_tree", "privacy"]

    -- Maintenance
    maintenance_level VARCHAR(20) CHECK (maintenance_level IN ('low', 'medium', 'high')),
    pest_resistance VARCHAR(20) CHECK (pest_resistance IN ('low', 'medium', 'high')),
    disease_resistance VARCHAR(20) CHECK (disease_resistance IN ('low', 'medium', 'high')),

    -- Pricing (base costs in USD)
    price_sapling FLOAT,
    price_6ft FLOAT,
    price_8ft FLOAT,
    price_10ft FLOAT,

    -- OCF / VTA program metadata
    vta_approved BOOLEAN DEFAULT FALSE,    -- On OCF Approved Tree Species List
    csj_street_tree BOOLEAN DEFAULT FALSE, -- City of San Jose approved street tree
    fall_color BOOLEAN DEFAULT FALSE,      -- Notable fall foliage color
    flowers BOOLEAN DEFAULT FALSE,         -- Showy ornamental flowers
    ocf_notes TEXT,                        -- Per-species notes

    -- Metadata
    image_url VARCHAR(500),
    description TEXT,
    planting_instructions TEXT,
    maintenance_notes JSONB,  -- Structured maintenance data

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_hardiness CHECK (hardiness_zone_min <= hardiness_zone_max),
    CONSTRAINT valid_height CHECK (mature_height_ft_min <= mature_height_ft_max),
    CONSTRAINT valid_spread CHECK (mature_spread_ft_min <= mature_spread_ft_max)
);

-- Indexes for plant_species
CREATE INDEX idx_hardiness ON plant_species(hardiness_zone_min, hardiness_zone_max);
CREATE INDEX idx_native ON plant_species USING GIN(native_regions);
CREATE INDEX idx_purposes ON plant_species USING GIN(purposes);
CREATE INDEX idx_tree_type ON plant_species(tree_type);
CREATE INDEX idx_growth_rate ON plant_species(growth_rate);

-- Full-text search index
CREATE INDEX idx_species_search ON plant_species USING GIN(
    to_tsvector('english', common_name || ' ' || scientific_name)
);

-- ============================================================================
-- PLANTING SITES TABLE
-- ============================================================================
CREATE TABLE planting_sites (
    site_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL,

    -- Location
    address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    zip_code VARCHAR(10),

    -- Site characteristics (from CV model)
    location_pixels JSONB,  -- {x: int, y: int}
    area_pixels INTEGER,
    avg_ndvi FLOAT CHECK (avg_ndvi >= -1 AND avg_ndvi <= 1),
    avg_slope FLOAT CHECK (avg_slope >= 0),
    suitability_score FLOAT CHECK (suitability_score >= 0 AND suitability_score <= 1),

    -- Infrastructure context (from OSM)
    osm_data JSONB,  -- roads, buildings, parking GeoJSON
    exclusion_warnings JSONB,  -- Array of warning messages

    -- Imagery references
    rgb_image_path TEXT,
    ndvi_image_path TEXT,
    slope_image_path TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for planting_sites
CREATE INDEX idx_analysis_id ON planting_sites(analysis_id);
CREATE INDEX idx_address ON planting_sites(address);
CREATE INDEX idx_location ON planting_sites(latitude, longitude);
CREATE INDEX idx_suitability ON planting_sites(suitability_score DESC);
CREATE INDEX idx_zip_code ON planting_sites(zip_code);

-- ============================================================================
-- CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,  -- Future: user authentication
    session_id VARCHAR(255),  -- For anonymous users

    -- Context
    address TEXT,
    site_ids JSONB,  -- Array of planting_site UUIDs

    -- Conversation state
    messages JSONB,  -- Claude message history
    current_phase VARCHAR(50) CHECK (current_phase IN (
        'exploration', 'recommendation', 'planning', 'completed'
    )),

    -- Metadata
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,

    -- Settings
    user_preferences JSONB  -- Budget, aesthetic preferences, etc.
);

-- Indexes for conversations
CREATE INDEX idx_user_id ON conversations(user_id);
CREATE INDEX idx_session_id ON conversations(session_id);
CREATE INDEX idx_started_at ON conversations(started_at DESC);
CREATE INDEX idx_completed ON conversations(completed);

-- ============================================================================
-- RECOMMENDATIONS TABLE
-- ============================================================================
CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    site_id UUID REFERENCES planting_sites(site_id) ON DELETE CASCADE,
    species_id VARCHAR(10) REFERENCES plant_species(species_id),

    -- Recommendation context
    suitability_score FLOAT CHECK (suitability_score >= 0 AND suitability_score <= 1),
    reasoning TEXT,
    quantity INTEGER DEFAULT 1,
    tree_size VARCHAR(20) CHECK (tree_size IN ('sapling', '6ft', '8ft', '10ft')),

    -- Calculated benefits
    estimated_cost FLOAT,
    environmental_benefits JSONB,  -- CO2, stormwater, etc.

    -- User actions
    user_selected BOOLEAN DEFAULT FALSE,
    user_feedback TEXT,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for recommendations
CREATE INDEX idx_conversation_id ON recommendations(conversation_id);
CREATE INDEX idx_site_id ON recommendations(site_id);
CREATE INDEX idx_species_id ON recommendations(species_id);
CREATE INDEX idx_user_selected ON recommendations(user_selected);
CREATE INDEX idx_created_at ON recommendations(created_at DESC);

-- ============================================================================
-- HARDINESS ZONES CACHE TABLE
-- ============================================================================
CREATE TABLE hardiness_zones (
    zip_code VARCHAR(10) PRIMARY KEY,
    hardiness_zone VARCHAR(5) NOT NULL,  -- e.g., "9b", "10a"
    zone_numeric INTEGER,  -- e.g., 9, 10

    -- Source metadata
    source VARCHAR(50) DEFAULT 'usda_api',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Additional climate data
    avg_min_temp_f INTEGER,  -- Average annual minimum temperature
    climate_data JSONB
);

CREATE INDEX idx_zone_numeric ON hardiness_zones(zone_numeric);

-- ============================================================================
-- TOOL EXECUTION LOG TABLE
-- ============================================================================
CREATE TABLE tool_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    tool_name VARCHAR(100) NOT NULL,
    input_parameters JSONB,
    output_result JSONB,

    -- Performance metrics
    execution_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,

    -- Error tracking
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tool_executions
CREATE INDEX idx_tool_conversation ON tool_executions(conversation_id);
CREATE INDEX idx_tool_name ON tool_executions(tool_name);
CREATE INDEX idx_executed_at ON tool_executions(executed_at DESC);
CREATE INDEX idx_success ON tool_executions(success);

-- ============================================================================
-- UPLOADED PHOTOS TABLE
-- ============================================================================
CREATE TABLE uploaded_photos (
    photo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    site_id UUID REFERENCES planting_sites(site_id),

    -- File information
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(50),

    -- Analysis results (from photo_analyzer tool)
    analysis_result JSONB,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for uploaded_photos
CREATE INDEX idx_photo_conversation ON uploaded_photos(conversation_id);
CREATE INDEX idx_photo_site ON uploaded_photos(site_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_plant_species_updated_at
    BEFORE UPDATE ON plant_species
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_planting_sites_updated_at
    BEFORE UPDATE ON planting_sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update last_message_at in conversations
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_message_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversations_last_message
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    WHEN (OLD.messages IS DISTINCT FROM NEW.messages)
    EXECUTE FUNCTION update_conversation_last_message();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Species with full environmental benefits
CREATE VIEW species_with_benefits AS
SELECT
    s.*,
    COALESCE(s.co2_sequestration_kg_year, 0) as co2_annual,
    COALESCE(s.stormwater_gallons_year, 0) as stormwater_annual,
    ROUND((s.co2_sequestration_kg_year * 20 * 51 / 1000)::numeric, 2) as lifetime_value_usd
FROM plant_species s;

-- View: Active conversations with site count
CREATE VIEW active_conversations AS
SELECT
    c.*,
    jsonb_array_length(c.site_ids) as site_count,
    jsonb_array_length(c.messages) as message_count
FROM conversations c
WHERE c.completed = FALSE;

-- View: Top recommended species (by selection frequency)
CREATE VIEW popular_species AS
SELECT
    s.species_id,
    s.common_name,
    s.scientific_name,
    COUNT(r.recommendation_id) as recommendation_count,
    COUNT(CASE WHEN r.user_selected THEN 1 END) as selection_count,
    ROUND(AVG(r.user_rating)::numeric, 2) as avg_rating
FROM plant_species s
LEFT JOIN recommendations r ON s.species_id = r.species_id
GROUP BY s.species_id, s.common_name, s.scientific_name
ORDER BY selection_count DESC, recommendation_count DESC;

-- ============================================================================
-- INITIAL DATA (Some common hardiness zones)
-- ============================================================================

-- Sample hardiness zones for major cities
INSERT INTO hardiness_zones (zip_code, hardiness_zone, zone_numeric, avg_min_temp_f) VALUES
('94102', '10b', 10, 35),  -- San Francisco
('10001', '7b', 7, 5),     -- New York City
('60601', '6a', 6, -10),   -- Chicago
('90001', '10a', 10, 30),  -- Los Angeles
('98101', '9a', 9, 20),    -- Seattle
('33101', '11a', 11, 40),  -- Miami
('78701', '9a', 9, 20),    -- Austin
('02101', '7a', 7, 0),     -- Boston
('80201', '5b', 5, -15),   -- Denver
('97201', '9a', 9, 20)     -- Portland
ON CONFLICT (zip_code) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE plant_species IS 'Catalog of tree species with growth characteristics and environmental benefits';
COMMENT ON TABLE planting_sites IS 'Analyzed planting sites from CV model with suitability scores';
COMMENT ON TABLE conversations IS 'User chat sessions with the AI agent';
COMMENT ON TABLE recommendations IS 'Tree species recommendations made by the agent';
COMMENT ON TABLE hardiness_zones IS 'Cached USDA hardiness zone data by ZIP code';
COMMENT ON TABLE tool_executions IS 'Log of all agent tool executions for monitoring';
COMMENT ON TABLE uploaded_photos IS 'User-uploaded site photos for analysis';

COMMENT ON COLUMN plant_species.species_id IS 'USDA PLANTS database symbol (e.g., ACPL for Acer platanoides)';
COMMENT ON COLUMN plant_species.co2_sequestration_kg_year IS 'Annual CO2 sequestration in kg/year for mature tree';
COMMENT ON COLUMN planting_sites.suitability_score IS 'CV model computed suitability (0-1), higher is better';
COMMENT ON COLUMN recommendations.environmental_benefits IS 'Projected benefits over time (JSON format)';
