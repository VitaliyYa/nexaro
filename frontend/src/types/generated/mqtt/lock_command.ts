/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Command payload sent from Cloud to Edge to operate a smart lock.
 */
export interface LockCommandPayload {
  command: "LOCK" | "UNLOCK";
  /**
   * Optional auto-relock delay in seconds
   */
  duration_seconds?: number;
  /**
   * User ID or system process initiating the command
   */
  requested_by?: string;
  /**
   * Unique command idempotency tracking ID
   */
  request_id: string;
}
