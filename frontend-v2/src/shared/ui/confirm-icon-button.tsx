import type { LucideIcon } from 'lucide-react'
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

interface ConfirmIconButtonProps {
  icon: LucideIcon
  /** Tooltip của nút. */
  title: string
  /**
   * Hiện CHỮ cạnh biểu tượng. Bỏ trống = nút chỉ có biểu tượng như cũ.
   *
   * Có để dùng lại nút này trong một DANH SÁCH DỌC (tấm `⋯` ở đầu trang chi
   * tiết): nằm trong hàng ngang thì mấy biểu tượng đọc theo cụm, còn xếp dọc thì
   * mỗi dòng đứng một mình và một cột biểu tượng không chữ là bắt đoán từng cái.
   * Vẫn giữ nguyên hộp xác nhận, nên không phải đổi sang `DeleteConfirmButton`
   * (bản đó tự dựng câu hỏi từ tên bản ghi, không nhận câu riêng của màn).
   */
  label?: string
  confirmTitle: string
  confirmDescription?: string
  confirmLabel?: string
  /** Thao tác nguy hiểm (xóa hẳn) — tô đỏ nút và nút xác nhận. */
  destructive?: boolean
  disabled?: boolean
  onConfirm: () => void
  className?: string
}

/**
 * Nút biểu tượng trong hàng bảng, hỏi xác nhận trước khi chạy.
 *
 * Dùng cho những thao tác đổi trạng thái hệ thống ngay lập tức (khóa tài khoản,
 * xóa hẳn bản ghi): bấm nhầm một ô nhỏ trong bảng là chuyện quá dễ.
 * Cần nút CÓ CHỮ thì dùng `DeleteConfirmButton`.
 */
export function ConfirmIconButton({
  icon: Icon,
  title,
  label,
  confirmTitle,
  confirmDescription,
  confirmLabel = 'Đồng ý',
  destructive,
  disabled,
  onConfirm,
  className,
}: ConfirmIconButtonProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/*  `type="button"` KHÔNG được bỏ: nút này hay nằm lọt trong một `<form>`
           (thẻ quyền truy cập của văn bản nằm ngay trong form thông tin), mà
           `<button>` không ghi type thì mặc định là **submit**. Hậu quả người
           dùng thấy: bấm biểu tượng thu hồi, hộp xác nhận mới hiện ra thôi mà
           toast «Cập nhật văn bản» đã nhảy — form vừa bị gửi đi (25/08/2026). */}
      <Button
        type="button"
        variant="ghost"
        size={label ? 'sm' : 'icon-sm'}
        title={title}
        //  Có chữ rồi thì thôi `aria-label`: nó ĐÈ lên nội dung nút, nên trình
        //  đọc màn hình sẽ bỏ qua chữ vừa thêm và đọc lại đúng cái tooltip.
        aria-label={label ? undefined : title}
        disabled={disabled}
        className={cn(destructive && 'text-destructive hover:text-destructive', className)}
        onClick={() => setOpen(true)}
      >
        <Icon />
        {label}
      </Button>

      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmTitle}</AlertDialogTitle>
            {confirmDescription && (
              <AlertDialogDescription>{confirmDescription}</AlertDialogDescription>
            )}
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={cn(destructive && buttonVariants({ variant: 'destructive' }))}
              onClick={onConfirm}
            >
              {confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
