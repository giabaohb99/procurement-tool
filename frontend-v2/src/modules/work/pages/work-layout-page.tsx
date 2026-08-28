import { useState } from 'react'
import { Outlet, useMatch } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { WorkCreateDialog } from '../components/work-create-dialog'
import { WorkSidebarTree } from '../components/work-sidebar-tree'

/**
 * Khung của phân hệ Công việc: cây danh sách bên trái + nội dung bên phải.
 *
 * Cây là route CHA nên nó không bị dựng lại mỗi lần đổi danh sách — trạng thái
 * mở/đóng của từng nhóm giữ nguyên, đúng như Lark.
 *
 * ⚠️ Cây nằm TRONG TRANG chứ không nhét vào menu trái của vỏ ERP. Đã thử đưa
 * vào menu chung (28/08/2026) rồi **bỏ**: menu đó là khuôn chung của mọi phân
 * hệ, nhét một cây dữ liệu người dùng vào là phá khuôn — cả `ErpModule` lẫn
 * `ModuleSidebar` phải mọc thêm một lối rẽ chỉ một phân hệ dùng.
 */
export function WorkLayoutPage() {
  const [dialog, setDialog] = useState<'list' | 'group' | null>(null)
  const [parentGroup, setParentGroup] = useState<number | null>(null)

  //  Màn Tổng quan là trang BÁO CÁO toàn chiều ngang, giống các phân hệ khác:
  //  không dựng cây dự án bên cạnh. Cây chỉ có nghĩa khi đang thao tác trên một
  //  dự án cụ thể — đứng cạnh biểu đồ nó chỉ chiếm mất một phần tư màn hình.
  const isOverview = useMatch(appRoutes.project.root) !== null

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {!isOverview && (
        <WorkSidebarTree
          onCreateGroup={() => {
            setParentGroup(null)
            setDialog('group')
          }}
          onCreateList={(groupId) => {
            setParentGroup(groupId)
            setDialog('list')
          }}
        />
      )}

      {/*  Bảng kanban tự cuộn bên trong nên khung ngoài phải khóa tràn; trang
          báo cáo thì dài theo nội dung, khóa tràn là cụt mất biểu đồ cuối. */}
      <div
        className={cn(
          'flex min-w-0 flex-1 flex-col',
          isOverview ? 'overflow-y-auto' : 'overflow-hidden',
        )}
      >
        <Outlet />
      </div>

      <WorkCreateDialog
        mode={dialog}
        parentGroupId={parentGroup}
        onClose={() => setDialog(null)}
      />
    </div>
  )
}
