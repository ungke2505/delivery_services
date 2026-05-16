// Service Worker - Delivery Services PWA
const CACHE_NAME = 'ds-pwa-v1';
const STATIC_ASSETS = [
  '/delivery',
  '/delivery/driver',
  '/delivery/manifest.json',
  '/delivery/manifest-driver.json',
];

// Install: cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('SW: some assets failed to cache', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: clear old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Jangan intercept API calls & uploads
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/files/') ||
    event.request.method !== 'GET'
  ) {
    return;
  }

  // Network-first untuk halaman navigasi
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Cache-first untuk aset statis
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});

// Background sync (opsional, untuk retry upload saat offline)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-orders') {
    console.log('SW: Background sync triggered');
  }
});
