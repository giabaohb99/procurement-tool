import { Upload, X } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'

interface PurchaseOrderDeliveryFilesProps {
  /** Thiếu id = lần giao chưa lưu — phải lưu đơn trước rồi mới đính kèm được. */
  deliveryId?: number
  purchaseOrderId: number
  editable: boolean
}

/**
 * Phiếu giao / chứng từ đính kèm của MỘT lần giao (`entity = 'delivery'`).
 *
 * Tách riêng khỏi bảng lần giao vì mỗi dòng cần hook query riêng — gọi hook
 * trong vòng lặp của bảng là vi phạm rules of hooks.
 */
export function PurchaseOrderDeliveryFiles({
  deliveryId,
  purchaseOrderId,
  editable,
}: PurchaseOrderDeliveryFilesProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data: files } = usePurchaseRequestAttachments('delivery', deliveryId ?? 0)
  const upload = useUploadPurchaseRequestAttachments(
    'delivery',
    deliveryId ?? 0,
    purchaseOrderId,
  )
  const remove = useDeletePurchaseRequestAttachment('delivery', deliveryId ?? 0)

  if (!deliveryId) {
    return <span className="text-xs text-muted-foreground">Lưu đơn để đính kèm</span>
  }

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
              if (selected.length) void upload.mutateAsync({ files: selected })
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
          <a
            href={file.url}
            target="_blank"
            rel="noreferrer"
            title={file.filename}
            className="min-w-0 flex-1 truncate text-xs text-primary hover:underline"
          >
            {file.filename}
          </a>
          {editable && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-destructive"
              title="Xóa tệp"
              disabled={remove.isPending}
              onClick={() => void remove.mutateAsync(file.id)}
            >
              <X />
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}
