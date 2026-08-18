import { GitBranch, Inbox, ListChecks, Power } from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { ApprovalEnginePage } from './pages/approval-engine-page'
import { ApprovalFlowDesignerPage } from './pages/approval-flow-designer-page'
import { ApprovalFlowListPage } from './pages/approval-flow-list-page'
import { MyTasksPage } from './pages/my-tasks-page'

/**
 * PHÊ DUYỆT — bộ máy dùng chung, **không phải một phân hệ nghiệp vụ**.
 *
 * Nó đứng riêng vì «Việc của tôi» gom việc của CẢ văn thư lẫn thu mua: nhét vào
 * một phân hệ nào đó thì người dùng phải đoán xem hộp việc của mình nằm ở đâu.
 *
 * Trang gốc chuyển thẳng sang «Việc của tôi» — đó là thứ 9 trên 10 lần người ta
 * vào đây để xem; màn khai luồng chỉ đụng tới lúc cấu hình.
 */
export const approvalModule: ErpModule = {
  id: 'approval',
  title: 'Phê duyệt',
  description: 'Việc đang chờ bạn và cấu hình luồng duyệt dùng chung.',
  icon: ListChecks,
  path: appRoutes.approval.root,
  accent: 'bg-amber-50 text-amber-600',
  enabled: true,
  //  KHÔNG khai `entity`: ai đăng nhập cũng có hộp việc của mình, khóa cả phân
  //  hệ theo quyền là người dùng thường không thấy việc của chính họ. Riêng màn
  //  khai luồng gắn `approval_flow` ở mục menu bên dưới.

  nav: [
    {
      label: 'Việc của tôi',
      path: appRoutes.approval.myTasks,
      icon: Inbox,
    },
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
    { path: appRoutes.approval.root, element: <Navigate to={appRoutes.approval.myTasks} replace /> },
    { path: appRoutes.approval.myTasks, element: <MyTasksPage /> },
    { path: appRoutes.approval.flows, element: <ApprovalFlowListPage /> },
    { path: appRoutes.approval.engine, element: <ApprovalEnginePage /> },
    { path: appRoutes.approval.flowNew, element: <ApprovalFlowDesignerPage /> },
    { path: '/approval/flows/:id', element: <ApprovalFlowDesignerPage /> },
  ],
}
