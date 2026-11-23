/* Zaria Village: keeps the statement page available when the phone is offline.
   Only the statement page itself is handled; the locked reports are never cached here. */
const CACHE = 'zaria-statement-v8';
const SHELL = ['./', 'manifest.webmanifest', 'icon-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  const root = new URL('./', self.registration.scope).pathname;
  const isStatement = e.request.mode === 'navigate' && (u.pathname === root || u.pathname === root + 'index.html');
  if (e.request.method !== 'GET' || u.origin !== location.origin || !(isStatement || SHELL.some(p => u.pathname === root + p.replace('./', '')))) return;
  e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(isStatement ? './' : e.request, copy)); return r; })
    .catch(() => caches.match(isStatement ? './' : e.request)));
});
