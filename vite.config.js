import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],

  server: {
    port: 5173,
  },

  preview: {
    port: 4173,
  },

  build: {
    sourcemap: false,
    cssCodeSplit: true,
    chunkSizeWarningLimit: 500,

    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined;
          }

          // Charts must be checked before React because "recharts"
          // contains the word "react".
          if (
            id.includes('/recharts/') ||
            id.includes('\\recharts\\') ||
            id.includes('/chart.js/') ||
            id.includes('\\chart.js\\')
          ) {
            return 'vendor-charts';
          }

          if (
            id.includes('/@supabase/') ||
            id.includes('\\@supabase\\')
          ) {
            return 'vendor-supabase';
          }

          if (
            id.includes('/axios/') ||
            id.includes('\\axios\\') ||
            id.includes('/date-fns/') ||
            id.includes('\\date-fns\\') ||
            id.includes('/lucide-react/') ||
            id.includes('\\lucide-react\\')
          ) {
            return 'vendor-ui';
          }

          // Match the actual React packages rather than every package
          // whose name happens to contain "react".
          if (
            id.includes('/react/') ||
            id.includes('\\react\\') ||
            id.includes('/react-dom/') ||
            id.includes('\\react-dom\\') ||
            id.includes('/react-router/') ||
            id.includes('\\react-router\\') ||
            id.includes('/react-router-dom/') ||
            id.includes('\\react-router-dom\\') ||
            id.includes('/scheduler/') ||
            id.includes('\\scheduler\\')
          ) {
            return 'vendor-react';
          }

          return 'vendor-other';
        },
      },
    },
  },

  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    globals: true,
    exclude: [
      'e2e/**',
      'node_modules/**',
      'dist/**',
    ],
  },
});