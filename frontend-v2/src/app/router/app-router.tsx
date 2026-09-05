import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AuthLayout } from '@/app/layouts/auth-layout'
import { LauncherLayout } from '@/app/layouts/launcher-layout'
import { ModuleLayout } from '@/app/layouts/module-layout'
import { ModuleLauncherPage } from '@/app/pages/module-launcher-page'
import { ForgotPasswordPage } from '@/core/auth/pages/forgot-password-page'
import { LoginPage } from '@/core/auth/pages/login-page'
import { ResetPasswordPage } from '@/core/auth/pages/reset-password-page'
import { NotFoundPage } from '@/shared/ui/not-found-page'
import { RouteErrorPage } from '@/shared/ui/route-error-page'
import { appRoutes } from '@/shared/constants/app-routes'
import { customModuleRoutes, moduleRoutes } from './module-registry'
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
              { path: appRoutes.resetPassword, element: <ResetPasswordPage /> },
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
            path: appRoutes.procurement.surveyRequestPrint(':id'),
            lazy: async () => ({
              Component: (await import('@/modules/procurement/pages/survey-request-print-page'))
                .SurveyRequestPrintPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.procurement.surveyRequestPurchasingPrint(':id'),
            lazy: async () => ({
              Component: (
                await import('@/modules/procurement/pages/survey-request-purchasing-print-page')
              ).SurveyRequestPurchasingPrintPage,
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
            path: appRoutes.finance.paymentRequestPrint(':id'),
            lazy: async () => ({
              Component: (await import('@/modules/finance/pages/payment-request-print-page'))
                .PaymentRequestPrintPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.document.documentPrint(':id'),
            lazy: async () => ({
              Component: (await import('@/modules/document/pages/document-print-page'))
                .DocumentPrintPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          //  Phân hệ TỰ MANG KHUNG riêng (Diễn đàn) — đứng ngoài `ModuleLayout`
          //  như các trang in; `routes.tsx` của phân hệ tự lo layout + errorElement.
          ...customModuleRoutes,
          {
            element: <LauncherLayout />,
            children: [
              {
                errorElement: <RouteErrorPage />,
                children: [
                  { index: true, element: <ModuleLauncherPage /> },
                  // Trang cá nhân DÙNG CHUNG cho mọi phân hệ nên đặt ở khung
                  // launcher. Trang thông báo riêng đã bỏ (CR-215) — thông báo
                  // nay là một tab trong Trang cá nhân; giữ route cũ làm chuyển
                  // hướng cho link bookmark/đã gửi qua email.
                  {
                    path: appRoutes.notifications,
                    element: <Navigate to="/me?tab=notifications" replace />,
                  },
                  {
                    path: appRoutes.me,
                    lazy: async () => ({
                      Component: (await import('@/app/pages/profile-page')).ProfilePage,
                    }),
                  },
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
