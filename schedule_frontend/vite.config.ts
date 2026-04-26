import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { defineConfig } from 'vite'

const host = process.env.TAURI_DEV_HOST

export default defineConfig({
  base: './',
  plugins: [
    vue(),
    Components({
      dts: 'src/components.d.ts',
      resolvers: [
        ElementPlusResolver({
          importStyle: 'css',
          directives: true,
        }),
      ],
    }),
  ],
  clearScreen: false,
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: host || '127.0.0.1',
    port: 1420,
    strictPort: true,
    hmr: host
      ? {
          protocol: 'ws',
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
  },
  build: {
    target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
    minify: process.env.TAURI_ENV_DEBUG ? false : 'esbuild',
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('@element-plus/icons-vue')) {
            return 'element-plus-icons'
          }
          if (id.includes('node_modules/vue') || id.includes('node_modules/pinia') || id.includes('node_modules/vue-router')) {
            return 'vue-vendor'
          }
          return undefined
        },
      },
    },
    chunkSizeWarningLimit: 650,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.test.ts'],
    server: {
      deps: {
        inline: ['element-plus', '@element-plus/icons-vue'],
      },
    },
  },
})
