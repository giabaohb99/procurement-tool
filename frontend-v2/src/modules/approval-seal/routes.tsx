import { ClipboardList, LayoutDashboard, Stamp, UserCog } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ DUYỆT DẤU — trình ký, duyệt và đóng dấu chứng từ.
 *
 * Nghiệp vụ: tạo & theo dõi yêu cầu đóng dấu (luồng người tạo → TBP duyệt → Văn
 * thư đóng dấu). Danh mục: Loại con dấu (khung CRUD chung).
 */
export const approvalSealModule: ErpModule = {
  id: 'approval-seal',
  title: 'Duyệt dấu',
  description: 'Trình ký, duyệt và đóng dấu chứng từ, hợp đồng, văn bản hành chính.',
  icon: Stamp,
  path: appRoutes.approvalSeal.root,
  accent: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
  enabled: true,

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.approvalSeal.root,
      icon: LayoutDashboard,
      entity: 'seal_request',
      end: true,
    },
    {
      label: 'Yêu cầu đóng dấu',
      path: appRoutes.approvalSeal.requests,
      icon: ClipboardList,
      entity: 'seal_request',
    },
    {
      //  Cấu hình văn thư — dùng chung khóa quyền `seal_type` (Quản trị con dấu).
      label: 'Phân công văn thư',
      path: appRoutes.approvalSeal.clerks,
      icon: UserCog,
      entity: 'seal_type',
      group: 'Cài đặt',
    },
  ],

  routes: [
    {
      path: appRoutes.approvalSeal.root,
      lazy: async () => ({
        Component: (await import('./pages/seal-dashboard-page')).SealDashboardPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.requests,
      lazy: async () => ({
        Component: (await import('./pages/seal-request-list-page')).SealRequestListPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.new,
      lazy: async () => ({
        Component: (await import('./pages/seal-request-form-page')).SealRequestFormPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.edit(':id'),
      lazy: async () => ({
        Component: (await import('./pages/seal-request-form-page')).SealRequestFormPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.sealTypes,
      lazy: async () => ({
        Component: (await import('./pages/seal-type-list-page')).SealTypeListPage,
      }),
    },
    {
      path: `${appRoutes.approvalSeal.sealTypes}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/seal-type-detail-page')).SealTypeDetailPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.clerks,
      lazy: async () => ({
        Component: (await import('./pages/seal-clerk-list-page')).SealClerkListPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.clerksNew,
      lazy: async () => ({
        Component: (await import('./pages/seal-clerk-form-page')).SealClerkFormPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.clerkDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/seal-clerk-detail-page')).SealClerkDetailPage,
      }),
    },
    {
      path: appRoutes.approvalSeal.detail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/seal-request-detail-page')).SealRequestDetailPage,
      }),
    },
  ],
}
