import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ThemeProvider } from 'next-themes'
import type { ReactNode } from 'react'

import { queryClient } from '@/core/api'
import { env } from '@/core/config/env'
import { Toaster } from '@/shared/ui/sonner'

/**
 * Gom mọi provider toàn cục về một chỗ, thứ tự từ ngoài vào trong:
 * theme -> react-query -> nội dung. Không cần AuthProvider vì auth nằm ở
 * zustand store (dùng được cả ngoài React).
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="top-right" richColors closeButton />
        {env.isDev && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ThemeProvider>
  )
}
