import { ExternalLink } from 'lucide-react'

/**
 * Link TỚI CHỖ LẤY giá trị của một ô cấu hình (trang cấp khóa API, danh sách model).
 *
 * Lý do có mặt: khóa API là thứ người dùng phải tự đi đăng ký rồi mang về. Ô nhập
 * không kèm đường dẫn thì việc đầu tiên họ làm là đi hỏi người khác — và câu trả
 * lời luôn là cùng một đường dẫn ấy.
 *
 * `rel="noreferrer"` bắt buộc: thiếu nó thì trang đích cầm `window.opener` và
 * đổi được địa chỉ tab ERP đang mở sau lưng người dùng.
 */
export function SettingDocLink({ href }: { href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
    >
      Lấy ở đây
      <ExternalLink className="size-3" />
    </a>
  )
}
