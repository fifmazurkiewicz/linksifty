import { sentryVitePlugin } from "@sentry/vite-plugin";
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  build: { sourcemap: process.env.SENTRY_AUTH_TOKEN ? "hidden" : false },
  plugins: [react(), ...(process.env.SENTRY_AUTH_TOKEN ? [sentryVitePlugin({
      authToken: process.env.SENTRY_AUTH_TOKEN,
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      telemetry: false,
      sourcemaps: { filesToDeleteAfterUpload: ["./dist/**/*.map"] },
    })] : [])],
})
