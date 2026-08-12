import { RouterProvider } from 'react-router-dom'

import { AppProviders } from '@/app/providers/app-providers'
import { router } from '@/app/router/app-router'
import { ErrorBoundary } from '@/shared/ui/error-boundary'

/**
 * Gốc ứng dụng: boundary ngoài cùng, rồi provider, rồi router.
 *
 * Boundary đặt NGOÀI `AppProviders` để bắt được cả lỗi của chính provider. Đổi
 * lại nó không dùng được toast/theme — nên màn lỗi ở đó chỉ là HTML thuần + CSS.
 */
export function App() {
  return (
    <ErrorBoundary fullScreen>
      <AppProviders>
        <RouterProvider router={router} />
      </AppProviders>
    </ErrorBoundary>
  )
}
