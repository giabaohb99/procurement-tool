import { FolderOpen, Tags } from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ HỒ SƠ — hiện **chỉ có danh mục Loại hồ sơ** (`/dossier/types`), chạy
 * trên dữ liệu thật: bảng `tab_dossier_type`, API `/api/dossier-types`, khóa
 * quyền `dossier_type`. `/dossier` chỉ là đường chuyển hướng vào đó.
 *
 * ⚠️ **Màn *Danh sách hồ sơ* CỐ Ý KHÔNG đăng ký route** (16/09/2026). Khuôn màn
 * đã dựng xong và còn nguyên trên đĩa — `pages/dossier-list-page.tsx` chạy trên
 * `api/dossier-mock-data.ts` — nhưng **không chỗ nào gọi tới**, và đó là chủ ý
 * về BẢO MẬT, không phải việc làm dở:
 *
 * Khóa quyền `dossier` chưa tồn tại ở backend, nên mục menu không khai được
 * `entity`. Mà `itemAllowed` coi **mục không khai `entity` là luôn hiện**, và
 * `canAccessRoute` trả `true` khi **không mục nào khớp đường dẫn**
 * (`module-visibility.ts:141`) — nghĩa là đăng ký route đó là mở nó cho **mọi
 * người đăng nhập**, ở cả hai lối vào. Hôm nay chỉ lộ dữ liệu giả; ngày ai đó
 * thay ruột `fetchDossiers` bằng `apiGet` thì **hồ sơ pháp lý của công ty lộ cho
 * toàn bộ nhân viên**, im lặng, không cần sửa dòng nào ở tệp này.
 *
 * ⚠️ Cũng vì vậy **đừng khai `SCOPE_FIELDS["dossier"] = PUBLIC` cho xong**: chưa
 * có model thì `ENTITY_MODEL_PATHS` không nhận cột thật (BB-2), nên PUBLIC là
 * lựa chọn duy nhất — và PUBLIC nghĩa là `apply_scope` **không lọc gì cả**. Đó
 * là đổi một món nợ nhìn thấy được lấy một món nợ vô hình.
 *
 * Bật lại màn này thì làm ĐỦ BỐN việc, theo đúng thứ tự:
 * 1. **Chốt bộ trường hồ sơ** — `types/dossier.ts` đang là khuôn chung.
 * 2. **Backend**: bảng `tab_dossier` + Alembic + controller. Nối loại bằng
 *    `dossier_type_id` **và** giữ một cột nhãn chép sẵn (bản in với tệp Excel đọc
 *    thẳng cột chữ — bài học duoc-CR-320).
 * 3. **Khóa quyền `dossier`** ở `core/permissions.py`, khai `SCOPE_FIELDS` bằng
 *    **cột thật** (chủ hồ sơ / bộ phận giữ) và thêm vào `ENTITY_MODEL_PATHS`.
 * 4. Mới đăng ký lại route + mục menu, **có `entity: 'dossier'`**, rồi thay ruột
 *    `fetchDossiers` bằng `apiGet` và xóa `api/dossier-mock-data.ts`.
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
      //  Gốc phân hệ không có màn riêng — đẩy thẳng vào danh mục. `ModuleLayout`
      //  đã chặn người thiếu quyền từ trước đó (`canOpenModule`), nên đường này
      //  chỉ chạy cho người vào được `/dossier/types`.
      path: appRoutes.dossier.root,
      element: <Navigate to={appRoutes.dossier.types} replace />,
    },
    {
      path: appRoutes.dossier.types,
      lazy: async () => ({
        Component: (await import('./pages/dossier-type-list-page')).DossierTypeListPage,
      }),
    },
    {
      //  ⚠️ Phải đứng TRƯỚC `:id` — cùng khuôn với `/hr/job-positions/new`.
      //  Đứng sau thì «new» khớp vào `:id`, khung CRUD gọi API chi tiết với một
      //  id không phải số và trang chỉ hiện lỗi tải.
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
