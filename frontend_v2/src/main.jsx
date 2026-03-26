import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import LogRocket from 'logrocket'
import './index.css'
import './i18n' // Initialize i18n before App
import App from './App.jsx'

// Initialize LogRocket session replay
const logrocketAppId = import.meta.env.VITE_LOGROCKET_APP_ID;
if (logrocketAppId) {
  LogRocket.init(logrocketAppId, {
    network: {
      // Don't capture request/response bodies (medical data privacy)
      requestSanitizer: (request) => {
        // Redact auth headers
        if (request.headers?.Authorization) {
          request.headers.Authorization = '[REDACTED]';
        }
        // Don't log request bodies (may contain medical data)
        request.body = undefined;
        return request;
      },
      responseSanitizer: (response) => {
        // Don't log response bodies (may contain medical data)
        response.body = undefined;
        return response;
      },
    },
    dom: {
      // Mask inputs that may contain sensitive data
      inputSanitizer: true,
    },
  });
}

// Initialize Sentry error tracking (only if DSN is configured)
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.5,
    environment: import.meta.env.MODE,
  });
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
