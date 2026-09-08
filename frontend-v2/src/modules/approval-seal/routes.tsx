import { ClipboardList, Stamp } from 'lucide-react'

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
      label: 'Yêu cầu đóng dấu',
      path: appRoutes.approvalSeal.root,
      icon: ClipboardList,
      entity: 'seal_request',
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.approvalSeal.root,
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
      path: appRoutes.approvalSeal.detail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/seal-request-detail-page')).SealRequestDetailPage,
      }),
    },
  ],
}
