/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Device entity connected to a property in SmartRent.
 */
export interface DeviceSchema {
  id: string;
  property_id: string;
  device_type: "lock" | "relay" | "valve" | "climate" | "sensor";
  name: string;
  is_active: boolean;
  settings?: {
    [k: string]: unknown;
  };
  last_seen?: string | null;
  created_at: string;
  updated_at: string;
}
