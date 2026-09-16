import { FolderOpen, Tags } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ HỒ SƠ — **nửa thật nửa mẫu**, đọc kỹ trước khi sửa:
 *
 * - **Loại hồ sơ** (`/dossier/types`) chạy trên dữ liệu THẬT: bảng
 *   `tab_dossier_type`, API `/api/dossier-types`, khóa quyền `dossier_type`.
 * - **Danh sách hồ sơ** (`/dossier`) vẫn là DỮ LIỆU MẪU trong trình duyệt.
 *
 * ⚠️ Ba việc còn nợ, làm cùng lúc với bảng `tab_dossier`:
 * 1. **Chốt loại hồ sơ** (lưu trữ pháp lý / dự án / đối tác / thầu) — bộ trường
 *    ở `types/dossier.ts` đang là khuôn chung, chốt xong mới dựng model.
 * 2. **Backend cho hồ sơ**: bảng + Alembic + controller, rồi thay ruột
 *    `fetchDossiers` bằng `apiGet`. Xóa `api/dossier-mock-data.ts`. Hồ sơ nối
 *    loại bằng `dossier_type_id` **và** giữ một cột nhãn chép sẵn (bản in với
 *    tệp Excel đọc thẳng cột chữ — bài học duoc-CR-320).
 * 3. **Khóa phân quyền `dossier`** trong `core/permissions.py` (kèm khai
 *    `SCOPE_FIELDS`), rồi gắn `entity` cho mục *Danh sách hồ sơ* dưới đây và bỏ
 *    `dossier` khỏi `openByDesign` trong `module-registry.test.ts` +
 *    `module-visibility.test.ts`. Tới lúc đó màn đó mới thật sự được gác — hiện
 *    giờ **ai đăng nhập cũng thấy** nó.
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
      path: appRoutes.dossier.root,
      icon: FolderOpen,
      //  CHƯA khai `entity`: khóa `dossier` chưa tồn tại ở backend. Xem ghi chú 3
      //  ở đầu tệp — đây là món nợ, không phải chủ ý mở công khai.
      end: true,
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
      path: appRoutes.dossier.root,
      lazy: async () => ({
        Component: (await import('./pages/dossier-list-page')).DossierListPage,
      }),
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
