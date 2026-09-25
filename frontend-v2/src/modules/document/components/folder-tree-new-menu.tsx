import { FilePlus, FileUp, FolderPlus, Plus } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { FolderQuickDocumentDialog } from './folder-quick-document-dialog'

interface FolderTreeNewMenuProps {
  /** Thư mục ĐANG CHỌN ở khung phải — `null` = đang ở GỐC: chỉ «Thư mục mới» (thư mục tự do) còn dùng được, hai mục văn bản cần một thư mục đích. */
  folderId: number | null
  /** Pháp nhân + tên của thư mục đang chọn — hộp «Tạo nhanh từ tệp» mở sẵn pháp nhân này. */
  folderCompanyId?: number
  folderName?: string
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
  folderCompanyId = 0,
  folderName,
  canCreateFolder,
  canCreateDocument,
  onCreateFolder,
}: FolderTreeNewMenuProps) {
  const navigate = useNavigate()
  //  Việc chờ chạy SAU khi menu đóng hẳn — xem `onCloseAutoFocus` bên dưới.
  const pendingActionRef = useRef<'folder' | 'quick-document' | null>(null)
  const [quickOpen, setQuickOpen] = useState(false)
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
          //  Hộp «Tạo nhanh từ tệp» cũng vậy: mở lúc menu còn giữ focus thì hộp
          //  thoại bị giành focus ngược.
          const action = pendingActionRef.current
          if (!action) return
          event.preventDefault()
          pendingActionRef.current = null
          if (action === 'folder') onCreateFolder()
          else setQuickOpen(true)
        }}
      >
        {canCreateFolder && (
          <DropdownMenuItem
            onSelect={() => {
              pendingActionRef.current = 'folder'
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
            {/*  Trước 25/09/2026 mục này chỉ mở lại trang tạo 3 bước — trùng hẳn
                 «Văn bản mới tại đây». Nay là hộp rút gọn: tải tệp, năm ô bắt
                 buộc, phân quyền, tạo luôn (không soạn thảo). */}
            <DropdownMenuItem
              onSelect={() => {
                pendingActionRef.current = 'quick-document'
              }}
            >
              <FileUp className="size-4" />
              Tạo nhanh từ tệp
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
      {/*  Chỉ dựng khi mở: mỗi lần mở là form mới, mang đúng thư mục lúc đó. */}
      {quickOpen && folderId != null && (
        <FolderQuickDocumentDialog
          open
          onOpenChange={setQuickOpen}
          folderId={folderId}
          folderCompanyId={folderCompanyId}
          folderName={folderName}
        />
      )}
    </DropdownMenu>
  )
}
