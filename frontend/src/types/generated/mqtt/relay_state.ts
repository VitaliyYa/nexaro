/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Reported physical state of a relay, switch, or power socket.
 */
export interface RelayStatePayload {
  state: "ON" | "OFF";
  /**
   * Current power consumption in Watts
   */
  power_w?: number | null;
  /**
   * Line voltage in Volts
   */
  voltage_v?: number | null;
  /**
   * ISO 8601 UTC timestamp of status update
   */
  timestamp: string;
}
