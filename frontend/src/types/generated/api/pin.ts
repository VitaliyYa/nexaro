/* eslint-disable */
/**
 * This file was automatically generated from JSON Schema.
 * Do not modify it manually.
 */

/**
 * Smart lock access PIN representation (plain-text pin is only present upon creation/transit, encrypted at rest).
 */
export interface PropertyPinSchema {
  id: string;
  property_id: string;
  device_id: string;
  /**
   * Guest or maintenance staff label
   */
  name: string;
  valid_from: string;
  valid_to: string;
  is_active: boolean;
  created_at: string;
}
