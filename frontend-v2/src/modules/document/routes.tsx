import {
  BookMarked,
  FileText,
  Files,
  LayoutDashboard,
  SlidersHorizontal,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ VĂN BẢN — quản lý văn bản đến / đi / nội bộ và các danh mục nền.
 *
 * ⚠️ Backend CHƯA có gì cho phân hệ này: dữ liệu đang nằm ở kho tạm phía trình
 * duyệt (`store/local-collection.ts`) và `ENTITIES` trong `core/permissions.py`
 * chưa có `document`. Vì vậy chưa gắn được `entity` để lọc quyền — hiện ai đăng
 * nhập cũng thấy phân hệ này.
 */
export const documentModule: ErpModule = {
  id: 'document',
  title: 'Văn bản',
  description: 'Công văn, quyết định, hợp đồng và biểu mẫu nội bộ.',
  icon: FileText,
  path: appRoutes.document.root,
  accent: 'bg-indigo-50 text-indigo-600',
  enabled: true,

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.document.root,
      icon: LayoutDashboard,
      end: true,
    },
    { label: 'Văn bản', path: appRoutes.document.documents, icon: Files, group: 'Nghiệp vụ' },
    { label: 'Sổ văn bản', path: appRoutes.document.books, icon: BookMarked, group: 'Nghiệp vụ' },
    // Bốn danh mục nền gom vào MỘT mục menu: chúng chỉ được đụng tới lúc khai
    // báo ban đầu, để bốn dòng riêng thì menu dài hơn cả phần việc hằng ngày.
    {
      label: 'Thiết lập văn bản',
      path: appRoutes.document.settings,
      icon: SlidersHorizontal,
      group: 'Danh mục',
    },
  ],

  // `/new` khai trước `/:id` cho dễ đọc; react-router vẫn tự ưu tiên route tĩnh
  // nên thứ tự này chỉ là quy ước.
  routes: [
    {
      path: appRoutes.document.root,
      lazy: async () => ({
        Component: (await import('./pages/document-dashboard-page')).DocumentDashboardPage,
      }),
    },
    {
      path: appRoutes.document.documents,
      lazy: async () => ({
        Component: (await import('./pages/document-list-page')).DocumentListPage,
      }),
    },
    {
      path: appRoutes.document.documentNew,
      lazy: async () => ({
        Component: (await import('./pages/document-create-page')).DocumentCreatePage,
      }),
    },
    {
      path: appRoutes.document.documentDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-detail-page')).DocumentDetailPage,
      }),
    },
    {
      path: appRoutes.document.books,
      lazy: async () => ({
        Component: (await import('./pages/document-book-page')).DocumentBookPage,
      }),
    },
    {
      path: appRoutes.document.settings,
      lazy: async () => ({
        Component: (await import('./pages/document-settings-page')).DocumentSettingsPage,
      }),
    },
    {
      path: appRoutes.document.typeNew,
      lazy: async () => ({
        Component: (await import('./pages/document-type-detail-page'))
          .DocumentTypeDetailPage,
      }),
    },
    {
      path: appRoutes.document.typeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-type-detail-page'))
          .DocumentTypeDetailPage,
      }),
    },
    {
      path: appRoutes.document.securityLevelNew,
      lazy: async () => ({
        Component: (await import('./pages/security-level-detail-page'))
          .SecurityLevelDetailPage,
      }),
    },
    {
      path: appRoutes.document.securityLevelDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/security-level-detail-page'))
          .SecurityLevelDetailPage,
      }),
    },
    {
      path: appRoutes.document.partnerNew,
      lazy: async () => ({
        Component: (await import('./pages/document-partner-detail-page'))
          .DocumentPartnerDetailPage,
      }),
    },
    {
      path: appRoutes.document.partnerDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-partner-detail-page'))
          .DocumentPartnerDetailPage,
      }),
    },
    {
      path: appRoutes.document.fieldNew,
      lazy: async () => ({
        Component: (await import('./pages/dynamic-field-detail-page'))
          .DynamicFieldDetailPage,
      }),
    },
    {
      path: appRoutes.document.fieldDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/dynamic-field-detail-page'))
          .DynamicFieldDetailPage,
      }),
    },
  ],
}
