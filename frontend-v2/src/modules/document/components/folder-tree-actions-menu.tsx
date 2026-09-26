import { useRef, useState, type ComponentProps } from 'react'
import {
  ArchiveRestore,
  FolderInput,
  FolderPlus,
  MoreHorizontal,
  Pencil,
  Share2,
  Trash2,
} from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { folderDeleteDisabledReason } from '../helpers/folder-delete-disabled-reason'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

export type FolderNodeAction =
  'add-child' | 'rename' | 'move' | 'access' | 'archive' | 'restore' | 'delete'

interface FolderTreeActionsMenuProps {
  data: DocFolderTreeNode
  onAction: (action: FolderNodeAction) => void
}

/**
 * Menu `⋯` theo ĐÚNG `my_level` của node — thư mục PHÁP NHÂN chỉ có "Thêm
 * thư mục con" + "Chia sẻ…" (mở hộp «Chia sẻ» kiểu Drive ở khung phải, xem
 * `?tab=access`), còn lại rẽ theo ba mức (Xem · Đóng góp · Quản lý) như bảng
 * ở `phase-04-phan-quyen-thu-muc.md`.
 *
 * Giao diện CHỈ đọc `my_level` để ẩn/hiện — không tự suy luận quyền, backend
 * chặn thật (xem ghi chú đầu `document-folder.ts`). Tách khỏi `folder-tree-item.tsx`
 * để tệp đó giữ dưới 200 dòng (đây là phần JSX lớn nhất trong đó).
 */
export function FolderTreeActionsMenu({ data, onAction }: FolderTreeActionsMenuProps) {
  //  Dựng LƯỜI (26/09/2026): chưa bấm thì chỉ vẽ một nút trơn, bấm lần đầu
  //  mới dựng DropdownMenu của Radix (+ `usePermission`) và mở sẵn. Mỗi dòng
  //  cây một bộ menu dựng trước là phần đắt nhất khi cây bung ra cả trăm dòng
  //  (gõ tìm trong cây sâu 100 cấp) — trong khi mỗi lần chỉ mở MỘT menu.
  const [activated, setActivated] = useState(false)
  //  Không có thao tác nào dùng được thì khỏi vẽ nút — một dấu `⋯` chết không
  //  làm gì cả chỉ khiến người xem bấm thử rồi nhận một menu rỗng.
  if (data.my_level < FOLDER_ACCESS_LEVEL.contribute) return null
  if (activated) return <FolderTreeActionsDropdown data={data} onAction={onAction} />
  return (
    <FolderTreeActionsButton
      label={data.name}
      onClick={() => setActivated(true)}
    />
  )
}

/**
 * Nút `⋯`. Nhận và CHUYỂN TIẾP mọi prop (`ref`, `onPointerDown`, `aria-expanded`,
 * `data-state`…) — `DropdownMenuTrigger asChild` gắn chúng vào đây; nuốt mất
 * là menu không mở được bằng chuột lẫn bàn phím.
 */
function FolderTreeActionsButton({
  label,
  onClick,
  ...rest
}: ComponentProps<'button'> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={`Thao tác với ${label}`}
      title="Thao tác"
      className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
      {...rest}
      onClick={(event) => {
        event.stopPropagation()
        onClick?.(event)
      }}
    >
      <MoreHorizontal className="size-4" />
    </button>
  )
}

function FolderTreeActionsDropdown({ data, onAction }: FolderTreeActionsMenuProps) {
  const pendingInlineEditRef = useRef<'add-child' | 'rename' | null>(null)
  function runInlineEdit(action: 'add-child' | 'rename') {
    pendingInlineEditRef.current = action
  }
  const { can } = usePermission()
  const canContribute = data.my_level >= FOLDER_ACCESS_LEVEL.contribute
  //  Mức Đóng góp có thể đến từ quyền GHI văn bản (`role_level_cap` ở backend)
  //  — tạo thư mục con thì vai trò còn phải có `doc_folder.create`.
  const canAddChild = can('doc_folder', 'create')
  const canManage = data.my_level >= FOLDER_ACCESS_LEVEL.manage
  const isArchived = data.status === FOLDER_STATUS.archived
  //  «Xóa» LUÔN hiện (phản hồi lead 24/09/2026) — người chỉ thấy thư mục pháp
  //  nhân trước đây không có cách nào biết tính năng này tồn tại vì mục bị
  //  GIẤU hẳn. `null` = xóa được.
  const deleteDisabledReason = folderDeleteDisabledReason(data)

  if (!canContribute) return null

  return (
    //  `defaultOpen`: component này chỉ được dựng NGAY SAU cú bấm đầu tiên
    //  vào nút trơn ở `FolderTreeActionsMenu` — cú bấm đó phải mở menu luôn.
    <DropdownMenu defaultOpen>
      <DropdownMenuTrigger asChild>
        <FolderTreeActionsButton label={data.name} />
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        onClick={(event) => event.stopPropagation()}
        onCloseAutoFocus={(event) => {
          //  «Thêm thư mục con» / «Đổi tên» mở Ô NHẬP TẠI CHỖ trên cây — chạy
          //  SAU KHI menu đóng hẳn (menu modal giữ focus, dựng ô lúc menu còn
          //  mở thì gõ không vào, lỗi báo 24/09/2026), và không trả focus về «⋯».
          const pending = pendingInlineEditRef.current
          if (!pending) return
          event.preventDefault()
          pendingInlineEditRef.current = null
          onAction(pending)
        }}
      >
        {canAddChild && (
          <DropdownMenuItem onSelect={() => runInlineEdit('add-child')}>
            <FolderPlus className="size-4" />
            Thêm thư mục con
          </DropdownMenuItem>
        )}

        {canManage && (
          <>
            <DropdownMenuItem onSelect={() => runInlineEdit('rename')}>
              <Pencil className="size-4" />
              Đổi tên tại chỗ
            </DropdownMenuItem>
            {data.kind !== FOLDER_KIND.companyGroup && (
              <DropdownMenuItem onSelect={() => onAction('move')}>
                <FolderInput className="size-4" />
                Chuyển tới…
              </DropdownMenuItem>
            )}
          </>
        )}

        {canManage && (
          <DropdownMenuItem onSelect={() => onAction('access')}>
            <Share2 className="size-4" />
            Chia sẻ…
          </DropdownMenuItem>
        )}

        {/*  Ngừng dùng/Khôi phục nay ÁP DỤNG CẢ thư mục pháp nhân (đính chính
             lead 24/09/2026 tối — backend đã mở khóa) — CHỈ còn cần `canManage`,
             khác Đổi tên/Chuyển tới ở trên vẫn CHẶN company root (đổi tên/dời
             pháp nhân không có ý nghĩa, hai việc đó không liên quan tới việc
             ngừng dùng/xóa). */}
        <DropdownMenuSeparator />
        {canManage &&
          (isArchived ? (
            <DropdownMenuItem onSelect={() => onAction('restore')}>
              <ArchiveRestore className="size-4" />
              Khôi phục
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onSelect={() => onAction('archive')}>
              <ArchiveRestore className="size-4 rotate-180" />
              Ngừng dùng
            </DropdownMenuItem>
          ))}
        <DropdownMenuItem
          variant="destructive"
          disabled={Boolean(deleteDisabledReason)}
          onSelect={() => onAction('delete')}
        >
          <Trash2 className="size-4 shrink-0" />
          {deleteDisabledReason ? (
            <span className="flex min-w-0 flex-col">
              <span>Xóa</span>
              <span className="text-xs font-normal text-muted-foreground">
                {deleteDisabledReason}
              </span>
            </span>
          ) : (
            'Xóa'
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
