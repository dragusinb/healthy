/**
 * Push Notification Service for Analize.online
 *
 * This service handles:
 * 1. Checking browser support for push notifications
 * 2. Requesting notification permission
 * 3. Registering the service worker
 * 4. Subscribing to push notifications
 * 5. Sending subscription to backend
 */

import api from '../api/client';

// Check if push notifications are supported
export function isPushSupported() {
  return 'serviceWorker' in navigator &&
         'PushManager' in window &&
         'Notification' in window;
}

// Get current notification permission status
export function getPermissionStatus() {
  if (!isPushSupported()) {
    return 'unsupported';
  }
  return Notification.permission; // 'default', 'granted', 'denied'
}

// Request notification permission
export async function requestPermission() {
  if (!isPushSupported()) {
    throw new Error('Push notifications are not supported in this browser');
  }

  const permission = await Notification.requestPermission();
  return permission; // 'granted', 'denied', or 'default'
}

// Register service worker
export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    throw new Error('Service Workers are not supported');
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    });

    console.log('Service Worker registered:', registration);

    // Wait for the service worker to be ready
    await navigator.serviceWorker.ready;

    return registration;
  } catch (error) {
    console.error('Service Worker registration failed:', error);
    throw error;
  }
}

// Convert URL-safe base64 to Uint8Array (for VAPID key)
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Get VAPID public key from server
export async function getVapidPublicKey() {
  try {
    const response = await api.get('/notifications/push/vapid-key');
    return response.data.vapid_public_key;
  } catch (error) {
    console.error('Failed to get VAPID public key:', error);
    throw new Error('Push notifications not configured on server');
  }
}

// Subscribe to push notifications
export async function subscribeToPush() {
  if (!isPushSupported()) {
    throw new Error('Push notifications are not supported');
  }

  // Check permission
  const permission = await requestPermission();
  if (permission !== 'granted') {
    throw new Error('Notification permission denied');
  }

  // Register service worker
  const registration = await registerServiceWorker();

  // Get VAPID public key from server
  const vapidPublicKey = await getVapidPublicKey();

  // Subscribe to push
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
  });

  console.log('Push subscription:', subscription);

  // Send subscription to backend
  const subscriptionData = subscription.toJSON();
  await api.post('/notifications/push/subscribe', {
    endpoint: subscriptionData.endpoint,
    keys: subscriptionData.keys
  });

  return subscription;
}

// Unsubscribe from push notifications
export async function unsubscribeFromPush() {
  if (!isPushSupported()) {
    return;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      // Unsubscribe from browser
      await subscription.unsubscribe();

      // Notify backend
      const subscriptionData = subscription.toJSON();
      await api.post('/notifications/push/unsubscribe', {
        endpoint: subscriptionData.endpoint,
        keys: subscriptionData.keys || {}
      });
    }
  } catch (error) {
    console.error('Failed to unsubscribe:', error);
    throw error;
  }
}

// Check if currently subscribed
export async function isSubscribed() {
  if (!isPushSupported()) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return !!subscription;
  } catch (error) {
    console.error('Error checking subscription:', error);
    return false;
  }
}

// Get current subscription
export async function getSubscription() {
  if (!isPushSupported()) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    return await registration.pushManager.getSubscription();
  } catch (error) {
    console.error('Error getting subscription:', error);
    return null;
  }
}

// Get list of user's subscribed devices from backend
export async function getSubscribedDevices() {
  try {
    const response = await api.get('/notifications/push/subscriptions');
    return response.data;
  } catch (error) {
    console.error('Failed to get subscribed devices:', error);
    return [];
  }
}

// Delete a specific device subscription
export async function deleteDeviceSubscription(subscriptionId) {
  await api.delete(`/notifications/push/subscriptions/${subscriptionId}`);
}

// Send a test notification
export async function sendTestNotification() {
  await api.post('/notifications/push/test');
}

// Initialize push notifications (call on app load)
export async function initializePushNotifications() {
  if (!isPushSupported()) {
    console.log('Push notifications not supported');
    return { supported: false };
  }

  try {
    // Register service worker
    await registerServiceWorker();

    // Check current subscription status
    const subscribed = await isSubscribed();
    const permission = getPermissionStatus();

    return {
      supported: true,
      subscribed,
      permission
    };
  } catch (error) {
    console.error('Error initializing push notifications:', error);
    return {
      supported: true,
      subscribed: false,
      permission: getPermissionStatus(),
      error: error.message
    };
  }
}
