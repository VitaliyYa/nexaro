/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Event and state payload for water leak sensors and motorized water valves.
 */
export interface ValveEventPayload {
  /**
   * True if water leak sensor is currently triggered
   */
  leak_detected: boolean;
  /**
   * Current mechanical state of the motorized water shutoff valve
   */
  valve_state: "OPEN" | "CLOSED" | "CLOSING" | "OPENING" | "UNKNOWN";
  /**
   * Identifier of the specific leak sensor that triggered the event
   */
  sensor_id?: string | null;
  /**
   * True if valve was closed autonomously by local HAOS automation
   */
  auto_closed?: boolean;
  /**
   * ISO 8601 UTC timestamp of the event
   */
  timestamp: string;
}
