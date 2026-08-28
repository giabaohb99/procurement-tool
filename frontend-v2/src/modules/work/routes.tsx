import { FolderKanban, LayoutDashboard, ListChecks } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ DỰ ÁN — task list kiểu Lark Tasks (CR-216).
 *
 * Thiết kế đầy đủ ở `doc/erp/cong-viec/`; lộ trình W0…W5 ở `03-lo-trinh-phase.md`.
 * Đã xong W0 (bảng dữ liệu + phân quyền), W1 (API) và phần lớn W2 (kanban, khung
 * nhìn danh sách, panel chi tiết) — phần còn thiếu của W2 ghi ở `03`.
 *
 * **MỘT DỰ ÁN CHÍNH LÀ MỘT DANH SÁCH CÔNG VIỆC** (`WorkList`), không phải hai
 * tầng chồng nhau. Trước đây hệ có hai phân hệ mang hai tên cho cùng một thứ:
 * «Công việc» làm thật ở đây, và «Dự án» chỉ là khung rỗng "Sắp có". Nay gộp về
 * một, lấy tên **Dự án** vì đó là cách người dùng gọi.
 *
 * ⚠️ Chỉ đổi tên ở tầng NGƯỜI DÙNG. Thư mục vẫn là `modules/work/`, API vẫn
 * `/api/work/...`, entity phân quyền vẫn `work_task`, bảng vẫn `tab_work_*`:
 * đổi mấy thứ đó phải kèm migration và nạp lại phân quyền trên máy thật, tốn mà
 * người dùng không thấy gì. Chữ "task" trần thì vẫn cấm dùng — nó đã bị bộ máy
 * duyệt và tab «Việc cần làm» (`/api/dashboard/tasks`, CR-215) chiếm.
 */
export const workModule: ErpModule = {
  id: 'work',
  title: 'Dự án',
  description: 'Dự án, bảng kanban, giao việc và theo dõi tiến độ.',
  icon: ListChecks,
  path: appRoutes.project.root,
  accent: 'bg-lime-500/10 text-lime-600 dark:text-lime-400',
  enabled: true,
  entity: 'work_task',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.project.root,
      icon: LayoutDashboard,
      entity: 'work_task',
      end: true,
    },
    {
      label: 'Dự án',
      path: appRoutes.project.list,
      icon: FolderKanban,
      entity: 'work_task',
      end: true,
    },
  ],

  //  Cây danh sách bên trái là route CHA: đổi danh sách thì chỉ phần bên phải
  //  dựng lại, cây giữ nguyên trạng thái mở/đóng của từng nhóm.
  routes: [
    {
      path: appRoutes.project.root,
      lazy: async () => ({
        Component: (await import('./pages/work-layout-page')).WorkLayoutPage,
      }),
      children: [
        {
          index: true,
          lazy: async () => ({
            Component: (await import('./pages/work-overview-page')).WorkOverviewPage,
          }),
        },
        {
          //  Bảng liệt kê mọi dự án. Không đụng `lists/:listId` — react-router chấm
          //  điểm theo độ cụ thể của mẫu, đường tĩnh luôn thắng đường có tham số.
          path: 'lists',
          lazy: async () => ({
            Component: (await import('./pages/project-list-page')).ProjectListPage,
          }),
        },
        {
          path: 'lists/:listId',
          lazy: async () => ({
            Component: (await import('./pages/work-list-page')).WorkListPage,
          }),
        },
      ],
    },
  ],
}
