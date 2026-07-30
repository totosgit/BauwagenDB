import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Blauwagen Verwaltung',
        short_name: 'Blauwagen',
        description: 'Lagerverwaltung für den Bauwagen',
        // Holzfarben passend zur App, vorher stand hier noch das alte Grün
        theme_color: '#c19c6d',
        background_color: '#cba97c',
        display: 'standalone',
        orientation: 'any',
        // ?v= mit index.html gleich halten und bei Icon-Änderungen hochzählen
        icons: [
          { src: '/icon-192.png?v=2', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png?v=2', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512.png?v=2', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Die Regeln pruefen den Pfad ueber ein URL-Objekt. Vorher standen
        // hier Ausdruecke wie /^\/api\//, die nie zutrafen: Workbox vergleicht
        // gegen die vollstaendige Adresse (https://.../api/...), nicht gegen
        // den Pfad. Dadurch wurde bis jetzt gar nichts zwischengespeichert
        // und die App zeigte ohne Netz ein leeres Geruest.
        runtimeCaching: [
          {
            // Daten: erst das Netz, nach 4 s der letzte bekannte Stand.
            // Ohne /api/auth/ -- eine gecachte Anmeldeantwort waere Unsinn.
            urlPattern: ({ url, sameOrigin }) =>
              sameOrigin
              && url.pathname.startsWith('/api/')
              && !url.pathname.startsWith('/api/auth/'),
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'blauwagen-daten',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 80, maxAgeSeconds: 60 * 60 * 24 * 7 },
              // Fehlerantworten (401, 500) nie ablegen
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            // Fotos aendern sich nie -- der Dateiname ist eine UUID.
            urlPattern: ({ url, sameOrigin }) =>
              sameOrigin && url.pathname.startsWith('/images/'),
            handler: 'CacheFirst',
            method: 'GET',
            options: {
              cacheName: 'blauwagen-bilder',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 60 },
              cacheableResponse: { statuses: [200] },
            },
          },
        ],
      }
    })
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/images': 'http://localhost:8000'
    }
  }
})
