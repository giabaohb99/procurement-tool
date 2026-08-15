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
}: DeleteConfirmButtonProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        variant="outline"
        className="text-destructive hover:text-destructive"
        onClick={() => setOpen(true)}
        disabled={pending}
      >
        {pending ? <Loader2 className="animate-spin" /> : <Trash2 />}
        Xóa
      </Button>

      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xóa "{recordName}"?</AlertDialogTitle>
            <AlertDialogDescription>
              Thao tác này không hoàn tác được.
              {warning ? ` ${warning}` : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={cn(buttonVariants({ variant: 'destructive' }))}
              onClick={() => void onConfirm()}
            >
              Xóa
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
