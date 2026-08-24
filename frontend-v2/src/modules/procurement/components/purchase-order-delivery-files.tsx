import { Upload, X } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'

const IMAGE_PATTERN = /\.(jpe?g|png|webp|gif)$/i

interface PurchaseOrderDeliveryFilesProps {
  /** Thiếu id = lần giao chưa lưu — tệp giữ tạm ở trang, lưu đơn xong mới tải lên. */
  deliveryId?: number
  purchaseOrderId: number
  editable: boolean
  /** Tệp đã chọn nhưng chưa có chỗ để gắn (lần giao chưa lưu). */
  pendingFiles: File[]
  onPendingFilesChange: (files: File[]) => void
}

/**
 * Phiếu giao / chứng từ đính kèm của MỘT lần giao (`entity = 'delivery'`).
 *
 * Tách riêng khỏi bảng lần giao vì mỗi dòng cần hook query riêng — gọi hook
 * trong vòng lặp của bảng là vi phạm rules of hooks.
 *
 * Lần giao vừa thêm chưa có id nên chưa gắn tệp vào đâu được: tệp được giữ tạm
 * trong bộ nhớ và tải lên ngay sau khi bấm "Lưu đơn" (trang lo việc đó). Không
 * làm vậy thì người nhập phải lưu đơn trước rồi mới quay lại đính từng phiếu.
 */
export function PurchaseOrderDeliveryFiles({
  deliveryId,
  purchaseOrderId,
  editable,
  pendingFiles,
  onPendingFilesChange,
}: PurchaseOrderDeliveryFilesProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data: files } = usePurchaseRequestAttachments('delivery', deliveryId ?? 0)
  const upload = useUploadPurchaseRequestAttachments(
    'delivery',
    deliveryId ?? 0,
    purchaseOrderId,
  )
  const remove = useDeletePurchaseRequestAttachment('delivery', deliveryId ?? 0)

  const isImageFile = (f: { content_type: string; filename: string }) =>
    f.content_type.startsWith('image/') || IMAGE_PATTERN.test(f.filename)
  const imageFiles = (files ?? []).filter(isImageFile)
  const lightbox = useImageLightbox()

  return (
    <div className="space-y-1">
      {editable && (
        <>
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(event) => {
              const selected = Array.from(event.target.files ?? [])
              if (selected.length) {
                if (deliveryId) void upload.mutateAsync({ files: selected })
                else onPendingFilesChange([...pendingFiles, ...selected])
              }
              event.target.value = ''
            }}
          />
          <Button
            variant="outline"
            size="sm"
            disabled={upload.isPending}
            onClick={() => inputRef.current?.click()}
          >
            <Upload />
            {upload.isPending ? 'Đang tải' : 'Tải tệp'}
          </Button>
        </>
      )}

      {(files ?? []).map((file) => (
        <div key={file.id} className="flex items-center gap-1">
          {isImageFile(file) ? (
            <button
              type="button"
              title={file.filename}
              onClick={() => lightbox.openAt(imageFiles.indexOf(file))}
              className="min-w-0 flex-1 truncate text-left text-xs text-primary hover:underline"
            >
              {file.filename}
            </button>
          ) : (
            <a
              href={file.url}
              target="_blank"
              rel="noreferrer"
              title={file.filename}
              className="min-w-0 flex-1 truncate text-xs text-primary hover:underline"
            >
              {file.filename}
            </a>
          )}
          {editable && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-destructive hover:text-destructive"
              title="Xóa tệp"
              disabled={remove.isPending}
              onClick={() => void remove.mutateAsync(file.id)}
            >
              <X />
            </Button>
          )}
        </div>
      ))}

      {pendingFiles.map((file, index) => (
        <div key={`${file.name}-${index}`} className="flex items-center gap-1">
          <span
            title={file.name}
            className="min-w-0 flex-1 truncate text-xs italic text-muted-foreground"
          >
            {file.name}
          </span>
          {editable && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-destructive hover:text-destructive"
              title="Bỏ tệp này"
              onClick={() =>
                onPendingFilesChange(pendingFiles.filter((_, current) => current !== index))
              }
            >
              <X />
            </Button>
          )}
        </div>
      ))}

      {!deliveryId && pendingFiles.length > 0 && (
        <p className="text-xs text-muted-foreground">Tệp sẽ được tải lên khi bấm Lưu đơn.</p>
      )}

      {imageFiles.length > 0 && (
        <ImageLightbox
          images={imageFiles.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}
    </div>
  )
}
