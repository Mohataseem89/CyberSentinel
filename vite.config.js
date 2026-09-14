import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),
        tailwindcss(),

  ],
  server: {
    port: 5173,
    historyApiFallback: true
  },
  preview: {
    port: 5173
  },
  build: {
    sourcemap: false,
    cssCodeSplit: true,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('react') || id.includes('scheduler')) return 'vendor-react';
          if (id.includes('chart.js') || id.includes('recharts')) return 'vendor-charts';
          if (id.includes('@supabase')) return 'vendor-supabase';
          if (id.includes('axios') || id.includes('date-fns') || id.includes('lucide-react')) return 'vendor-ui';
          return 'vendor-other';
        },
      },
    },
  },
  test: { environment: 'jsdom', setupFiles: './src/test/setup.js', globals: true, exclude: ['e2e/**', 'node_modules/**', 'dist/**'] }
})
