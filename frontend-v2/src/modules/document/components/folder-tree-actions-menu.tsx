import { useRef } from 'react'
import {
  ArchiveRestore,
  FolderInput,
  FolderPlus,
  MoreHorizontal,
  Pencil,
  Share2,
  Trash2,
} from 'lucide-react'

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
  const pendingInlineEditRef = useRef<'add-child' | 'rename' | null>(null)
  function runInlineEdit(action: 'add-child' | 'rename') {
    pendingInlineEditRef.current = action
  }
  const canContribute = data.my_level >= FOLDER_ACCESS_LEVEL.contribute
  const canManage = data.my_level >= FOLDER_ACCESS_LEVEL.manage
  const isArchived = data.status === FOLDER_STATUS.archived
  //  «Xóa» LUÔN hiện (phản hồi lead 24/09/2026) — người chỉ thấy thư mục pháp
  //  nhân trước đây không có cách nào biết tính năng này tồn tại vì mục bị
  //  GIẤU hẳn. `null` = xóa được.
  const deleteDisabledReason = folderDeleteDisabledReason(data)

  //  Không có thao tác nào dùng được thì khỏi vẽ nút — một dấu `⋯` chết không
  //  làm gì cả chỉ khiến người xem bấm thử rồi nhận một menu rỗng.
  if (!canContribute) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`Thao tác với ${data.name}`}
          title="Thao tác"
          className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
          onClick={(event) => event.stopPropagation()}
        >
          <MoreHorizontal className="size-4" />
        </button>
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
        <DropdownMenuItem onSelect={() => runInlineEdit('add-child')}>
          <FolderPlus className="size-4" />
          Thêm thư mục con
        </DropdownMenuItem>

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
