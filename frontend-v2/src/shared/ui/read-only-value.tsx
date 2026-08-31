import { cn } from '@/shared/utils/cn'

interface ReadOnlyValueProps {
  children?: React.ReactNode
  /**
   * Chữ dài (tên hàng, ghi chú, mô tả): xuống dòng thay vì cắt cụt, và cao tối
   * thiểu bằng `Textarea` để bố cục không nhảy khi bật/tắt chế độ sửa.
   */
  multiline?: boolean
  className?: string
}

/**
 * Ô CHỈ ĐỌC — dùng thay cho `<Input disabled>` / `<Textarea disabled>` ở mọi chỗ
 * chỉ hiện dữ liệu chứ không cho sửa.
 *
 * `disabled` là thuộc tính của Ô NHẬP LIỆU, nói rằng "ô này không tham gia biểu
 * mẫu". Trình duyệt hiểu theo nghĩa đen: ô mất khả năng nhận con trỏ nên KHÔNG
 * bôi đen và KHÔNG copy được — người dùng không chép nổi mã vật tư ra ngoài —
 * lại còn bị làm mờ 50% nên giá trị thật nhìn y như chữ gợi ý (placeholder).
 * Chữ nằm trong thẻ thường thì bôi đen / copy / đọc màn hình đều bình thường.
 *
 * `readOnly` cũng giữ được việc bôi đen, nhưng ô vẫn trông như đang mời gõ vào.
 * Ở đây phần lớn màn là XEM chứng từ, nên hiện thẳng dạng chữ đúng hơn.
 *
 * MÀU: nền `--locked` (xám thấy rõ) + viền `--input`, đối lại ô nhập được nay
 * ghim nền TRẮNG (`bg-background`). Hai nền phải khác nhau đủ để liếc một cái
 * là biết ô nào gõ được — nền `bg-muted/35` cũ nhạt tới mức lẫn với ô trắng
 * (khách báo 31/08/2026).
 */
export function ReadOnlyValue({ children, multiline = false, className }: ReadOnlyValueProps) {
  const isDash = typeof children === 'string' && (children === '—' || children === '-')
  const empty = children === null || children === undefined || children === '' || isDash

  return (
    <div
      className={cn(
        'rounded-lg border border-input bg-locked px-3 text-sm font-medium text-locked-foreground',
        multiline
          ? 'min-h-16 py-2.5 break-words whitespace-pre-wrap'
          : 'flex min-h-9 items-center py-2',
        className,
      )}
    >
      {empty ? null : children}
    </div>
  )
}
