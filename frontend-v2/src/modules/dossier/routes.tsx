import { FolderOpen, Tags } from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ HỒ SƠ — kho giấy tờ công ty. Hai màn, **hai khóa quyền riêng**:
 *
 *   `/dossier/list`   → bảng `tab_dossier`,      khóa `dossier`
 *   `/dossier/types`  → bảng `tab_dossier_type`, khóa `dossier_type`
 *
 * Tách hai theo luật «một khóa = một màn hình» (CR-157), và vì hai việc do hai
 * nhóm người làm: lập hồ sơ là việc hằng ngày của hành chính mỗi phòng, còn sửa
 * LOẠI thì đổi luôn **khuôn biểu mẫu** (`field_schema`) cho cả công ty — gộp
 * một khóa là ai lập được một tờ giấy phép cũng xóa được ô «Số giấy phép» khỏi
 * mọi hồ sơ cùng loại.
 *
 * ⚠️ **MỌI mục menu ở đây BẮT BUỘC khai `entity`.** Khung điều hướng của
 * `frontend-v2` mặc định MỞ ở hai chỗ, cả hai im lặng: `itemAllowed` coi mục
 * không khai `entity` là luôn hiện, và `canAccessRoute` trả `true` khi **không
 * mục nào khớp đường dẫn** (`module-visibility.ts:141`). Nghĩa là đăng ký một
 * route mà không có mục menu gác nó = mở cho **mọi người đăng nhập**, ở cả hai
 * lối vào. Màn *Danh sách hồ sơ* từng nằm đúng trong tình trạng đó (16/09/2026)
 * và phải gỡ khỏi routing cho tới khi backend có khóa `dossier` thật.
 *
 * Nay nó đã có: `dossier` nằm trong `ENTITIES`, khai **cột thật** ở
 * `SCOPE_FIELDS` (pháp nhân · phòng · người lập · người phụ trách) — KHÔNG phải
 * `PUBLIC` — và có mặt trong `ENTITY_MODEL_PATHS`. Phạm vi kiểm bằng
 * `test/backend/test_ho_so_pham_vi.py`; luật gác của tệp này kiểm bằng
 * `routes.test.ts` ngay bên cạnh.
 */
export const dossierModule: ErpModule = {
  id: 'dossier',
  title: 'Hồ sơ',
  description: 'Kho hồ sơ công ty — nơi lưu bản gốc, người phụ trách, hạn hiệu lực.',
  icon: FolderOpen,
  path: appRoutes.dossier.root,
  accent: 'bg-green-500/10 text-green-600 dark:text-green-400',
  enabled: true,

  nav: [
    {
      label: 'Danh sách hồ sơ',
      path: appRoutes.dossier.list,
      icon: FolderOpen,
      entity: 'dossier',
    },
    {
      label: 'Loại hồ sơ',
      path: appRoutes.dossier.types,
      icon: Tags,
      entity: 'dossier_type',
      //  `manage: true` — mục chỉ hiện với người SỬA được danh mục. Mọi vai trò
      //  đều có `read` (seed cấp, vì ô chọn loại trên màn hồ sơ cần), nên gác
      //  bằng `read` là cả công ty thấy một mục mở ra chỉ để nhìn, mọi nút xám.
      manage: true,
      group: 'Danh mục',
    },
  ],

  routes: [
    {
      //  Gốc phân hệ không có màn riêng — đẩy vào danh sách hồ sơ. `ModuleLayout`
      //  đã chặn người thiếu quyền từ trước đó (`canOpenModule`).
      path: appRoutes.dossier.root,
      element: <Navigate to={appRoutes.dossier.list} replace />,
    },
    {
      path: appRoutes.dossier.list,
      lazy: async () => ({
        Component: (await import('./pages/dossier-list-page')).DossierListPage,
      }),
    },
    {
      //  ⚠️ Phải đứng TRƯỚC `:id` — cùng khuôn với `/hr/job-positions/new`.
      //  Đứng sau thì «new» khớp vào `:id`, khung CRUD gọi API chi tiết với một
      //  id không phải số và trang chỉ hiện lỗi tải.
      path: appRoutes.dossier.newDossier,
      lazy: async () => ({
        Component: (await import('./pages/dossier-detail-page')).DossierDetailPage,
      }),
    },
    {
      path: appRoutes.dossier.detail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/dossier-detail-page')).DossierDetailPage,
      }),
    },
    {
      path: appRoutes.dossier.types,
      lazy: async () => ({
        Component: (await import('./pages/dossier-type-list-page')).DossierTypeListPage,
      }),
    },
    {
      path: appRoutes.dossier.typeNew,
      lazy: async () => ({
        Component: (await import('./pages/dossier-type-detail-page')).DossierTypeDetailPage,
      }),
    },
    {
      path: appRoutes.dossier.typeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/dossier-type-detail-page')).DossierTypeDetailPage,
      }),
    },
  ],
}
