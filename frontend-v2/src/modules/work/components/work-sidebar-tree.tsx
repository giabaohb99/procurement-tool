import {
  ChevronDown,
  ChevronRight,
  FolderKanban,
  FolderPlus,
  ListPlus,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Pin,
  PinOff,
  Settings2,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { usePinnedLists } from '../hooks/use-pinned-lists'
import { useWorkSidebar } from '../hooks/use-work-lists'
import type { WorkGroupNode, WorkList } from '../types/work'
import { collectSidebarLists } from '../utils/pinned-lists'
import { dotClass } from '../utils/work-colors'

interface WorkSidebarTreeProps {
  /** Mở hộp thoại tạo — trang cha giữ hộp thoại để cây chỉ lo việc vẽ. */
  onCreateList: (groupId: number | null) => void
  /** `parentId` = tạo NHÓM CON trong nhóm đó (bao-CR-482); `null` = nhóm cấp 1. */
  onCreateGroup: (parentId: number | null) => void
  /** Mở hộp Quản lý nhóm (đổi tên · thành viên · lưu trữ) — bao-CR-482. */
  onManageGroup: (group: WorkGroupNode) => void
  /**
   * Bản HÉ RA khi rê chuột vào mép trái (cây đang ẩn, chưa ghim lại). Lúc ấy nút
   * ở dải tiêu đề đổi nghĩa: không phải «Ẩn» nữa mà là «Ghim» — bấm để cây ở lại
   * hẳn thay vì biến mất ngay khi con trỏ đi chỗ khác.
   */
  peeking?: boolean
  /** Ẩn cây, hoặc ghim lại nếu đang hé ra. Trạng thái ở `WorkLayoutPage`. */
  onToggleCollapse: () => void
  /**
   * Vừa bấm vào một dự án. Chỉ khổ hẹp cần: ở đó cây nằm trong tờ trượt phủ gần
   * trọn màn hình, phải tự đóng lại mới thấy được dự án vừa chọn. Bản cắm cứng
   * bên trái không truyền — chuyển trang là cây đứng yên, đúng như mong đợi.
   */
  onNavigate?: () => void
}

/**
 * Cây điều hướng bên trái của phân hệ (A-05): nhóm → nhóm con → list.
 *
 * Đây là sidebar CỦA MÀN HÌNH, không phải sidebar của vỏ ERP: nội dung đổi theo
 * dữ liệu người dùng nên không khai được vào `nav` tĩnh trong `routes.tsx`, và
 * cũng KHÔNG nhét vào menu chung — xem ghi chú ở `work-layout-page.tsx`.
 */
export function WorkSidebarTree({
  onCreateList,
  onCreateGroup,
  onManageGroup,
  peeking = false,
  onToggleCollapse,
  onNavigate,
}: WorkSidebarTreeProps) {
  const { data, isLoading } = useWorkSidebar()
  const pins = usePinnedLists()

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
  //  Khu ghim: lấy THEO THỨ TỰ ghim, bỏ id không còn trong cây (dự án đã lưu trữ / bị gỡ quyền).
  const byId = new Map(collectSidebarLists(groups, loose).map((l) => [l.id, l]))
  const pinnedLists = pins.pinned.flatMap((id) => byId.get(id) ?? [])

  return (
    //  Bản HÉ RA bỏ `border-r`: nó nằm trong một thẻ nổi đã có viền riêng, để
    //  nguyên là hai đường kẻ dọc sát nhau ở mép phải.
    <nav className={cn('flex h-full w-64 shrink-0 flex-col', !peeking && 'border-r')}>
      <div className="flex items-center justify-between gap-1 border-b px-3 py-2">
        <span className="text-sm font-semibold text-navy">Danh sách dự án</span>
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon"
            title="Tạo nhóm dự án"
            onClick={() => onCreateGroup(null)}
          >
            <FolderPlus className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" title="Tạo dự án" onClick={() => onCreateList(null)}>
            <ListPlus className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title={peeking ? 'Ghim danh sách dự án' : 'Ẩn danh sách dự án'}
            aria-label={peeking ? 'Ghim danh sách dự án' : 'Ẩn danh sách dự án'}
            onClick={onToggleCollapse}
          >
            {peeking ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {trong && (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Chưa có dự án nào. Bấm dấu cộng ở trên để tạo.
          </p>
        )}
        {pinnedLists.length > 0 && (
          <div className="mb-2 border-b pb-2" aria-label="Dự án đã ghim">
            <p className="px-2 pb-1 text-xs font-medium text-muted-foreground uppercase">Đã ghim</p>
            {pinnedLists.map((l) => (
              <ListLink
                key={l.id}
                item={l}
                depth={0}
                pinned
                onTogglePin={() => pins.toggle(l.id)}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        )}
        {groups.map((g) => (
          <GroupNode
            key={g.id}
            node={g}
            depth={0}
            pins={pins}
            onCreateList={onCreateList}
            onCreateGroup={onCreateGroup}
            onManageGroup={onManageGroup}
            onNavigate={onNavigate}
          />
        ))}
        {/* List không thuộc nhóm nào đứng cuối cây — vẫn hợp lệ (A-08). */}
        {loose.map((l) => (
          <ListLink
            key={l.id}
            item={l}
            depth={0}
            pinned={pins.isPinned(l.id)}
            onTogglePin={() => pins.toggle(l.id)}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </nav>
  )
}

interface GroupNodeProps {
  node: WorkGroupNode
  depth: number
  pins: ReturnType<typeof usePinnedLists>
  onCreateList: (groupId: number | null) => void
  onCreateGroup: (parentId: number | null) => void
  onManageGroup: (group: WorkGroupNode) => void
  onNavigate?: () => void
}

function GroupNode({
  node,
  depth,
  pins,
  onCreateList,
  onCreateGroup,
  onManageGroup,
  onNavigate,
}: GroupNodeProps) {
  const [mo, setMo] = useState(true)
  const Icon = mo ? ChevronDown : ChevronRight
  //  Cây chỉ hai cấp (backend chặn cấp 3) — nhóm con không có mục «Thêm nhóm con».
  const canNest = depth === 0

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
          {/*  Nhóm dự án (trên dữ liệu là NHÓM) không có bảng việc riêng — biểu
               tượng thư mục để khỏi lẫn với dự án thường, vốn mang chấm màu. */}
          <FolderKanban className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{node.name}</span>
        </button>
        {/*  Chỉ hiện khi rê chuột: hàng nào cũng có nút thì cây thành rừng nút.
            Vẫn giữ được bằng bàn phím nhờ `focus-visible:opacity-100`. */}
        <Button
          variant="ghost"
          size="icon"
          title="Tạo dự án trong nhóm"
          aria-label={`Tạo dự án trong nhóm ${node.name}`}
          className="size-6 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
          onClick={() => onCreateList(node.id)}
        >
          <ListPlus className="size-3.5" />
        </Button>
        {/*  bao-CR-482: menu của NHÓM — trước đây nhóm tạo xong là không đổi tên,
            không mời ai, không lưu trữ được từ giao diện dù API đã có. */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              title="Thao tác với nhóm dự án"
              aria-label={`Thao tác với nhóm dự án ${node.name}`}
              className="size-6 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
            >
              <MoreHorizontal className="size-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem onSelect={() => onManageGroup(node)}>
              <Settings2 className="size-4" />
              Quản lý nhóm dự án
            </DropdownMenuItem>
            {canNest && (
              <DropdownMenuItem onSelect={() => onCreateGroup(node.id)}>
                <FolderPlus className="size-4" />
                Tạo nhóm con
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onSelect={() => onCreateList(node.id)}>
              <ListPlus className="size-4" />
              Tạo dự án trong nhóm
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {mo && (
        <>
          {node.children.map((c) => (
            <GroupNode
              key={c.id}
              node={c}
              depth={depth + 1}
              pins={pins}
              onCreateList={onCreateList}
              onCreateGroup={onCreateGroup}
              onManageGroup={onManageGroup}
              onNavigate={onNavigate}
            />
          ))}
          {node.lists.map((l) => (
            <ListLink
              key={l.id}
              item={l}
              depth={depth + 1}
              pinned={pins.isPinned(l.id)}
              onTogglePin={() => pins.toggle(l.id)}
              onNavigate={onNavigate}
            />
          ))}
        </>
      )}
    </div>
  )
}

function ListLink({
  item,
  depth,
  pinned,
  onTogglePin,
  onNavigate,
}: {
  item: WorkList
  depth: number
  pinned: boolean
  onTogglePin: () => void
  onNavigate?: () => void
}) {
  return (
    //  Nút ghim đứng NGOÀI thẻ liên kết: lồng nút trong <a> là hai điều khiển
    //  tương tác chồng nhau, trình đọc màn hình đọc sai và bấm ghim lại nhảy trang.
    <div className="group/list relative">
      <NavLink
        to={appRoutes.project.detail(item.id)}
        onClick={onNavigate}
        style={{ paddingLeft: depth * 12 + 26 }}
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2 rounded-md py-1.5 pr-8 text-sm hover:bg-accent',
            isActive && 'bg-accent font-medium text-accent-foreground',
          )
        }
      >
        <span className={cn('size-2 shrink-0 rounded-full', dotClass(item.color))} />
        <span className="truncate">{item.name}</span>
      </NavLink>
      <Button
        variant="ghost"
        size="icon"
        title={pinned ? 'Bỏ ghim' : 'Ghim lên đầu danh sách'}
        aria-label={pinned ? `Bỏ ghim ${item.name}` : `Ghim ${item.name}`}
        aria-pressed={pinned}
        onClick={onTogglePin}
        //  Đã ghim thì luôn hiện (để thấy trạng thái); chưa ghim chỉ hiện khi rê / tiêu điểm.
        className={cn(
          'absolute top-1/2 right-1 size-6 -translate-y-1/2 focus-visible:opacity-100',
          pinned ? 'opacity-100' : 'opacity-0 group-hover/list:opacity-100',
        )}
      >
        {pinned ? <PinOff className="size-3.5" /> : <Pin className="size-3.5" />}
      </Button>
    </div>
  )
}
