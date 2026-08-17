import { AlertTriangle } from 'lucide-react'

interface DocumentNeedsReviewBannerProps {
  needsReview: boolean
  note: string
}

/**
 * BĂNG "CẦN RÀ LẠI" — bật khi văn bản CHA đổi (E11 a, E07/E08 sau này).
 *
 * Hệ thống chỉ **đánh dấu**, tuyệt đối không tự sửa nội dung con: người rà quyết
 * định, và quyết định đó vào nhật ký thao tác. Vì thế băng này không có nút "đã
 * xử lý" — bỏ dấu là việc của người sửa văn bản, không phải một cái bấm cho hết
 * cảnh báo.
 */
export function DocumentNeedsReviewBanner({
  needsReview,
  note,
}: DocumentNeedsReviewBannerProps) {
  if (!needsReview) return null

  return (
    <div className="mb-3 flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
      <div className="text-sm text-amber-900">
        <p className="font-medium">Văn bản này cần rà lại.</p>
        {note && <p className="text-amber-800">{note}</p>}
      </div>
    </div>
  )
}
