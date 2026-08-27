import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ThemeProvider } from 'next-themes'
import type { ReactNode } from 'react'

import { queryClient } from '@/core/api'
import { env } from '@/core/config/env'
import { ThemeSync } from '@/shared/theme/theme-sync'
import { Toaster } from '@/shared/ui/sonner'

/**
 * Gom mọi provider toàn cục về một chỗ, thứ tự từ ngoài vào trong:
 * theme -> react-query -> nội dung. Không cần AuthProvider vì auth nằm ở
 * zustand store (dùng được cả ngoài React).
 */
export function AppProviders({ children }: { children: ReactNode }) {
  //  `defaultTheme="system"` + `enableSystem`: chọn được cả ba (Theo hệ thống /
  //  Sáng / Tối) ở popover ảnh đại diện. `disableTransitionOnChange` để mọi
  //  `transition-colors` không chạy đua với hiệu ứng loang của View Transitions
  //  — hai thứ cùng đổi màu một lúc thì nhìn nhòe.
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        {/* Bảng màu đi theo TÀI KHOẢN (máy chủ), khác `ThemeProvider` ở trên chỉ
            lo chế độ nền Sáng/Tối và nhớ trong máy. Hai thứ vuông góc nhau. */}
        <ThemeSync />
        {children}
        <Toaster position="top-center" richColors closeButton />
        {/* Nút devtools để góc TRÁI-dưới: góc phải-dưới đã dành cho bong bóng Trợ lý AI. */}
        {env.isDev && (
          <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
        )}
      </QueryClientProvider>
    </ThemeProvider>
  )
}
