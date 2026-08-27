import { GitBranch, ListChecks, Power } from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { ApprovalEnginePage } from './pages/approval-engine-page'
import { ApprovalFlowDesignerPage } from './pages/approval-flow-designer-page'
import { ApprovalFlowListPage } from './pages/approval-flow-list-page'

/**
 * PHÊ DUYỆT — bộ máy dùng chung, **không phải một phân hệ nghiệp vụ**.
 *
 * ⚠️ **Chỉ còn phần CẤU HÌNH** (21/08/2026). Màn «Việc của tôi» đã xóa hẳn:
 * hộp việc nay nằm trong chính phân hệ của chứng từ («Chờ tôi duyệt» của Văn
 * bản), và duyệt thì bấm ngay trên chứng từ sau khi đã mở ra đọc. Một danh sách
 * gom chung có nút duyệt trên từng dòng mời người ta ký thứ chỉ nhìn thấy mỗi
 * cái tiêu đề — đúng cái đường tắt mà bộ máy này sinh ra để bịt.
 *
 * Bật bộ máy duyệt cho Thu mua thì dựng hộp việc TRONG phân hệ Thu mua, đừng
 * gọi lại màn gom chung.
 *
 * Trang gốc chuyển sang danh sách luồng — thứ duy nhất còn lại ở đây.
 */
export const approvalModule: ErpModule = {
  id: 'approval',
  title: 'Phê duyệt',
  description: 'Khai luồng duyệt dùng chung và bật bộ máy theo loại chứng từ.',
  icon: ListChecks,
  path: appRoutes.approval.root,
  accent: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  enabled: true,
  //  Cả phân hệ nay chỉ còn màn cấu hình, nên khóa thẳng bằng `approval_flow`:
  //  người dùng thường không có việc gì ở đây nữa.
  entity: 'approval_flow',

  nav: [
    {
      label: 'Luồng duyệt',
      path: appRoutes.approval.flows,
      icon: GitBranch,
      entity: 'approval_flow',
      group: 'Cấu hình',
    },
    {
      label: 'Bật bộ máy duyệt',
      path: appRoutes.approval.engine,
      icon: Power,
      entity: 'approval_flow',
      group: 'Cấu hình',
    },
  ],

  routes: [
    { path: appRoutes.approval.root, element: <Navigate to={appRoutes.approval.flows} replace /> },
    { path: appRoutes.approval.flows, element: <ApprovalFlowListPage /> },
    { path: appRoutes.approval.engine, element: <ApprovalEnginePage /> },
    { path: appRoutes.approval.flowNew, element: <ApprovalFlowDesignerPage /> },
    { path: '/approval/flows/:id', element: <ApprovalFlowDesignerPage /> },
  ],
}
