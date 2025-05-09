import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './hive-mind/ui/src')
    }
  },
  server: {
    port: 3001,
    strictPort: false,
    host: true,
  },
  // Tauri expects a fixed port, fail if that port is not available
  clearScreen: false,
  // For Tauri support
  build: {
    target: ['es2021', 'chrome100', 'safari13'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  }
}); 