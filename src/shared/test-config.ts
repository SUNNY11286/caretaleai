/**
 * Property-Based Testing Configuration
 * 
 * This module provides centralized configuration for property-based testing
 * using fast-check. All property tests should use these settings to ensure
 * consistency with the design requirements (minimum 100 iterations).
 */

import * as fc from 'fast-check';

/**
 * Standard configuration for property-based tests
 * - numRuns: Minimum 100 iterations as per design document
 * - timeout: 30 seconds for complex property tests
 * - verbose: Enable detailed output for debugging
 */
export const propertyTestConfig: fc.Parameters<unknown> = {
  numRuns: 100,
  verbose: fc.VerbosityLevel.Verbose,
  // Seed can be set for reproducible tests
  // seed: 42,
};

/**
 * Extended configuration for intensive property tests
 * Use this for tests that need more thorough coverage
 */
export const intensivePropertyTestConfig: fc.Parameters<unknown> = {
  numRuns: 500,
  verbose: fc.VerbosityLevel.Verbose,
};

/**
 * Quick configuration for smoke tests during development
 * Not recommended for CI/CD pipelines
 */
export const quickPropertyTestConfig: fc.Parameters<unknown> = {
  numRuns: 20,
  verbose: fc.VerbosityLevel.None,
};

/**
 * Helper function to run property tests with standard configuration
 * 
 * @example
 * ```typescript
 * runPropertyTest('Property 1: Multimodal Input Processing', 
 *   fc.property(fc.string(), (input) => {
 *     // Test implementation
 *   })
 * );
 * ```
 */
export function runPropertyTest(
  testName: string,
  property: fc.IProperty<unknown>,
  config: fc.Parameters<unknown> = propertyTestConfig
): void {
  test(testName, () => {
    fc.assert(property, config);
  });
}
