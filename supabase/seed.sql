-- SmartRent Development Seed Data
-- ---------------------------------

-- Note: In Supabase, auth.users is managed by GoTrue.
-- For local testing, mock users or test IDs can be inserted or linked.

-- Insert demo property (assuming a test user ID: '00000000-0000-0000-0000-000000000001')
-- INSERT INTO properties (id, owner_id, name, address, timezone)
-- VALUES (
--     'a0000000-0000-0000-0000-000000000001',
--     '00000000-0000-0000-0000-000000000001',
--     'Apartment 101 - City Center',
--     '123 Main Street, Apt 101, Moscow',
--     'Europe/Moscow'
-- ) ON CONFLICT DO NOTHING;

-- Demo devices
-- INSERT INTO devices (id, property_id, device_type, name, is_active, settings)
-- VALUES
--     ('lock_front', 'a0000000-0000-0000-0000-000000000001', 'lock', 'Front Entrance Lock', true, '{"auto_lock_seconds": 10}'::jsonb),
--     ('relay_boiler', 'a0000000-0000-0000-0000-000000000001', 'relay', 'Boiler Power Relay', true, '{}'::jsonb),
--     ('valve_kitchen', 'a0000000-0000-0000-0000-000000000001', 'valve', 'Kitchen Water Shutoff', true, '{}'::jsonb),
--     ('ac_livingroom', 'a0000000-0000-0000-0000-000000000001', 'climate', 'Living Room AC', true, '{"max_temp": 30, "min_temp": 16}'::jsonb)
-- ON CONFLICT DO NOTHING;
