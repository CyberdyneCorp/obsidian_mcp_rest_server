-- Initialize PostgreSQL with required extensions
-- Note: Graph creation is handled by Alembic migrations

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE and set search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Grant permissions for AGE
GRANT USAGE ON SCHEMA ag_catalog TO obsidian;
GRANT ALL ON ALL TABLES IN SCHEMA ag_catalog TO obsidian;
