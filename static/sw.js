/* HeatSafe PWA service worker — network-first so live data is never stale. */
const CACHE = "heatsafe-v1";
const PRECACHE = [
  "/",
  "/test",
  "/static/style.css",
  "/static/test.css",
  "/static/app.js",
  "/static/test.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Never cache live API/tool responses.
  if (url.pathname.startsWith("/tools/") || url.pathname.startsWith("/api/") ||
      url.pathname.startsWith("/analytics/") || url.pathname === "/health") return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() => caches.match(request).then((cached) =>
        // The HTML shell is a fallback for navigations only — serving it in
        // place of a script or stylesheet would "succeed" with wrong content.
        cached || (request.mode === "navigate" ? caches.match("/") : Response.error())
      ))
  );
});
