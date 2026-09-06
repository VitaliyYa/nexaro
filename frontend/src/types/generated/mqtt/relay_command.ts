/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Command payload sent to toggle or switch relay power.
 */
export interface RelayCommandPayload {
  command: "ON" | "OFF" | "TOGGLE";
  /**
   * Unique command idempotency tracking ID
   */
  request_id: string;
}
