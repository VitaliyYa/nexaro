/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Reported physical state of a smart lock (e.g. TTLock).
 */
export interface LockStatePayload {
  /**
   * Current lock mechanical state
   */
  state: "locked" | "unlocked" | "jammed" | "unknown";
  /**
   * Battery level percentage
   */
  battery: number;
  /**
   * Source or method of the last lock/unlock action
   */
  last_trigger?: "manual" | "passcode" | "card" | "fingerprint" | "app" | "auto_lock" | "unknown";
  /**
   * Diagnostic error message or null if normal
   */
  error?: string | null;
  /**
   * ISO 8601 UTC timestamp of status update
   */
  timestamp: string;
}
