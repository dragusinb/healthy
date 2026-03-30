import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../api/client';

// Generate or retrieve persistent anonymous visitor ID.
// Uses localStorage so the same browser always maps to one visitor,
// even across tabs and browser restarts.
function getSessionId() {
  let vid = localStorage.getItem('_anl_vid');
  if (!vid) {
    // Migrate from old sessionStorage key if present
    vid = sessionStorage.getItem('_anl_sid');
    if (!vid) {
      vid = Math.random().toString(36).slice(2) + Date.now().toString(36);
    }
    localStorage.setItem('_anl_vid', vid);
  }
  return vid;
}

// Parse UTM params from URL
function getUtmParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    utm_source: params.get('utm_source') || undefined,
    utm_medium: params.get('utm_medium') || undefined,
    utm_campaign: params.get('utm_campaign') || undefined,
  };
}

// Get referrer domain
function getReferrer() {
  const ref = document.referrer;
  if (!ref) return undefined;
  try {
    const url = new URL(ref);
    // Don't track self-referrals
    if (url.hostname === 'analize.online') return undefined;
    return ref;
  } catch {
    return ref;
  }
}

/**
 * Tracks page views on every route change.
 * Sends anonymous data to /analytics/pageview.
 * No cookies, no PII, GDPR-friendly.
 */
export default function useAnalytics() {
  const location = useLocation();
  const lastPage = useRef(null);

  useEffect(() => {
    const page = location.pathname;

    // Don't double-track same page
    if (page === lastPage.current) return;
    lastPage.current = page;

    // Don't track admin pages
    if (page.startsWith('/admin')) return;

    // Detect logged-in user for visitor type analytics
    // Token is a JWT in sessionStorage — decode the payload to get user_id
    let userId = undefined;
    try {
      const token = sessionStorage.getItem('token');
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.sub) userId = parseInt(payload.sub, 10) || undefined;
      }
    } catch {}

    // Fire and forget — don't await, don't handle errors
    const data = {
      page,
      session_id: getSessionId(),
      referrer: getReferrer(),
      screen_width: window.innerWidth,
      user_id: userId,
      ...getUtmParams(),
    };

    // Use navigator.sendBeacon for reliability (survives page unload)
    // Fallback to fetch for browsers that don't support it with JSON
    try {
      const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
      const sent = navigator.sendBeacon?.('/analytics/pageview', blob);
      if (!sent) {
        // Fallback
        fetch('/analytics/pageview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
          keepalive: true,
        }).catch(() => {});
      }
    } catch {
      // Silently fail — analytics should never break the app
    }
  }, [location.pathname]);
}
