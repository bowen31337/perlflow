/**
 * Vitest setup file
 * Configures the test environment for React component testing
 */

import '@testing-library/react';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Clean up DOM after each test
afterEach(() => {
  cleanup();
});
