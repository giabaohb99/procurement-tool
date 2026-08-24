import {
  BookMarked,
  FileText,
  Files,
  Hash,
  LayoutDashboard,
  Link2,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { DocumentApprovalNavBadge } from './components/document-approval-nav-badge'

/**
 * Phân hệ VĂN THƯ — soạn thảo, duyệt, ban hành và tra cứu văn bản.
 *
 * Trục của văn bản là **loại × pháp nhân ban hành × phiên bản**. Toàn bộ phân
 * hệ đã chạy trên backend thật (`/api/documents`, `/api/doc-types`,
 * `/api/external-parties`, `/api/document-books`).
 *
 * **Sổ văn bản là một phần của đường làm việc chính**, không phải màn phụ: văn
 * bản vào sổ thì được cấp thêm một số thứ tự trong sổ, và **thành viên của sổ
 * đọc được mọi văn bản trong sổ đó** (người quản lý sổ sửa được) — cách cấp
 * quyền theo quyển thay vì chia tay từng văn bản.
 */
export const documentModule: ErpModule = {
  id: 'document',
  title: 'Văn bản',
  description: 'Công văn, quyết định, hợp đồng và biểu mẫu nội bộ.',
  icon: FileText,
  path: appRoutes.document.root,
  accent: 'bg-indigo-50 text-indigo-600',
  enabled: true,
  //  Không có quyền nào trên văn bản thì không thấy cả phân hệ.
  entity: 'document',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.document.root,
      icon: LayoutDashboard,
      end: true,
    },
    {
      label: 'Văn bản',
      path: appRoutes.document.documents,
      icon: Files,
      entity: 'document',
      group: 'Nghiệp vụ',
    },
    {
      //  CHỜ TÔI DUYỆT — đứng ngay dưới «Văn bản» vì đó là việc phải làm trong
      //  ngày, còn mọi mục dưới nữa là tra cứu và khai báo.
      //
      //  KHÔNG khai `entity`: người duyệt trong luồng thường **không có vai trò
      //  nào** ở phân hệ Văn bản (backend cũng đã mở đúng khe đó, xem
      //  `doc_reader` trong `controller.py`). Gác mục này bằng `document.read`
      //  là giấu việc của chính họ khỏi mắt họ.
      label: 'Chờ tôi duyệt',
      path: appRoutes.document.pendingApproval,
      icon: ShieldCheck,
      badge: DocumentApprovalNavBadge,
      group: 'Nghiệp vụ',
    },
    {
      label: 'Sổ văn bản',
      path: appRoutes.document.books,
      icon: BookMarked,
      entity: 'document_book',
      group: 'Nghiệp vụ',
    },
    // Các danh mục nền gom vào MỘT mục menu: chúng chỉ được đụng tới lúc khai
    // báo ban đầu, để mỗi cái một dòng thì menu dài hơn cả phần việc hằng ngày.
    {
      label: 'Thiết lập văn bản',
      path: appRoutes.document.settings,
      icon: SlidersHorizontal,
      entity: 'doc_type',
      group: 'Danh mục',
    },
    {
      label: 'Quy tắc đánh số',
      path: appRoutes.document.numberingRules,
      icon: Hash,
      entity: 'doc_type',
      group: 'Danh mục',
    },
    {
      label: 'Quy tắc quan hệ',
      path: appRoutes.document.linkRules,
      icon: Link2,
      entity: 'doc_type',
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
      path: appRoutes.document.pendingApproval,
      lazy: async () => ({
        Component: (await import('./pages/document-pending-approval-page'))
          .DocumentPendingApprovalPage,
      }),
    },
    {
      path: appRoutes.document.books,
      lazy: async () => ({
        Component: (await import('./pages/document-book-page')).DocumentBookPage,
      }),
    },
    {
      path: appRoutes.document.bookNew,
      lazy: async () => ({
        Component: (await import('./pages/document-book-detail-page')).DocumentBookDetailPage,
      }),
    },
    {
      path: appRoutes.document.bookDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-book-detail-page')).DocumentBookDetailPage,
      }),
    },
    {
      path: appRoutes.document.settings,
      lazy: async () => ({
        Component: (await import('./pages/document-settings-page')).DocumentSettingsPage,
      }),
    },
    {
      path: appRoutes.document.numberingRules,
      lazy: async () => ({
        Component: (await import('./pages/document-numbering-rules-page'))
          .DocumentNumberingRulesPage,
      }),
    },
    {
      path: appRoutes.document.numberingRuleNew,
      lazy: async () => ({
        Component: (await import('./pages/document-numbering-rule-detail-page'))
          .DocumentNumberingRuleDetailPage,
      }),
    },
    {
      path: appRoutes.document.numberingRuleDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-numbering-rule-detail-page'))
          .DocumentNumberingRuleDetailPage,
      }),
    },
    {
      //  Màn «Áp dụng cho tôi» nay là tab «Văn bản đến» của màn Văn bản. Giữ
      //  đường dẫn cũ để link đã gửi cho nhau và trang đã ghim còn mở được —
      //  chuyển hướng chứ không để 404.
      path: appRoutes.document.appliedToMe,
      element: <Navigate to={appRoutes.document.documents} replace />,
    },
    {
      path: appRoutes.document.linkRules,
      lazy: async () => ({
        Component: (await import('./pages/document-link-rules-page')).DocumentLinkRulesPage,
      }),
    },
    {
      path: appRoutes.document.linkRuleNew,
      lazy: async () => ({
        Component: (await import('./pages/document-link-rule-detail-page'))
          .DocumentLinkRuleDetailPage,
      }),
    },
    {
      path: appRoutes.document.linkRuleDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-link-rule-detail-page'))
          .DocumentLinkRuleDetailPage,
      }),
    },
    {
      path: appRoutes.document.typeNew,
      lazy: async () => ({
        Component: (await import('./pages/document-type-detail-page')).DocumentTypeDetailPage,
      }),
    },
    {
      path: appRoutes.document.typeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-type-detail-page')).DocumentTypeDetailPage,
      }),
    },
    {
      path: appRoutes.document.templateNew,
      lazy: async () => ({
        Component: (await import('./pages/document-template-detail-page'))
          .DocumentTemplateDetailPage,
      }),
    },
    {
      path: appRoutes.document.templateDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-template-detail-page'))
          .DocumentTemplateDetailPage,
      }),
    },
    {
      path: appRoutes.document.partnerNew,
      lazy: async () => ({
        Component: (await import('./pages/document-partner-detail-page')).DocumentPartnerDetailPage,
      }),
    },
    {
      path: appRoutes.document.partnerDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/document-partner-detail-page')).DocumentPartnerDetailPage,
      }),
    },
    {
      path: appRoutes.document.securityLevelNew,
      lazy: async () => ({
        Component: (await import('./pages/security-level-detail-page')).SecurityLevelDetailPage,
      }),
    },
    {
      path: appRoutes.document.securityLevelDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/security-level-detail-page')).SecurityLevelDetailPage,
      }),
    },
  ],
}
