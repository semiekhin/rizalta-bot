// Service worker для PWA установки
const CACHE_NAME = 'rizalta-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Network-first strategy — всегда свежие данные
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
