const withPWA = require("next-pwa")({
    dest: "public",
    disable: process.env.NODE_ENV === "development",
    register: true,
    skipWaiting: true,
    runtimeCaching: [
        {
            urlPattern: /^https:\/\/fonts\.(?:gstatic)\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
                cacheName: 'google-fonts-webfonts',
                expiration: {
                    maxEntries: 4,
                    maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
                },
            },
        },
        {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
                cacheName: 'google-fonts-stylesheets',
                expiration: {
                    maxEntries: 4,
                    maxAgeSeconds: 7 * 24 * 60 * 60, // 1 week
                },
            },
        },
        {
            urlPattern: /^https?:\/\/localhost:8000\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
                cacheName: 'autointern-api',
                expiration: {
                    maxEntries: 32,
                    maxAgeSeconds: 5 * 60, // 5 minutes
                },
                networkTimeoutSeconds: 5,
            },
        },
        {
            urlPattern: /.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
                cacheName: 'http-cache',
                expiration: {
                    maxEntries: 32,
                    maxAgeSeconds: 24 * 60 * 60, // 24 hours
                },
            },
        },
    ],
});

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
            },
            {
                source: '/health',
                destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`,
            },
        ];
    },
};

module.exports = withPWA(nextConfig);

