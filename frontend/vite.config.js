import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// docs/contract/ lives above the Vite root. We alias into it rather than copy
// case_detail.json in, because CLAUDE.md invariant 8 says the contract and the
// code that reads it move together — a copy inside src/ would drift silently.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@contract': fileURLToPath(new URL('../docs/contract', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    fs: {
      allow: ['..'],
    },
  },
})
