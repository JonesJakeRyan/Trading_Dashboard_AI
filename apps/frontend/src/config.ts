/**
 * Frontend configuration
 * Uses environment variables set at build time
 */

export const config = {
  // API base URL - defaults to empty string for same-origin requests
  // In production, this should point to your backend Railway service
  apiUrl: import.meta.env.VITE_API_URL || '',
  
  // Environment
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

export default config;
