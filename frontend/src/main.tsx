import { ErrorBoundary } from "@sentry/react";
import { initMonitoring } from "./lib/monitoring";
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

initMonitoring();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary fallback={<p role="alert">Wystąpił błąd aplikacji. Odśwież stronę.</p>}><App /></ErrorBoundary>
  </StrictMode>,
)
