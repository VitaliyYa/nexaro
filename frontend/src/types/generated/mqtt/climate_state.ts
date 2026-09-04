/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Reported physical state of climate control (HVAC / AC / Thermostat).
 */
export interface ClimateStatePayload {
  /**
   * Current ambient temperature in Celsius
   */
  current_temperature: number;
  /**
   * Target setpoint temperature in Celsius
   */
  target_temperature: number;
  /**
   * Current operational mode
   */
  hvac_mode: "off" | "cool" | "heat" | "fan_only" | "auto" | "dry";
  /**
   * Fan speed setting
   */
  fan_mode?: "auto" | "low" | "medium" | "high" | null;
  /**
   * Power state of the climate unit
   */
  is_powered: boolean;
  /**
   * ISO 8601 UTC timestamp of status update
   */
  timestamp: string;
}
