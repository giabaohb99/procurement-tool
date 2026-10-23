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
import { guardedPrintLazy } from './print-route-guard'
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
        //  bao-CR-638: trang CÔNG KHAI hướng dẫn nối AI riêng — không cần đăng nhập, ngoài mọi khung, không bao giờ có khóa.
        path: appRoutes.connectAi,
        lazy: async () => ({
          Component: (await import('@/app/pages/connect-ai-page')).ConnectAiPage,
        }),
        errorElement: <RouteErrorPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            //  ai-CR-218: màn đồng ý OAuth của cổng MCP — cần đăng nhập nhưng đứng NGOÀI khung ứng dụng (như trang in).
            path: appRoutes.oauthConsent(':req'),
            lazy: async () => ({
              Component: (await import('@/app/pages/oauth-consent-page')).OAuthConsentPage,
            }),
            errorElement: <RouteErrorPage />,
          },
          //  NF-20: MỌI route in đi qua `guardedPrintLazy` — quyền khai ở `print-route-access.ts`.
          {
            path: appRoutes.procurement.purchaseRequestPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseRequestPrint(':id'), async () => {
              const { PurchaseRequestPrintPage } = await import('@/modules/procurement/pages/purchase-request-print-page')
              return PurchaseRequestPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  bao-CR-310 đợt 4 — bản in theo NCC của YCMH; trang còn tự gác thêm supplier:read (N-17).
            path: appRoutes.procurement.purchaseRequestSupplierPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseRequestSupplierPrint(':id'), async () => {
              const { PurchaseRequestSupplierPrintPage } = await import('@/modules/procurement/pages/purchase-request-supplier-print-page')
              return PurchaseRequestSupplierPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  bao-CR-314 — `:id` là id ĐƠN MUA HÀNG; cổng quyền là quyền in ĐƠN (purchase_order:print).
            path: appRoutes.procurement.purchaseRequestPrintFromPo(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseRequestPrintFromPo(':id'), async () => {
              const { PurchaseRequestPrintPage } = await import('@/modules/procurement/pages/purchase-request-print-page')
              return () => <PurchaseRequestPrintPage fromPo />
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.procurement.purchaseOrderPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseOrderPrint(':id'), async () => {
              const { PurchaseOrderPrintPage } = await import('@/modules/procurement/pages/purchase-order-print-page')
              return PurchaseOrderPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  bao-CR-322 — cùng trang in, mở sẵn mẫu Đơn mua hàng; giữ đường dẫn bản v1.
            path: appRoutes.procurement.purchaseOrderGoodsPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseOrderGoodsPrint(':id'), async () => {
              const { PurchaseOrderPrintPage } = await import('@/modules/procurement/pages/purchase-order-print-page')
              return () => <PurchaseOrderPrintPage defaultMode="goods" />
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.procurement.purchaseOrderImportPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.procurement.purchaseOrderImportPrint(':id'), async () => {
              const { PurchaseOrderImportPrintPage } = await import('@/modules/procurement/pages/purchase-order-import-print-page')
              return PurchaseOrderImportPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  bao-CR-357 — bản in báo cáo giá vốn: phạm vi đi bằng query string, không có `:id`.
            path: appRoutes.procurement.importLandedCostPrint,
            lazy: guardedPrintLazy(appRoutes.procurement.importLandedCostPrint, async () => {
              const { ImportLandedCostPrintPage } = await import('@/modules/procurement/pages/import-landed-cost-print-page')
              return ImportLandedCostPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.finance.paymentRequestPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.finance.paymentRequestPrint(':id'), async () => {
              const { PaymentRequestPrintPage } = await import('@/modules/finance/pages/payment-request-print-page')
              return PaymentRequestPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.document.documentPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.document.documentPrint(':id'), async () => {
              const { DocumentPrintPage } = await import('@/modules/document/pages/document-print-page')
              return DocumentPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.vehicleBooking.print(':id'),
            lazy: guardedPrintLazy(appRoutes.vehicleBooking.print(':id'), async () => {
              const { VehicleBookingPrintPage } = await import('@/modules/vehicle-booking/pages/vehicle-booking-print-page')
              return VehicleBookingPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.approvalSeal.print(':id'),
            lazy: guardedPrintLazy(appRoutes.approvalSeal.print(':id'), async () => {
              const { SealRequestPrintPage } = await import('@/modules/approval-seal/pages/seal-request-print-page')
              return SealRequestPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  duoc-CR-676 — Phiếu thông tin nhân viên BM00../QT01/NS (phòng Nhân sự in từ hồ sơ).
            path: appRoutes.hr.employeeInfoPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.hr.employeeInfoPrint(':id'), async () => {
              const { EmployeeInfoPrintPage } = await import('@/modules/hr/pages/employee-info-print-page')
              return EmployeeInfoPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            //  duoc-CR-676 — phiếu của chính mình, mở từ Trang cá nhân.
            path: appRoutes.hr.myEmployeeInfoPrint,
            lazy: guardedPrintLazy(appRoutes.hr.myEmployeeInfoPrint, async () => {
              const { MyEmployeeInfoPrintPage } = await import('@/modules/hr/pages/employee-info-print-page')
              return MyEmployeeInfoPrintPage
            }),
            errorElement: <RouteErrorPage />,
          },
          {
            path: appRoutes.hr.leaveRequestPrint(':id'),
            lazy: guardedPrintLazy(appRoutes.hr.leaveRequestPrint(':id'), async () => {
              const { LeaveRequestPrintPage } = await import('@/modules/hr/pages/leave-request-print-page')
              return LeaveRequestPrintPage
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
