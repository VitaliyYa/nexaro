/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Command payload sent to control climate / AC setpoints and modes.
 */
export interface ClimateCommandPayload {
  /**
   * Target setpoint temperature in Celsius
   */
  target_temperature?: number;
  /**
   * Desired operational mode
   */
  hvac_mode?: "off" | "cool" | "heat" | "fan_only" | "auto" | "dry";
  /**
   * Desired fan speed
   */
  fan_mode?: "auto" | "low" | "medium" | "high";
  /**
   * Unique command idempotency tracking ID
   */
  request_id: string;
}
