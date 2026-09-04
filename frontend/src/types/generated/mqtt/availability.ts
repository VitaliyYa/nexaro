/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Availability heartbeat and Last Will and Testament (LWT) status for Edge nodes.
 */
export interface NodeAvailabilityPayload {
  status: "online" | "offline";
  /**
   * Identifier of the Edge node gateway
   */
  node_id: string;
  /**
   * Software or firmware version of the edge node
   */
  version?: string;
  /**
   * ISO 8601 UTC timestamp of the status change
   */
  timestamp: string;
}
