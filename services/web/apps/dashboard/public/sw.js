/// <reference lib="webworker" />

declare const self: ServiceWorkerGlobalScope;

const CACHE_NAME = 'autointern-v1';
const OFFLINE_URL = '/offline';

// Files to cache immediately on install
const precacheAssets = [
    '/',
    '/offline',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png',
];

self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching assets');
            return cache.addAll(precacheAssets).catch((err) => {
                console.warn('[Service Worker] Cache addAll error:', err);
            });
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const { method, destination, url } = request;

    // Skip non-GET requests
    if (method !== 'GET') {
        return;
    }

    // Skip extensions and data: URIs
    if (url.startsWith('chrome-extension://') || url.startsWith('data:')) {
        return;
    }

    // Network-first strategy for API calls
    if (url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Clone and cache the response
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseToCache);
                    });
                    return response;
                })
                .catch(() => {
                    // Fall back to cache
                    return caches.match(request).then((cached) => {
                        if (cached) {
                            return cached;
                        }
                        // If not in cache, show offline page
                        return caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });
                    });
                })
        );
        return;
    }

    // Cache-first strategy for static assets
    if (destination === 'image' || destination === 'style' || destination === 'script' || destination === 'font') {
        event.respondWith(
            caches.match(request).then((cached) => {
                if (cached) {
                    return cached;
                }

                return fetch(request)
                    .then((response) => {
                        if (!response || response.status !== 200 || response.type === 'error') {
                            return response;
                        }

                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });

                        return response;
                    })
                    .catch(() => {
                        // Return offline page as fallback
                        return caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });
                    });
            })
        );
        return;
    }

    // Stale-while-revalidate for documents
    event.respondWith(
        caches.match(request).then((cached) => {
            const fetchPromise = fetch(request).then((response) => {
                if (!response || response.status !== 200 || response.type === 'error') {
                    return response;
                }

                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, responseToCache);
                });

                return response;
            });

            return cached || fetchPromise.catch(() => {
                return caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });
            });
        })
    );
});

export {};
