import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from '@/App'
import { AuthProvider } from '@/auth/auth-context'
import { ConfirmHost } from '@/components/confirm-dialog'
import { Toaster } from '@/components/ui/sonner'
import '@/index.css'
import '@/styles/article-content.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
        <Toaster position="top-right" richColors />
        <ConfirmHost />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
)
