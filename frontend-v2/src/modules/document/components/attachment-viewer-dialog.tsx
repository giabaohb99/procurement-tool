import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { AttachmentViewerPane } from './attachment-viewer-pane'

interface AttachmentViewerDialogProps {
  /** `id` của FileLink — `null` là đang đóng. */
  linkId: number | null
  filename: string
  contentType?: string
  /** Số hiệu văn bản, in vào watermark để ảnh chụp lọt ra ngoài còn truy được. */
  documentCode?: string
  onClose: () => void
  /** In chìm tên người xem — mặc định BẬT; cột tệp của tab «Văn bản» tắt (xem `AttachmentViewerPane`). */
  watermark?: boolean
}

/**
 * XEM TỆP ĐÍNH KÈM NGAY TRONG TRANG, trong một HỘP THOẠI — không tải về máy.
 *
 * Chỉ còn là vỏ `Dialog` bọc `AttachmentViewerPane` (tách ra ở phase 09) —
 * logic blob/HTML/watermark nằm nguyên trong đó, đừng chép lại ở đây. Dùng ở
 * nơi xem TỪ MỘT DANH SÁCH (vd `document-attachment-list.tsx`); tab «Tệp» của
 * văn bản (nhiều tệp, có cây bên cạnh) dùng thẳng `AttachmentViewerPane` qua
 * `document-file-viewer-layout.tsx`, không qua hộp thoại này.
 */
export function AttachmentViewerDialog({
  linkId,
  filename,
  contentType,
  documentCode,
  onClose,
  watermark = true,
}: AttachmentViewerDialogProps) {
  return (
    <Dialog open={linkId !== null} onOpenChange={(open) => !open && onClose()}>
      {/*  `sm:` là bắt buộc: `DialogContent` mặc định `sm:max-w-lg`, một lớp
           `max-w-5xl` trơn KHÔNG đè được nó (khác biến thể) — hộp thoại kẹt ở
           512px, khung PDF tràn ra ngoài viền (ảnh chụp 24/09/2026). */}
      <DialogContent className="sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="truncate">{filename}</DialogTitle>
        </DialogHeader>

        {/*  `key` theo tệp: đổi tệp là DỰNG LẠI khung ruột, xem ghi chú ở
             `AttachmentViewerPane`. */}
        {linkId !== null && (
          <AttachmentViewerPane
            key={linkId}
            linkId={linkId}
            filename={filename}
            contentType={contentType}
            documentCode={documentCode}
            watermark={watermark}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
