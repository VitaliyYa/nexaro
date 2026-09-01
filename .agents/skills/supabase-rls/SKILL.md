---
name: supabase-rls
description: >-
  Best practices and guidelines for Supabase PostgreSQL database design, Row Level Security (RLS)
  policies, multi-tenancy, service_role isolation, and pg_cron maintenance in SmartRent.
---

# Supabase RLS & Database Security Guide

This skill specifies database modeling, Row Level Security (RLS), and security policies for **SmartRent** on Supabase (PostgreSQL).

---

## 1. Multi-Tenancy Architecture

All operational data is tenant-isolated by `property_id` and property ownership:

- **Users (`auth.users`)**: Handled by Supabase Auth (GoTrue).
- **Properties (`properties`)**: Owned by a user (`owner_id = auth.uid()`).
- **Devices (`devices`)**: Associated with a property (`property_id REFERENCES properties(id)`).
- **Device Logs & Events (`device_logs`)**: Associated with devices and properties.

---

## 2. Row Level Security (RLS) Policy Standards

Every table **must** have RLS enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`).

### Policies Examples

#### Devices Table
```sql
-- View devices of owned properties
CREATE POLICY "Users can view own property devices"
ON devices FOR SELECT USING (
  property_id IN (
    SELECT id FROM properties WHERE owner_id = auth.uid()
  )
);

-- Update devices of owned properties
CREATE POLICY "Users can update own property devices"
ON devices FOR UPDATE USING (
  property_id IN (
    SELECT id FROM properties WHERE owner_id = auth.uid()
  )
);
```

#### Property Logs Table
```sql
CREATE POLICY "Users can view own property logs"
ON device_logs FOR SELECT USING (
  property_id IN (
    SELECT id FROM properties WHERE owner_id = auth.uid()
  )
);
```

---

## 3. Strict `service_role` Separation

> [!IMPORTANT]
> The backend API must execute user requests using the user's Supabase JWT token so that RLS is enforced at the database level.

- **User API Requests:** Pass `Authorization: Bearer <user_jwt>` to Supabase client.
- **Background Workers (MQTT Worker / Cron Tasks):** Allowed to use `service_role` key **only** for system telemetry ingestion, provisioning, and batch log writes.
- **Rule:** Never expose or use `service_role` in user-facing HTTP endpoints.

---

## 4. PIN Codes & Physical Access Security

1. PIN codes for smart locks (e.g. TTLock) are **encrypted at rest** and never stored in plain text.
2. PIN codes are **never logged** in application logs or standard telemetry logs.
3. Every PIN creation, modification, or deletion generates an entry in `audit_logs` (recording timestamp, user ID, lock ID, and action type).

---

## 5. Log Retention with `pg_cron`

Telemetry and device logs are retained for 90 days. A scheduled `pg_cron` job cleans up old logs:

```sql
SELECT cron.schedule(
  'cleanup-device-logs-90-days',
  '0 3 * * *', -- Everyday at 03:00 UTC
  $$DELETE FROM device_logs WHERE created_at < NOW() - INTERVAL '90 days'$$
);
```
