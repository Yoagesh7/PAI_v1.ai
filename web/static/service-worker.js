const CACHE_NAME = 'partnerai-v1';
const PRECACHE_URLS = [
  '/',
  '/static/css/design-system.css',
  '/static/js/focus_mode_v5.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Network-first for API calls, cache-first for navigation/static
  const req = event.request;
  if (req.method !== 'GET') return;

  if (req.mode === 'navigate' || req.destination === 'document') {
    event.respondWith(
      fetch(req).catch(() => caches.match('/'))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(resp => {
      return caches.open(CACHE_NAME).then(cache => {
        try { cache.put(req, resp.clone()); } catch(e) { }
        return resp;
      });
    })).catch(() => cached || Promise.reject('no-match'))
  );
});
