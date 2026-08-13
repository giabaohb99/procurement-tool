import { createBrowserRouter } from 'react-router-dom'

import { AuthLayout } from '@/app/layouts/auth-layout'
import { LauncherLayout } from '@/app/layouts/launcher-layout'
import { ModuleLayout } from '@/app/layouts/module-layout'
import { ModuleLauncherPage } from '@/app/pages/module-launcher-page'
import { ForgotPasswordPage } from '@/core/auth/pages/forgot-password-page'
import { LoginPage } from '@/core/auth/pages/login-page'
import { NotFoundPage } from '@/shared/ui/not-found-page'
import { RouteErrorPage } from '@/shared/ui/route-error-page'
import { appRoutes } from '@/shared/constants/app-routes'
import { moduleRoutes } from './module-registry'
import { ProtectedRoute } from './protected-route'

/**
 * Cây route ba khung:
 *  - `AuthLayout`     — màn công khai (đăng nhập, quên mật khẩu)
 *  - `LauncherLayout` — màn chọn phân hệ, không menu trái
 *  - `ModuleLayout`   — bên trong một phân hệ, có menu trái của phân hệ đó
 *
 * Route nghiệp vụ KHÔNG khai báo ở đây mà đến từ `module-registry`.
 *
 * BẮT LỖI — hai tầng, cố ý:
 *  1. Route gốc không path ôm cả cây: lỗi ở chính layout (hoặc ở nhánh chưa có
 *     boundary riêng) dội lên đây, thay toàn màn hình. Không có tầng này thì
 *     react-router hiện màn lỗi mặc định trần trụi của nó.
 *  2. Mỗi layout có thêm một route con KHÔNG path chỉ để giữ `errorElement`.
 *     Nhờ vậy lỗi của trang con chỉ thay phần `Outlet` — người dùng vẫn còn
 *     header/menu để đi tiếp thay vì mất trắng khung app.
 *
 * Lỗi NGOÀI router (provider, RouterProvider) do `ErrorBoundary` ở `app.tsx` lo.
 */
export const router = createBrowserRouter([
  {
    errorElement: <RouteErrorPage />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          {
            errorElement: <RouteErrorPage />,
            children: [
              { path: appRoutes.login, element: <LoginPage /> },
              { path: appRoutes.forgotPassword, element: <ForgotPasswordPage /> },
            ],
          },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: appRoutes.procurement.purchaseRequestPrint(':id'),
            lazy: async () => ({
              Component: (await import('@/modules/procurement/pages/purchase-request-print-page'))
                .PurchaseRequestPrintPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.procurement.purchaseOrderPrint(':id'),
            lazy: async () => ({
              Component: (await import('@/modules/procurement/pages/purchase-order-print-page'))
                .PurchaseOrderPrintPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            element: <LauncherLayout />,
            children: [
              {
                errorElement: <RouteErrorPage />,
                children: [
                  { index: true, element: <ModuleLauncherPage /> },
                  // Bắt mọi URL không khớp phân hệ nào — kể cả phân hệ đang tắt.
                  { path: '*', element: <NotFoundPage /> },
                ],
              },
            ],
          },
          {
            element: <ModuleLayout />,
            children: [
              {
                // Trang phân hệ nạp bằng `lazy`: chunk hụt (thường do vừa deploy
                // bản mới) sẽ ném lỗi ở đây thay vì trắng màn hình.
                errorElement: <RouteErrorPage />,
                children: moduleRoutes,
              },
            ],
          },
        ],
      },
    ],
  },
])
