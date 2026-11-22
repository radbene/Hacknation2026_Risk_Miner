import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// public demo through an ngrok tunnel
const allowedHosts = ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app', '.ngrok.dev']
const proxy = { '/api': { target: process.env.API_URL ?? 'http://localhost:8040', changeOrigin: true } }

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: { port: 5180, allowedHosts, proxy },
  // production build for the public demo: `npm run build && npx vite preview` (port 5190) + `ngrok http 5190`
  preview: { port: 5190, strictPort: true, allowedHosts, proxy },
})
