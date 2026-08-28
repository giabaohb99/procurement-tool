import { ChevronDown, ChevronRight, FolderPlus, ListPlus } from 'lucide-react'
import { useState } from 'react'
import { NavLink } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useWorkSidebar } from '../hooks/use-work-lists'
import type { WorkGroupNode, WorkList } from '../types/work'
import { dotClass } from '../utils/work-colors'

interface WorkSidebarTreeProps {
  /** Mở hộp thoại tạo — trang cha giữ hộp thoại để cây chỉ lo việc vẽ. */
  onCreateList: (groupId: number | null) => void
  onCreateGroup: () => void
}

/**
 * Cây điều hướng bên trái của phân hệ (A-05): nhóm → nhóm con → list.
 *
 * Đây là sidebar CỦA MÀN HÌNH, không phải sidebar của vỏ ERP: nội dung đổi theo
 * dữ liệu người dùng nên không khai được vào `nav` tĩnh trong `routes.tsx`, và
 * cũng KHÔNG nhét vào menu chung — xem ghi chú ở `work-layout-page.tsx`.
 */
export function WorkSidebarTree({ onCreateList, onCreateGroup }: WorkSidebarTreeProps) {
  const { data, isLoading } = useWorkSidebar()

  if (isLoading) {
    return (
      <div className="space-y-2 p-3">
        <Skeleton className="h-7 w-full" />
        <Skeleton className="h-7 w-4/5" />
        <Skeleton className="h-7 w-3/5" />
      </div>
    )
  }

  const groups = data?.groups ?? []
  const loose = data?.lists ?? []
  const trong = groups.length === 0 && loose.length === 0

  return (
    <nav className="flex h-full w-64 shrink-0 flex-col border-r">
      <div className="flex items-center justify-between gap-1 border-b px-3 py-2">
        <span className="text-sm font-semibold text-navy">Danh sách dự án</span>
        <div className="flex items-center gap-0.5">
          <Button variant="ghost" size="icon" title="Nhóm mới" onClick={onCreateGroup}>
            <FolderPlus className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="Danh sách mới"
            onClick={() => onCreateList(null)}
          >
            <ListPlus className="size-4" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {trong && (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Chưa có danh sách nào. Bấm dấu cộng ở trên để tạo.
          </p>
        )}
        {groups.map((g) => (
          <GroupNode key={g.id} node={g} depth={0} onCreateList={onCreateList} />
        ))}
        {/* List không thuộc nhóm nào đứng cuối cây — vẫn hợp lệ (A-08). */}
        {loose.map((l) => (
          <ListLink key={l.id} item={l} depth={0} />
        ))}
      </div>
    </nav>
  )
}

interface GroupNodeProps {
  node: WorkGroupNode
  depth: number
  onCreateList: (groupId: number | null) => void
}

function GroupNode({ node, depth, onCreateList }: GroupNodeProps) {
  const [mo, setMo] = useState(true)
  const Icon = mo ? ChevronDown : ChevronRight

  return (
    <div>
      <div
        className="group flex items-center gap-1 rounded-md px-2 py-1.5 hover:bg-accent"
        style={{ paddingLeft: depth * 12 + 8 }}
      >
        <button
          type="button"
          onClick={() => setMo((v) => !v)}
          className="flex min-w-0 flex-1 items-center gap-1.5 text-left text-sm font-medium"
        >
          <Icon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{node.name}</span>
        </button>
        {/*  Chỉ hiện khi rê chuột: hàng nào cũng có nút thì cây thành rừng nút.
            Vẫn giữ được bằng bàn phím nhờ `focus-visible:opacity-100`. */}
        <Button
          variant="ghost"
          size="icon"
          title="Thêm danh sách vào nhóm này"
          aria-label={`Thêm danh sách vào nhóm ${node.name}`}
          className="size-6 opacity-0 focus-visible:opacity-100 group-hover:opacity-100"
          onClick={() => onCreateList(node.id)}
        >
          <ListPlus className="size-3.5" />
        </Button>
      </div>

      {mo && (
        <>
          {node.children.map((c) => (
            <GroupNode key={c.id} node={c} depth={depth + 1} onCreateList={onCreateList} />
          ))}
          {node.lists.map((l) => (
            <ListLink key={l.id} item={l} depth={depth + 1} />
          ))}
        </>
      )}
    </div>
  )
}

function ListLink({ item, depth }: { item: WorkList; depth: number }) {
  return (
    <NavLink
      to={appRoutes.project.detail(item.id)}
      style={{ paddingLeft: depth * 12 + 26 }}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-2 rounded-md py-1.5 pr-2 text-sm hover:bg-accent',
          isActive && 'bg-accent font-medium text-accent-foreground',
        )
      }
    >
      <span className={cn('size-2 shrink-0 rounded-full', dotClass(item.color))} />
      <span className="truncate">{item.name}</span>
    </NavLink>
  )
}
