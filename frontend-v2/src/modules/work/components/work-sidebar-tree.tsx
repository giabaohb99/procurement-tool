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
import { useMemo, useState } from 'react'
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
import { useSidebarListDrag, type SidebarListDrag } from '../hooks/use-sidebar-list-drag'
import { useWorkSidebar } from '../hooks/use-work-lists'
import { WORK_ROLE, type WorkGroupNode, type WorkList } from '../types/work'
import { collectSidebarLists } from '../utils/pinned-lists'
import { flattenGroups, type FlatWorkGroup } from '../utils/work-groups'
import { ListRowMenu } from './list-row-menu'
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
   * ở dải tiêu đề đổi nghĩa: không phải "Ẩn" nữa mà là "Ghim" — bấm để cây ở lại
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
  //  duoc-CR-783: nguồn cho mục "Chuyển sang nhóm" ở menu "…" của từng dòng dự án.
  const flatGroups = useMemo(() => flattenGroups(data), [data])
  //  duoc-CR-783: kéo dòng dự án thả lên tên nhóm / khu "Chưa thuộc nhóm" để đổi nhóm.
  const drag = useSidebarListDrag()

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
                groups={flatGroups}
                drag={drag}
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
            groups={flatGroups}
            drag={drag}
            onCreateList={onCreateList}
            onCreateGroup={onCreateGroup}
            onManageGroup={onManageGroup}
            onNavigate={onNavigate}
          />
        ))}
        {/* List không thuộc nhóm nào đứng cuối cây — vẫn hợp lệ (A-08). Có nhóm thì phải có tiêu đề riêng: thiếu nó,
            dự án lẻ chỉ thụt lệch dự án trong nhóm vài pixel và nhìn như con của nhóm cuối cùng (duoc-CR-782). */}
        {/*  Khu "Chưa thuộc nhóm" cũng là ĐÍCH THẢ (đưa dự án ra khỏi nhóm) — đang kéo một dự án trong nhóm thì luôn
             hiện khu này, kể cả khi chưa có dự án lẻ nào, không thì không có chỗ để thả. */}
        <div
          {...drag.dropProps(0, true)}
          className={cn('rounded-md', drag.over === 0 && 'bg-primary/10 ring-1 ring-primary/40')}
        >
          {groups.length > 0 && (loose.length > 0 || Boolean(drag.dragging?.group_id)) && (
            <p className="mt-3 px-2 pb-1 text-xs font-medium text-muted-foreground uppercase">Chưa thuộc nhóm</p>
          )}
          {loose.map((l) => (
            <ListLink
              key={l.id}
              item={l}
              groups={flatGroups}
              drag={drag}
              pinned={pins.isPinned(l.id)}
              onTogglePin={() => pins.toggle(l.id)}
              onNavigate={onNavigate}
            />
          ))}
          {Boolean(drag.dragging?.group_id) && loose.length === 0 && (
            <p className="px-2 py-2 text-xs text-muted-foreground">Thả vào đây để đưa dự án ra khỏi nhóm</p>
          )}
        </div>
      </div>
    </nav>
  )
}

interface GroupNodeProps {
  node: WorkGroupNode
  depth: number
  pins: ReturnType<typeof usePinnedLists>
  /** Mọi nhóm đã duỗi phẳng — cho mục "Chuyển sang nhóm" ở menu "…" của dòng dự án. */
  groups: FlatWorkGroup[]
  drag: SidebarListDrag
  onCreateList: (groupId: number | null) => void
  onCreateGroup: (parentId: number | null) => void
  onManageGroup: (group: WorkGroupNode) => void
  onNavigate?: () => void
}

function GroupNode({
  node,
  depth,
  pins,
  groups,
  drag,
  onCreateList,
  onCreateGroup,
  onManageGroup,
  onNavigate,
}: GroupNodeProps) {
  const [mo, setMo] = useState(true)
  const Icon = mo ? ChevronDown : ChevronRight
  //  Cây chỉ hai cấp (backend chặn cấp 3) — nhóm con không có mục "Thêm nhóm con".
  const canNest = depth === 0
  //  Thả dự án vào nhóm này được khi mình quản trị nhóm và nhóm chưa lưu trữ (backend đòi `CAN_MANAGE` ở nhóm đích).
  const canReceive = node.my_role !== null && node.my_role <= WORK_ROLE.ADMIN && node.is_archived !== 1

  return (
    <div>
      <div
        {...drag.dropProps(node.id, canReceive)}
        className={cn(
          'group flex items-center gap-1 rounded-md px-2 py-1.5 hover:bg-accent',
          drag.over === node.id && 'bg-primary/10 ring-1 ring-primary/40',
        )}
      >
        <button
          type="button"
          aria-expanded={mo}
          onClick={() => setMo((v) => !v)}
          className="flex min-w-0 flex-1 items-center gap-1.5 text-left text-sm font-semibold text-foreground"
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

      {/*  Con của nhóm nằm trong một khung có ĐƯỜNG GIÓNG dọc thẳng dưới mũi tên của nhóm: thụt lề bằng con số
           (`depth * 12`) như trước thì cấp nọ cấp kia chỉ lệch vài pixel, nhìn không ra dự án nào thuộc nhóm nào. */}
      {mo && (
        <div className="ml-[15px] border-l pl-1.5">
          {node.children.map((c) => (
            <GroupNode
              key={c.id}
              node={c}
              depth={depth + 1}
              pins={pins}
              groups={groups}
              drag={drag}
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
              groups={groups}
              drag={drag}
              pinned={pins.isPinned(l.id)}
              onTogglePin={() => pins.toggle(l.id)}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ListLink({
  item,
  groups,
  drag,
  pinned,
  onTogglePin,
  onNavigate,
}: {
  item: WorkList
  groups: FlatWorkGroup[]
  drag: SidebarListDrag
  pinned: boolean
  onTogglePin: () => void
  onNavigate?: () => void
}) {
  return (
    //  Nút ghim đứng NGOÀI thẻ liên kết: lồng nút trong <a> là hai điều khiển
    //  tương tác chồng nhau, trình đọc màn hình đọc sai và bấm ghim lại nhảy trang.
    <div
      {...drag.dragProps(item)}
      className={cn(
        'group/list relative',
        drag.dragProps(item).draggable && 'cursor-grab active:cursor-grabbing',
        drag.dragging?.id === item.id && 'opacity-50',
      )}
    >
      <NavLink
        to={appRoutes.project.detail(item.id)}
        onClick={onNavigate}
        //  Thẻ <a> tự kéo được (kéo ra là kéo đường dẫn) — tắt đi để cú kéo thuộc về cả DÒNG (duoc-CR-783).
        draggable={false}
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2 rounded-md py-1.5 pr-14 pl-2.5 text-sm text-foreground/85 hover:bg-accent hover:text-foreground',
            //  Dòng đang mở phải nổi hẳn: nền `accent` của theme gần như trùng nền cây, đứng xa là không thấy.
            isActive && 'bg-primary/10 font-semibold text-primary hover:bg-primary/15 hover:text-primary',
          )
        }
      >
        <span className={cn('size-2 shrink-0 rounded-full', dotClass(item.color))} />
        <span className="truncate">{item.name}</span>
      </NavLink>
      <span className="absolute top-1/2 right-1 flex -translate-y-1/2 items-center">
        {/*  duoc-CR-783: "…" → Lưu trữ dự án (chỉ chủ dự án thấy). Hiện khi rê, như nút ghim chưa ghim. */}
        <ListRowMenu item={item} groups={groups} className="opacity-0 group-hover/list:opacity-100 focus-visible:opacity-100" />
        <Button
          variant="ghost"
          size="icon"
          title={pinned ? 'Bỏ ghim' : 'Ghim lên đầu danh sách'}
          aria-label={pinned ? `Bỏ ghim ${item.name}` : `Ghim ${item.name}`}
          aria-pressed={pinned}
          onClick={onTogglePin}
          //  Đã ghim thì luôn hiện (để thấy trạng thái); chưa ghim chỉ hiện khi rê / tiêu điểm.
          className={cn(
            'size-6 focus-visible:opacity-100',
            pinned ? 'opacity-100' : 'opacity-0 group-hover/list:opacity-100',
          )}
        >
          {pinned ? <PinOff className="size-3.5" /> : <Pin className="size-3.5" />}
        </Button>
      </span>
    </div>
  )
}
