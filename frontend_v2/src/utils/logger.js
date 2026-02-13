/**
 * Simple logger utility for consistent logging behavior.
 * In production (NODE_ENV === 'production'), only errors are logged.
 * In development, all log levels are enabled.
 */

const isDev = import.meta.env.DEV;

const logger = {
  /**
   * Log debug messages (development only)
   */
  debug: (...args) => {
    if (isDev) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Log informational messages (development only)
   */
  info: (...args) => {
    if (isDev) {
      console.log('[INFO]', ...args);
    }
  },

  /**
   * Log warning messages (development only)
   */
  warn: (...args) => {
    if (isDev) {
      console.warn('[WARN]', ...args);
    }
  },

  /**
   * Log error messages (always, needed for debugging production issues)
   * Note: In production, consider sending errors to a monitoring service
   */
  error: (...args) => {
    console.error('[ERROR]', ...args);
  },
};

export default logger;
