import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 8200,
    open: true,
    proxy: {
      // Health check proxies to bypass CORS
      '/health/8100': { target: 'http://localhost:8100', changeOrigin: true, rewrite: (path) => '/' },
      '/health/8101': { target: 'http://localhost:8101', changeOrigin: true, rewrite: (path) => '/api/v3/health' },
      '/health/8102': { target: 'http://localhost:8102', changeOrigin: true, rewrite: (path) => '/api/health' },
      '/health/8091': { target: 'http://localhost:8091', changeOrigin: true, rewrite: (path) => '/' },
      '/health/8103': { target: 'http://localhost:8103', changeOrigin: true, rewrite: (path) => '/api/v1/health' },
      '/health/8108': { target: 'http://localhost:8108', changeOrigin: true, rewrite: (path) => '/api/v1/health' },
      '/health/8202': { target: 'http://localhost:8202', changeOrigin: true, rewrite: (path) => '/health' },
      '/health/8105': { target: 'http://localhost:8105', changeOrigin: true, rewrite: (path) => '/encoder/status' },
      '/health/3000': { target: 'http://localhost:3000', changeOrigin: true, rewrite: (path) => '/health' },
      '/health/5173': { target: 'http://localhost:5173', changeOrigin: true, rewrite: (path) => '/' },
    },
  },
  publicDir: 'public',
});
