import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: './',   // Zorgt ervoor dat Vite de juiste root gebruikt
  build: {
    outDir: 'dist',  // Output map voor de build
  },
  server: {
    port: 5173,  // Poort waarop de frontend draait
    open: true,  // Opent de browser automatisch bij start
  }
});
