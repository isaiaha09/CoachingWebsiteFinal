self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('number44-cache').then(cache => {
      return cache.addAll([
        '/',
        '/static/bookings/site.webmanifest.json',
        '/static/bookings/images_and_videos/number44-192x192.png',
        '/static/bookings/images_and_videos/number44-512x512.png'
      ]);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});