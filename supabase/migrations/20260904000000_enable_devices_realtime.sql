-- Enable Realtime for the devices table
-- Ensures postgres_changes events are emitted to authorized frontend clients via RLS

-- 1. Set replica identity to full so that old records are available in updates/deletes if needed
ALTER TABLE devices REPLICA IDENTITY FULL;

-- 2. Add devices table to the Supabase Realtime publication
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'devices'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE devices;
    END IF;
END $$;
