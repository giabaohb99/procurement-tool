import {
  Eye,
  FolderInput,
  FolderOpen,
  MoreHorizontal,
  MoreVertical,
  PenLine,
  Share2,
  Trash2,
} from 'lucide-react'
import type { ReactNode } from 'react'

import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from '@/shared/ui/context-menu'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import {
  buildFolderItemMenuActions,
  FOLDER_ITEM_MENU_ACTION,
  type FolderItemMenuInput,
} from '../helpers/folder-item-menu-actions'

interface FolderItemContextMenuProps extends FolderItemMenuInput {
  children: ReactNode
  onOpen: () => void
  onRename?: () => void
  onMoveTo?: () => void
  onManagePermissions?: () => void
  onViewDetails: () => void
  onRemove?: () => void
  /**
   * Thêm nút «⋯» LUÔN THẤY (không cần chuột phải) — thẻ pill của thư mục con
   * kiểu Drive (đặc tả §P5, chốt UI 23/09/2026: "icon + tên + ⋯"). Bỏ trống =
   * chỉ có menu chuột phải như trước (thẻ Lưới của văn bản).
   */
  showMenuButton?: boolean
  /**
   * Vị trí nút «⋯» khi `showMenuButton` — `'center'` (mặc định) canh giữa
   * chiều cao, đúng cho DÒNG THẤP (pill/list); `'corner'` ghim GÓC TRÊN PHẢI,
   * đúng cho THẺ CAO (thẻ Lưới văn bản, `folder-grid-document-card.tsx`) —
   * canh giữa trên một khối cao ~130px thả nút vào giữa vùng xem trước, không
   * phải góc như Drive thật.
   */
  menuButtonPlacement?: 'center' | 'corner'
  /**
   * Nút menu LUÔN hiện (icon «⋮» dọc, kiểu thẻ thư mục Google Drive) thay vì
   * chỉ hiện khi rê chuột — thẻ thư mục con (`folder-child-cards.tsx`).
   */
  menuButtonAlwaysVisible?: boolean
  /**
   * Vì sao mục «Xóa» bị KHÓA — chỉ có nghĩa khi `kind = 'folder'` (phản hồi
   * lead 24/09/2026: «Xóa» của thư mục nay LUÔN hiện, xem
   * `folder-delete-disabled-reason.ts`). `null`/bỏ trống = xóa được bình
   * thường. Văn bản không dùng prop này — mục «Xóa» của văn bản vẫn ẨN hẳn
   * khi thiếu `canDeleteDocument` (không đổi).
   */
  removeDisabledReason?: string | null
}

const LABELS: Record<string, string> = {
  [FOLDER_ITEM_MENU_ACTION.open]: 'Mở',
  [FOLDER_ITEM_MENU_ACTION.rename]: 'Đổi tên',
  [FOLDER_ITEM_MENU_ACTION.moveTo]: 'Chuyển tới…',
  [FOLDER_ITEM_MENU_ACTION.managePermissions]: 'Chia sẻ…',
  [FOLDER_ITEM_MENU_ACTION.viewDetails]: 'Xem chi tiết',
  [FOLDER_ITEM_MENU_ACTION.remove]: 'Xóa',
}

const ICONS: Record<string, typeof Eye> = {
  [FOLDER_ITEM_MENU_ACTION.open]: FolderOpen,
  [FOLDER_ITEM_MENU_ACTION.rename]: PenLine,
  [FOLDER_ITEM_MENU_ACTION.moveTo]: FolderInput,
  [FOLDER_ITEM_MENU_ACTION.managePermissions]: Share2,
  [FOLDER_ITEM_MENU_ACTION.viewDetails]: Eye,
  [FOLDER_ITEM_MENU_ACTION.remove]: Trash2,
}

/**
 * MENU trên một dòng (thư mục hoặc văn bản) — đặc tả §B. Bọc quanh
 * thẻ/dòng đang có (`children`), chỉ THÊM sự kiện chuột phải (+ nút «⋯» tùy
 * chọn), không đổi hành vi bấm trái của nội dung bên trong.
 *
 * Danh sách mục hiện ra do {@link buildFolderItemMenuActions} quyết định (hàm
 * THUẦN, có test riêng) — tệp này chỉ lo phần DỰNG GIAO DIỆN + nối handler,
 * dùng CHUNG một danh sách cho cả `ContextMenu` (chuột phải) lẫn `DropdownMenu`
 * (nút «⋯», khi `showMenuButton`).
 */
export function FolderItemContextMenu({
  children,
  onOpen,
  onRename,
  onMoveTo,
  onManagePermissions,
  onViewDetails,
  onRemove,
  showMenuButton = false,
  menuButtonPlacement = 'center',
  menuButtonAlwaysVisible = false,
  removeDisabledReason,
  ...menuInput
}: FolderItemContextMenuProps) {
  const actions = buildFolderItemMenuActions(menuInput)
  const handlers: Partial<Record<string, () => void>> = {
    [FOLDER_ITEM_MENU_ACTION.open]: onOpen,
    [FOLDER_ITEM_MENU_ACTION.rename]: onRename,
    [FOLDER_ITEM_MENU_ACTION.moveTo]: onMoveTo,
    [FOLDER_ITEM_MENU_ACTION.managePermissions]: onManagePermissions,
    [FOLDER_ITEM_MENU_ACTION.viewDetails]: onViewDetails,
    [FOLDER_ITEM_MENU_ACTION.remove]: onRemove,
  }
  const items = actions.map((action) => ({
    action,
    Icon: ICONS[action],
    handler: handlers[action],
    //  Chỉ «Xóa» có lý do khóa RIÊNG (thư mục pháp nhân / thiếu quyền Quản lý)
    //  — mọi mục khác disable đơn thuần vì thiếu handler.
    disabledReason: action === FOLDER_ITEM_MENU_ACTION.remove ? removeDisabledReason : null,
  }))

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div className={cn('relative', showMenuButton && 'group/pill')}>
          {children}
          {showMenuButton && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  aria-label="Thêm tùy chọn"
                  onClick={(event) => event.stopPropagation()}
                  className={cn(
                    'absolute right-1.5 flex size-6 items-center justify-center rounded opacity-0 transition-opacity group-hover/pill:opacity-100 hover:bg-muted focus-visible:opacity-100 data-[state=open]:opacity-100',
                    menuButtonPlacement === 'corner' ? 'top-1.5' : 'top-1/2 -translate-y-1/2',
                    menuButtonAlwaysVisible && 'opacity-100 hover:bg-background/70',
                  )}
                >
                  {menuButtonAlwaysVisible ? (
                    <MoreVertical className="size-4" />
                  ) : (
                    <MoreHorizontal className="size-4" />
                  )}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {items.map(({ action, Icon, handler, disabledReason }) => (
                  <DropdownMenuItem
                    key={action}
                    variant={action === FOLDER_ITEM_MENU_ACTION.remove ? 'destructive' : 'default'}
                    disabled={!handler || Boolean(disabledReason)}
                    onSelect={handler}
                  >
                    <Icon className="size-4 shrink-0" />
                    <MenuItemLabel label={LABELS[action]} disabledReason={disabledReason} />
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </ContextMenuTrigger>
      <ContextMenuContent className="w-56">
        {items.map(({ action, Icon, handler, disabledReason }) => (
          <ContextMenuItem
            key={action}
            variant={action === FOLDER_ITEM_MENU_ACTION.remove ? 'destructive' : 'default'}
            disabled={!handler || Boolean(disabledReason)}
            onSelect={handler}
          >
            <Icon className="size-4 shrink-0" />
            <MenuItemLabel label={LABELS[action]} disabledReason={disabledReason} />
          </ContextMenuItem>
        ))}
      </ContextMenuContent>
    </ContextMenu>
  )
}

/** Nhãn một mục menu — kèm dòng chữ mờ nhỏ giải thích lý do KHÓA (chỉ «Xóa» dùng, xem `removeDisabledReason`). */
function MenuItemLabel({
  label,
  disabledReason,
}: {
  label: string
  disabledReason?: string | null
}) {
  if (!disabledReason) return <>{label}</>
  return (
    <span className="flex min-w-0 flex-col">
      <span>{label}</span>
      <span className="text-xs font-normal text-muted-foreground">{disabledReason}</span>
    </span>
  )
}
