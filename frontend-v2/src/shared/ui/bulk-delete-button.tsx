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
import { Button, buttonVariants } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

interface BulkDeleteButtonProps {
  /** Số dòng đang chọn — 0 thì nút không dựng. */
  count: number
  /** Gọi tên thứ bị xóa, vd «dòng». */
  unitLabel: string
  /** Câu giải thích trong hộp xác nhận. */
  description?: string
  onConfirm: () => void | Promise<unknown>
  pending?: boolean
  size?: 'default' | 'sm'
  className?: string
}

/**
 * Nút «Xóa đã chọn (n)» + hộp xác nhận — bao-CR-547 (xóa nhiều dòng trên phiếu Nháp).
 *
 * `type="button"` vì cùng lý do với `DeleteConfirmButton`: đứng trong form thì mặc định `submit`
 * sẽ lưu trước khi hỏi. Hộp chỉ đóng khi việc xóa XONG — xóa lỗi thì giữ hộp, toast của
 * `httpClient` đã nói lý do.
 */
export function BulkDeleteButton({
  count,
  unitLabel,
  description = 'Thao tác này không hoàn tác được.',
  onConfirm,
  pending,
  size = 'default',
  className,
}: BulkDeleteButtonProps) {
  const [open, setOpen] = useState(false)
  if (count <= 0) return null

  async function confirm() {
    try {
      await onConfirm()
      setOpen(false)
    } catch {
      //  `httpClient` đã báo lỗi bằng toast — giữ hộp để người dùng đọc rồi tự đóng.
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="destructive"
        size={size}
        className={cn('whitespace-nowrap', className)}
        onClick={() => setOpen(true)}
      >
        <Trash2 className="size-4" />
        Xóa đã chọn ({count})
      </Button>
      <AlertDialog open={open} onOpenChange={(next) => !pending && setOpen(next)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Xóa {count} {unitLabel} đã chọn?
            </AlertDialogTitle>
            <AlertDialogDescription>{description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={pending}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={buttonVariants({ variant: 'destructive' })}
              disabled={pending}
              onClick={(event) => {
                //  Không để Radix tự đóng hộp trước khi xóa xong.
                event.preventDefault()
                void confirm()
              }}
            >
              {pending && <Loader2 className="mr-1.5 size-4 animate-spin" />}
              Xóa {count} {unitLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
