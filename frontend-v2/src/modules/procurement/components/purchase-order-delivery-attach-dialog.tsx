import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { useUploadPurchaseRequestAttachments } from '../hooks/use-purchase-request-support'
import { PurchaseOrderDeliveryFiles } from './purchase-order-delivery-files'

interface PurchaseOrderDeliveryAttachDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  purchaseOrderId: number
  /** Lần giao ĐÃ LƯU cần đính tệp. */
  deliveryId: number
  deliveryNo: number
  lineNumber: number
  productCode: string
  productName: string
}

/**
 * Hộp đính tệp của MỘT lần giao (ai-CR-240) — mở thẳng từ link trợ lý AI (`?delivery=<id>&attach=1` hoặc
 * `?line=<id>&delivery_no=<số>&attach=1`), để người dùng tải hóa đơn / phiếu giao mà khỏi mở chi tiết dòng rồi dò lần
 * giao trong bảng 27 cột.
 *
 * Tệp tải lên NGAY (cùng đường với nút Tải ở bảng lần giao), không cần bấm Lưu đơn. Trang chỉ mở hộp khi người xem có
 * quyền ghi đơn và dòng chưa khóa — không có quyền thì trang hiện như thường.
 */
export function PurchaseOrderDeliveryAttachDialog({
  open,
  onOpenChange,
  purchaseOrderId,
  deliveryId,
  deliveryNo,
  lineNumber,
  productCode,
  productName,
}: PurchaseOrderDeliveryAttachDialogProps) {
  const upload = useUploadPurchaseRequestAttachments('delivery', deliveryId, purchaseOrderId)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Đính tệp vào lần giao số {deliveryNo}</DialogTitle>
          <DialogDescription>
            Dòng {lineNumber} · {productCode}
            {productName ? ` · ${productName}` : ''}. Tệp tải lên ngay, không cần bấm Lưu đơn.
          </DialogDescription>
        </DialogHeader>

        <FileDropzone
          busy={upload.isPending}
          onFiles={(files) => void upload.mutateAsync({ files })}
          hint="Kéo thả tệp hóa đơn / phiếu giao vào đây hoặc bấm để chọn tệp"
        />

        <PurchaseOrderDeliveryFiles
          deliveryId={deliveryId}
          purchaseOrderId={purchaseOrderId}
          editable={false}
          pendingFiles={[]}
          onPendingFilesChange={() => undefined}
        />

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
