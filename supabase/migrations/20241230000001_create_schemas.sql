-- Migration: 20241230000001_create_schemas.sql
-- Description: Create bronze, silver, gold schemas for Medallion architecture
-- Author: InsightPulseAI

-- Create schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Grant usage to authenticated role
GRANT USAGE ON SCHEMA bronze TO authenticated;
GRANT USAGE ON SCHEMA silver TO authenticated;
GRANT USAGE ON SCHEMA gold TO authenticated;

-- Grant usage to service_role for backend operations
GRANT ALL ON SCHEMA bronze TO service_role;
GRANT ALL ON SCHEMA silver TO service_role;
GRANT ALL ON SCHEMA gold TO service_role;

-- Add comments for documentation
COMMENT ON SCHEMA bronze IS 'Raw data layer - Odoo webhooks, imports, external sources';
COMMENT ON SCHEMA silver IS 'Cleaned and normalized business entities';
COMMENT ON SCHEMA gold IS 'Aggregated views and reporting tables';
