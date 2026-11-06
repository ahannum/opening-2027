// Keeps the player available offline: its own files, stories.js and every frame image it has fetched
// (the page fetches them all once in the background). Network first, so updates show up as soon as
// the phone is online; the saved copy is the fallback. Frames the page draws itself live in IndexedDB.
const CACHE = "opening-2027-player-v2";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // Only the player's own files; the planner it loads to draw frames always comes from the network.
  if (event.request.method !== "GET" || url.origin !== location.origin || !url.pathname.startsWith(new URL("./", location).pathname)) return;
  event.respondWith(fetch(event.request)
    .then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put(event.request, copy));
      }
      return response;
    })
    .catch(() => caches.match(event.request, { ignoreSearch: true })
      .then((hit) => hit || (event.request.mode === "navigate" ? caches.match("index.html") : Response.error()))));
});
