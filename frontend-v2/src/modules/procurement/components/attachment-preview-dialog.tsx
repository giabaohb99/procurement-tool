import { Download, ExternalLink, FileWarning, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import { downloadFile, fetchBlobUrl } from '@/core/api'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import type { AttachmentFile } from '../api/purchase-request-support-api'

/** Ảnh và PDF xem NHÚNG THẲNG được (khớp `INLINE_VIEW_TYPES` ở backend). */
function isInlineViewable(file: AttachmentFile): boolean {
  const type = (file.content_type || '').toLowerCase()
  if (type.startsWith('image/') || type.includes('pdf')) return true
  return /\.(png|jpe?g|gif|webp|bmp|pdf)$/i.test(file.filename)
}

function isImage(file: AttachmentFile): boolean {
  return (
    (file.content_type || '').toLowerCase().startsWith('image/') ||
    /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.filename)
  )
}

async function download(file: AttachmentFile) {
  try {
    await downloadFile(`/api/attachments/${file.id}/download`, file.filename)
  } catch {
    toast.error(`Không tải được tệp "${file.filename}".`)
  }
}

interface AttachmentPreviewDialogProps {
  file: AttachmentFile | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * XEM TRƯỚC tài liệu trên POPUP ngay tại trang — ảnh và PDF nhúng thẳng, tải qua
 * đường CÓ KIỂM QUYỀN (`/api/attachments/{id}/view`) rồi dựng `blob:` URL để nhúng
 * (không trỏ thẳng `src` vào API vì thẻ ảnh/iframe không mang được token đăng nhập).
 * Kiểu khác (Word/Excel…) không xem tại chỗ được → mời Tải về / Mở tab mới.
 */
export function AttachmentPreviewDialog({ file, open, onOpenChange }: AttachmentPreviewDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] w-full max-w-4xl flex-col gap-3">
        <DialogHeader>
          <DialogTitle className="truncate pr-6" title={file?.filename}>
            {file?.filename || 'Xem tài liệu'}
          </DialogTitle>
        </DialogHeader>
        {/*  Remount theo `file.id`: mỗi tệp một lần nạp mới, trạng thái khởi tạo sạch
            nên KHÔNG phải reset state trong effect. */}
        {file && <PreviewBody key={file.id} file={file} />}
      </DialogContent>
    </Dialog>
  )
}

function PreviewBody({ file }: { file: AttachmentFile }) {
  const viewable = isInlineViewable(file)
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  //  Dẫn xuất — không set trong effect: xem được nhưng chưa có blob và chưa lỗi.
  const loading = viewable && !blobUrl && !failed

  useEffect(() => {
    if (!viewable) return
    let cancelled = false
    let created: string | null = null
    fetchBlobUrl(`/api/attachments/${file.id}/view`)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url)
          return
        }
        created = url
        setBlobUrl(url)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
      if (created) URL.revokeObjectURL(created)
    }
  }, [file.id, viewable])

  function openNewTab() {
    //  Ưu tiên `blob:` đã kiểm quyền; chưa có thì dùng `url` kho lưu trữ; không có nữa thì tải về.
    const target = blobUrl || file.url
    if (target) window.open(target, '_blank', 'noopener')
    else void download(file)
  }

  return (
    <>
      <div className="flex min-h-[60vh] flex-1 items-center justify-center overflow-auto rounded-lg border bg-muted/30">
        {!viewable ? (
          <div className="flex flex-col items-center gap-2 p-8 text-center text-sm text-muted-foreground">
            <FileWarning className="size-8 text-muted-foreground" />
            Kiểu tệp này không xem trước tại chỗ được. Hãy tải về hoặc mở ở tab mới.
          </div>
        ) : loading ? (
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        ) : failed ? (
          <div className="flex flex-col items-center gap-2 p-8 text-center text-sm text-destructive">
            <FileWarning className="size-8" />
            Không tải được nội dung để xem trước.
          </div>
        ) : blobUrl && isImage(file) ? (
          <img src={blobUrl} alt={file.filename} className="max-h-[76vh] w-auto object-contain" />
        ) : blobUrl ? (
          <iframe src={blobUrl} title={file.filename} className="h-[76vh] w-full" />
        ) : null}
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button variant="outline" onClick={openNewTab}>
          <ExternalLink className="size-4" />
          Mở tab mới
        </Button>
        <Button variant="outline" onClick={() => void download(file)}>
          <Download className="size-4" />
          Tải về
        </Button>
      </div>
    </>
  )
}
