import { AlertTriangle, Download, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { extractErrorMessage, fetchBlobUrl } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import type { ChainAttachment } from '../types/document-chain'
import { isChainImage } from '../utils/group-document-chain'

interface ChainFilePreviewDialogProps {
  /** Tệp đang mở — `null` là đóng. */
  file: ChainAttachment | null
  onClose: () => void
  onDownload: (file: ChainAttachment) => void
}

/**
 * Xem nhanh một tệp trong chuỗi chứng từ, ngay trong trang.
 *
 * Nội dung lấy qua `GET /api/attachments/{id}/view` — đường CÓ kiểm quyền, chứ
 * không phải `url` đọc thẳng kho lưu trữ như bản v1 (`frontend/src/pages/
 * Documents.tsx` gán `url` vào `<img>`/`<iframe>`). Khác biệt thật chứ không
 * phải cho đẹp: backend để `url` RỖNG với entity riêng tư, và đường đọc thẳng
 * kho không chặn được người vừa bị thu hồi quyền.
 */
export function ChainFilePreviewDialog({
  file,
  onClose,
  onDownload,
}: ChainFilePreviewDialogProps) {
  return (
    <Dialog open={file !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle className="truncate pr-8">{file?.filename ?? ''}</DialogTitle>
        </DialogHeader>

        {/* `key` theo tệp: đổi tệp là dựng lại khung ruột với state trống, khỏi
            phải dọn state trong effect (và khỏi thấy tệp cũ nhấp nháy một nhịp). */}
        {file && (
          <>
            <PreviewBody key={file.link_id} file={file} />
            <div className="flex justify-end">
              <Button type="button" variant="outline" size="sm" onClick={() => onDownload(file)}>
                <Download />
                Tải tệp này
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

function PreviewBody({ file }: { file: ChainAttachment }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    let createdUrl = ''

    fetchBlobUrl(`/api/attachments/${file.link_id}/view`)
      .then((url) => {
        createdUrl = url
        // Đóng khung trước khi tải xong thì thu hồi ngay, đừng gán vào state của
        // component sắp biến mất.
        if (cancelled) URL.revokeObjectURL(url)
        else setBlobUrl(url)
      })
      .catch((requestError) => !cancelled && setError(extractErrorMessage(requestError)))

    return () => {
      cancelled = true
      // Không thu hồi thì blob nằm lại trong bộ nhớ tới khi đóng tab.
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [file.link_id])

  return (
    <div className="max-h-[70vh] min-h-64 overflow-auto rounded-md border bg-muted/30">
      {error && (
        <p
          role="alert"
          className="flex items-start gap-2 px-3 py-4 text-sm text-amber-900 dark:text-amber-300"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          {error}
        </p>
      )}

      {!blobUrl && !error && (
        <div className="flex h-64 items-center justify-center text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      )}

      {blobUrl &&
        (isChainImage(file) ? (
          <img src={blobUrl} alt={file.filename} className="mx-auto block max-w-full" />
        ) : (
          // `<iframe>` chứ không `<embed>`: trình xem PDF của trình duyệt chạy
          // trong khung riêng, và backend đã gắn `Content-Security-Policy: sandbox`.
          <iframe src={blobUrl} title={file.filename} className="h-[70vh] w-full" />
        ))}
    </div>
  )
}
