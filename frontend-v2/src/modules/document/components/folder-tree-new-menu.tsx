import { FilePlus, FileUp, FolderPlus, Plus } from 'lucide-react'
import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'

interface FolderTreeNewMenuProps {
  /** Thư mục ĐANG CHỌN ở khung phải — `null` = đang ở GỐC: chỉ «Thư mục mới» (thư mục tự do) còn dùng được, hai mục văn bản cần một thư mục đích. */
  folderId: number | null
  /** Tạo được thư mục ở chỗ đang đứng — trong thư mục: đủ mức trên `folderId`; ở gốc: có `doc_folder.create`. */
  canCreateFolder: boolean
  /** Vai trò có `document.create` — thiếu thì ẩn hai mục «Văn bản …». */
  canCreateDocument: boolean
  onCreateFolder: () => void
}

/**
 * Nút «+ Mới» to, kiểu Drive — nằm TRÊN CÙNG khung trái (đặc tả §P3, chốt UI
 * 23/09/2026: dời khỏi thanh công cụ khung phải xuống đây để khỏi tranh chỗ
 * với «Chia sẻ»/chuyển Lưới-Danh sách). Tác dụng lên đúng thư mục ĐANG XEM ở
 * khung phải (`folderId`) — giống Drive mở «+ Mới» ngay tại thư mục đang đứng,
 * không phải một hộp chọn cha riêng.
 *
 * «Thư mục mới» dùng LẠI đúng dòng nhập tạm tại chỗ (`onCreateFolder` =
 * `beginCreate` của `folder-tree-panel.tsx`) — không mở hộp thoại, cùng cơ chế
 * với nút icon nhỏ ở `folder-tree-panel-header.tsx` (giữ cả hai: nút to này
 * cho thao tác đầu tiên khi mới vào trang, nút icon nhỏ tiện tay khi đang rê
 * chuột ngay trên một dòng cây).
 */
export function FolderTreeNewMenu({
  folderId,
  canCreateFolder,
  canCreateDocument,
  onCreateFolder,
}: FolderTreeNewMenuProps) {
  const navigate = useNavigate()
  const pendingCreateRef = useRef(false)
  //  Tạo văn bản cần một thư mục đích (không tạo ở gốc).
  const canCreateDocumentHere = canCreateDocument && folderId != null

  function goCreateDocument() {
    if (folderId != null) navigate(`${appRoutes.document.documentNew}?folder_id=${folderId}`)
  }

  //  Người CHỈ XEM không thấy nút nào để bấm (lỗi lead bắt khi test UI
  //  24/09/2026: nút «+ Mới» hiện cho cả người không tạo được gì).
  if (!canCreateFolder && !canCreateDocumentHere) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
        >
          <Plus className="size-4" />
          Mới
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        className="w-56"
        onCloseAutoFocus={(event) => {
          //  «Thư mục mới» mở Ô NHẬP TẠI CHỖ trên cây. Menu Radix là modal, giữ
          //  focus bên trong nó: dựng ô nhập lúc menu CÒN MỞ thì `autoFocus`
          //  bị kéo ngược, đóng menu xong focus lại về nút «Mới» — gõ không vào
          //  đâu cả (lỗi báo 24/09/2026). Nên chỉ dựng ô SAU KHI menu đã đóng
          //  hẳn, và không trả focus về nút.
          if (!pendingCreateRef.current) return
          event.preventDefault()
          pendingCreateRef.current = false
          onCreateFolder()
        }}
      >
        {canCreateFolder && (
          <DropdownMenuItem
            onSelect={() => {
              pendingCreateRef.current = true
            }}
          >
            <FolderPlus className="size-4" />
            Thư mục mới
          </DropdownMenuItem>
        )}
        {canCreateDocumentHere && (
          <>
            <DropdownMenuItem onSelect={goCreateDocument}>
              <FilePlus className="size-4" />
              Văn bản mới tại đây
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={goCreateDocument}>
              <FileUp className="size-4" />
              Văn bản từ tệp có sẵn
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
