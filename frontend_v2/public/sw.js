/**
 * Service Worker for Analize.online Push Notifications
 *
 * This service worker handles:
 * 1. Receiving push notifications from the server
 * 2. Displaying notifications with proper formatting
 * 3. Handling notification clicks to open the app
 */

// Service worker version for cache busting
const SW_VERSION = '1.0.0';

// Cache names
const CACHE_NAME = 'analize-v1';
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/healthy.svg',
  '/icons/icon-192.svg',
  '/icons/icon-512.svg',
];

// Install event - pre-cache static assets

// Handle push notification events
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    console.error('[SW] Failed to parse push data:', e);
    data = {
      title: 'Analize.online',
      body: event.data ? event.data.text() : 'Ai o notificare noua'
    };
  }

  const title = data.title || 'Analize.online';
  const options = {
    body: data.body || '',
    icon: data.icon || '/favicon.svg',
    badge: data.badge || '/favicon.svg',
    tag: data.tag || 'default',
    data: data.data || {},
    // Vibration pattern: vibrate 200ms, pause 100ms, vibrate 200ms
    vibrate: [200, 100, 200],
    // Keep notification visible until user interacts
    requireInteraction: true,
    // Action buttons
    actions: getActionsForType(data.data?.type)
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Get action buttons based on notification type
function getActionsForType(type) {
  switch (type) {
    case 'new_documents':
      return [
        { action: 'view', title: 'Vezi Documentele' },
        { action: 'dismiss', title: 'Inchide' }
      ];
    case 'abnormal_biomarker':
      return [
        { action: 'view', title: 'Vezi Detalii' },
        { action: 'dismiss', title: 'Inchide' }
      ];
    case 'analysis_complete':
      return [
        { action: 'view', title: 'Vezi Raportul' },
        { action: 'dismiss', title: 'Inchide' }
      ];
    case 'sync_failed':
      return [
        { action: 'view', title: 'Verifica' },
        { action: 'dismiss', title: 'Inchide' }
      ];
    default:
      return [
        { action: 'view', title: 'Deschide' },
        { action: 'dismiss', title: 'Inchide' }
      ];
  }
}

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  // Get URL to open from notification data
  const urlToOpen = event.notification.data?.url || '/dashboard';
  const fullUrl = new URL(urlToOpen, self.location.origin).href;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.startsWith(self.location.origin) && 'focus' in client) {
            // App is open, navigate and focus
            client.navigate(fullUrl);
            return client.focus();
          }
        }
        // App is not open, open new window
        if (clients.openWindow) {
          return clients.openWindow(fullUrl);
        }
      })
  );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed');
});

// Service worker installation
self.addEventListener('install', (event) => {
  console.log('[SW] Service Worker installed, version:', SW_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Service worker activation
self.addEventListener('activate', (event) => {
  console.log('[SW] Service Worker activated, version:', SW_VERSION);
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => clients.claim())
  );
});

// Fetch event - network first with cache fallback for navigation, cache first for static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip API calls and external resources
  if (url.pathname.startsWith('/api/') || url.origin !== self.location.origin) return;

  // For navigation requests (HTML pages), use network-first
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match('/')))
    );
    return;
  }

  // For static assets, use cache-first
  if (url.pathname.match(/\.(js|css|svg|png|jpg|jpeg|gif|woff2?|ttf|eot)$/)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        });
      })
    );
    return;
  }
});

// Log any errors
self.addEventListener('error', (event) => {
  console.error('[SW] Service Worker error:', event.error);
});
