import { Lock } from 'lucide-react'

interface DocumentSubmittedLockNoticeProps {
  /** Văn bản (hay bản đang mở) có đang trình duyệt không. */
  submitted: boolean
}

/**
 * Băng báo VÌ SAO không gõ được — hiện khi văn bản đang trình duyệt.
 *
 * Không có băng này thì người soạn mở trang, thấy trang giấy xám ngắt và không
 * bấm được vào đâu, rồi đi hỏi "hệ hỏng à". Nói luôn cả đường ra: rút phiếu thì
 * văn bản về Nháp và sửa tiếp được (D-029).
 */
export function DocumentSubmittedLockNotice({ submitted }: DocumentSubmittedLockNoticeProps) {
  if (!submitted) return null

  return (
    <div className="mb-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
      <Lock className="mt-0.5 size-4 shrink-0" />
      <span>
        <strong>Đang trình duyệt nên nội dung và thông tin đã khóa.</strong> Người duyệt phải ký
        đúng bản họ đọc — sửa được lúc này thì bản ban hành sẽ khác bản đã xem. Muốn sửa: mở tab{' '}
        <strong>Phê duyệt</strong> rồi <strong>rút phiếu</strong>, hoặc chờ người duyệt trả lại;
        văn bản về <strong>Nháp</strong> là gõ tiếp được.
      </span>
    </div>
  )
}
