import { FileUp } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'
import { FolderQuickDocumentDialog } from './folder-quick-document-dialog'

interface FolderQuickDocumentButtonProps {
  folderId: number
  folderCompanyId: number
  /** Mức quyền của người xem trên thư mục — dưới Đóng góp thì không thêm được văn bản vào đây. */
  folderMyLevel: number
}

/**
 * Nút «Tải tệp lên» HIỆN SẴN ở thanh công cụ khung phải — cùng hộp «Tạo nhanh
 * từ tệp» với mục trong menu «+ Mới». Thêm vì chỉ để trong menu thì người
 * dùng không thấy (phản hồi 25/09/2026). Thiếu `document.create` thì ẩn hẳn.
 */
export function FolderQuickDocumentButton({
  folderId,
  folderCompanyId,
  folderMyLevel,
}: FolderQuickDocumentButtonProps) {
  const { can } = usePermission()
  const [open, setOpen] = useState(false)
  //  Thư mục chỉ ở mức Xem (vd hiện ra vì được chia một văn bản trong đó) thì
  //  máy chủ sẽ từ chối thêm văn bản — ẩn nút thay vì để bấm rồi ăn lỗi.
  if (!can('document', 'create') || folderMyLevel < FOLDER_ACCESS_LEVEL.contribute) return null

  return (
    <>
      <Button type="button" size="sm" onClick={() => setOpen(true)}>
        <FileUp className="size-4" />
        <span className="hidden sm:inline">Tải tệp lên</span>
      </Button>
      {/*  Chỉ dựng khi mở: mỗi lần mở là form mới, mang đúng thư mục lúc đó. */}
      {open && (
        <FolderQuickDocumentDialog
          open
          onOpenChange={setOpen}
          folderId={folderId}
          folderCompanyId={folderCompanyId}
        />
      )}
    </>
  )
}
