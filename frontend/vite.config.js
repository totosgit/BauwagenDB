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
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache', networkTimeoutSeconds: 5 }
          },
          {
            urlPattern: /^\/images\//,
            handler: 'CacheFirst',
            options: { cacheName: 'image-cache' }
          }
        ]
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
