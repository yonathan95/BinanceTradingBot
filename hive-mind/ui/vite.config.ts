import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            console.log('Proxy error:', err);
            res.writeHead(500, {
              'Content-Type': 'text/plain',
            });
            res.end('Backend API server is not running. Using mock data instead.');
          });
        }
      },
      '/mock-api': {
        target: 'http://localhost:3000',
        rewrite: (path) => path.replace(/^\/mock-api/, '/public/mock-api'),
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
  },
}); 