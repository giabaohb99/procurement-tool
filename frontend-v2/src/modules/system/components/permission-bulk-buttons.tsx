import { cn } from '@/shared/utils/cn'

/**
 * Hai nút "chọn hết" của ma trận phân quyền — tách khỏi `role-permission-matrix`
 * cho tệp đó chỉ còn việc dựng bảng.
 */

/** Nút thao tác gọn ở thanh trên bảng ma trận. */
export function PermissionBulkButton({
  children,
  danger,
  disabled,
  onClick,
}: {
  children: string
  danger?: boolean
  disabled?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={cn(
        'rounded border px-1.5 py-0.5 transition',
        'enabled:hover:bg-accent enabled:hover:text-foreground',
        danger &&
          'enabled:hover:border-destructive/40 enabled:hover:bg-destructive/10 enabled:hover:text-destructive',
        //  `enabled:` chứ không `hover:` trơn — nút đã khóa mà rê vào vẫn sáng
        //  lên thì người dùng bấm hoài không được, tưởng lỗi (cùng luật với
        //  `shared/ui/checkbox.tsx`).
        'disabled:cursor-not-allowed disabled:opacity-50',
      )}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

/**
 * Nút "Chọn hết / Bỏ hết" của một dòng (phân hệ hoặc entity).
 *
 * ⚠️ **Luôn hiện, không ẩn chờ rê chuột.** Bản trước để
 * `opacity-0 group-hover:opacity-100` và khách báo màn Phân quyền "không có chức
 * năng chọn hết" — chức năng chỉ hiện khi rê chuột vào đúng dòng thì bằng như
 * không có, nhất là trên máy cảm ứng.
 *
 * `label` chỉ đi vào `aria-label`: 60 dòng cùng một chữ "Chọn hết" thì người
 * dùng trình đọc màn hình nghe một chuỗi giống hệt nhau, không biết đang ở dòng nào.
 */
export function PermissionRowBulkButton({
  allOn,
  label,
  onClick,
  className,
}: {
  allOn: boolean
  label: string
  onClick: () => void
  className?: string
}) {
  const text = allOn ? 'Bỏ hết' : 'Chọn hết'
  return (
    <button
      type="button"
      className={cn(
        'shrink-0 rounded px-1.5 py-0.5 text-xs font-normal text-muted-foreground/80 transition',
        'hover:bg-background hover:text-foreground focus-visible:text-foreground',
        className,
      )}
      onClick={onClick}
      aria-label={`${text} quyền của ${label}`}
    >
      {text}
    </button>
  )
}
