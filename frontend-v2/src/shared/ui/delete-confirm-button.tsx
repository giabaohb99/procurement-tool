import { Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'
import { buttonVariants } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

interface DeleteConfirmButtonProps {
  /** Tên bản ghi, hiện trong câu hỏi xác nhận. */
  recordName: string
  onConfirm: () => Promise<unknown>
  pending?: boolean
  /** Câu cảnh báo thêm (vd "Tài khoản đăng nhập kèm theo sẽ bị khóa"). */
  warning?: string
  /** Ghép cuối vào nút mở hộp (vd tông `ACTION_TONE_CLASS.danger` cho viền đỏ như v1). */
  className?: string
  /** Chữ trên nút mở hộp — mặc định "Xóa". Thu mua truyền "Xóa phiếu" / "Xóa đơn" như v1 (duoc-CR-741). */
  label?: string
  /** Câu hỏi trong hộp — mặc định `Xóa "<tên bản ghi>"?`. */
  title?: string
  /** Chữ nút đồng ý — mặc định "Xóa". */
  confirmLabel?: string
  /** Thay CẢ đoạn giải thích (bỏ câu "không hoàn tác được" + `warning`) — để chép đúng câu của v1. */
  description?: string
}

/**
 * Nút Xóa kèm hộp xác nhận. Xóa danh mục là thao tác không hoàn tác được và
 * dữ liệu cũ có thể đang tham chiếu tới nó, nên không bao giờ xóa thẳng.
 */
export function DeleteConfirmButton({
  recordName,
  onConfirm,
  pending,
  warning,
  className,
  label = 'Xóa',
  title,
  confirmLabel = 'Xóa',
  description,
}: DeleteConfirmButtonProps) {
  const [open, setOpen] = useState(false)
  //  Tên bản ghi có thể rất dài (vd mục đích phiếu là cả đoạn văn) → cắt gọn + "…" để
  //  tiêu đề hộp xác nhận không phình ra khỏi khung.
  const shortName = recordName.length > 80 ? `${recordName.slice(0, 80).trimEnd()}…` : recordName

  return (
    <>
      {/*  ⚠️ `type="button"` là BẮT BUỘC, không phải cho đẹp.

           Nút này đứng trong `<form>` ở gần hết màn chi tiết (hồ sơ nhân sự,
           công ty, phòng ban, YCMH, YCBG, ĐMH, YCTT…). Thiếu `type` thì HTML
           mặc định là `submit`: bấm "Xóa" là form **LƯU bản ghi** trước, rồi
           hộp xác nhận mới mở ra. Người dùng đổi ý bấm Hủy — nhưng bản ghi đã
           bị lưu rồi, và dòng "Cập nhật" trong lịch sử thao tác là của một
           thao tác không ai thực hiện.

           Dựng lại được trên trình duyệt thật 08/09/2026. Lỗi có từ lâu, im
           lặng vì hai việc (lưu và mở hộp thoại) đều "thành công". */}
      <Button
        type="button"
        variant="outline"
        className={cn('text-destructive hover:text-destructive', className)}
        onClick={() => setOpen(true)}
        disabled={pending}
      >
        {pending ? <Loader2 className="animate-spin" /> : <Trash2 />}
        {label}
      </Button>

      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="break-words">{title ?? `Xóa "${shortName}"?`}</AlertDialogTitle>
            <AlertDialogDescription className="whitespace-pre-line">
              {description ?? `Thao tác này không hoàn tác được.${warning ? ` ${warning}` : ''}`}
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={cn(buttonVariants({ variant: 'destructive' }))}
              onClick={() => void onConfirm()}
            >
              {confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
