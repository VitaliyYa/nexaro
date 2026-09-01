-- SmartRent SaaS Initial Database Migration
-- Multi-Tenant IoT Architecture with Row Level Security (RLS)

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- 2. Utility Functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = pg_catalog.now();
    RETURN NEW;
END;
$$;

-- 3. Properties Table
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    address TEXT,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_properties_owner_id ON properties(owner_id);

CREATE TRIGGER trg_properties_updated_at
BEFORE UPDATE ON properties
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 4. Devices Table
CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(64) NOT NULL,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    device_type VARCHAR(32) NOT NULL CHECK (device_type IN ('lock', 'relay', 'valve', 'climate', 'sensor')),
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (property_id, id)
);

CREATE INDEX IF NOT EXISTS idx_devices_property_type ON devices(property_id, device_type);

CREATE TRIGGER trg_devices_updated_at
BEFORE UPDATE ON devices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 5. Device Telemetry and Event Logs Table
CREATE TABLE IF NOT EXISTS device_logs (
    id BIGSERIAL PRIMARY KEY,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    device_id VARCHAR(64),
    topic VARCHAR(255) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_device_logs_property_created ON device_logs(property_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_logs_device_created ON device_logs(property_id, device_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_logs_created_retention ON device_logs(created_at);

-- 6. MQTT Edge Node Credentials Table (Hashed passwords for Mosquitto Auth Webhook)
CREATE TABLE IF NOT EXISTS mqtt_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mqtt_credentials_property ON mqtt_credentials(property_id);
CREATE INDEX IF NOT EXISTS idx_mqtt_credentials_username ON mqtt_credentials(username);

CREATE TRIGGER trg_mqtt_credentials_updated_at
BEFORE UPDATE ON mqtt_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 7. Smart Locks Encrypted PIN Codes Table
CREATE TABLE IF NOT EXISTS property_pins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    device_id VARCHAR(64) NOT NULL,
    pin_encrypted TEXT NOT NULL,
    pin_name VARCHAR(100) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_property_pins_lookup ON property_pins(property_id, device_id, is_active);

CREATE TRIGGER trg_property_pins_updated_at
BEFORE UPDATE ON property_pins
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 8. Audit Logs Table (Physical Access & Security Operations)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    action VARCHAR(64) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_property_created ON audit_logs(property_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- 9. Row Level Security (RLS) Policies
-- -----------------------------------------------------------------------------

-- Enable RLS on all tables
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mqtt_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_pins ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Properties Policies
CREATE POLICY "Users can view own properties"
ON properties FOR SELECT
TO authenticated
USING (owner_id = auth.uid());

CREATE POLICY "Users can insert own properties"
ON properties FOR INSERT
TO authenticated
WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Users can update own properties"
ON properties FOR UPDATE
TO authenticated
USING (owner_id = auth.uid())
WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Users can delete own properties"
ON properties FOR DELETE
TO authenticated
USING (owner_id = auth.uid());

-- Devices Policies
CREATE POLICY "Users can view own property devices"
ON devices FOR SELECT
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own property devices"
ON devices FOR INSERT
TO authenticated
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can update own property devices"
ON devices FOR UPDATE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
)
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own property devices"
ON devices FOR DELETE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

-- Device Logs Policies
CREATE POLICY "Users can view own property logs"
ON device_logs FOR SELECT
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own property logs"
ON device_logs FOR INSERT
TO authenticated
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

-- MQTT Credentials Policies
CREATE POLICY "Users can view own property mqtt credentials"
ON mqtt_credentials FOR SELECT
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own property mqtt credentials"
ON mqtt_credentials FOR INSERT
TO authenticated
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can update own property mqtt credentials"
ON mqtt_credentials FOR UPDATE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
)
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own property mqtt credentials"
ON mqtt_credentials FOR DELETE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

-- Property PINs Policies
CREATE POLICY "Users can view own property pins"
ON property_pins FOR SELECT
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own property pins"
ON property_pins FOR INSERT
TO authenticated
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can update own property pins"
ON property_pins FOR UPDATE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
)
WITH CHECK (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own property pins"
ON property_pins FOR DELETE
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

-- Audit Logs Policies
CREATE POLICY "Users can view own property audit logs"
ON audit_logs FOR SELECT
TO authenticated
USING (
    property_id IN (
        SELECT id FROM properties WHERE owner_id = auth.uid()
    )
);

CREATE POLICY "Users can insert audit log entries"
ON audit_logs FOR INSERT
TO authenticated
WITH CHECK (
    user_id = auth.uid()
    AND (
        property_id IS NULL OR
        property_id IN (SELECT id FROM properties WHERE owner_id = auth.uid())
    )
);

-- -----------------------------------------------------------------------------
-- 10. pg_cron Scheduled Maintenance (90-Day Retention Policy)
-- -----------------------------------------------------------------------------

-- Daily cleanup at 03:00 UTC
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        PERFORM cron.schedule(
            'cleanup-device-logs-90-days',
            '0 3 * * *',
            $cron$DELETE FROM device_logs WHERE created_at < now() - INTERVAL '90 days'$cron$
        );
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron extension not available or permissions restricted in current context; please register cron job in Supabase dashboard';
END;
$$;
