import { AlertTriangle, Check, ExternalLink } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'

interface DocumentNeedsReviewBannerProps {
  needsReview: boolean
  note: string
  /**
   * Bản gốc để đối chiếu (`source_document_id` — có với bản riêng của pháp nhân
   * con). Không có thì giấu nút mở, và câu hướng dẫn chỉ sang tab Quan hệ.
   */
  sourceDocumentId?: number | null
  /** Chỉ người sửa được văn bản mới xác nhận được là đã rà xong. */
  canWrite?: boolean
  onConfirm?: () => void
  pending?: boolean
}

/**
 * BĂNG "CẦN RÀ LẠI" — bật khi văn bản CHA đổi (bản gốc lên phiên bản mới, cha
 * bị bãi bỏ, ràng buộc của bản trích).
 *
 * Hệ thống chỉ **đánh dấu**, không bao giờ tự sửa nội dung văn bản con: người rà
 * mới là người quyết định.
 *
 * ⚠️ Trước 19/08/2026 băng này **không có nút nào**, với lý do "bỏ dấu là việc
 * của người sửa văn bản, không phải một cái bấm cho hết cảnh báo". Ý đúng nhưng
 * hụt một nửa: trong mã có **năm chỗ bật cờ và không chỗ nào tắt**, nên rà xong,
 * sửa xong, ban hành xong thì băng vàng vẫn treo vĩnh viễn. Vài tháng là văn bản
 * nào cũng đeo băng, và đúng lúc cảnh báo cần được chú ý thì không ai nhìn nữa.
 *
 * Nay có hai nút, và nút xác nhận **bắt ghi kết luận** — "đã đối chiếu, vẫn
 * đúng" khác hẳn "đã sửa theo Chương II" nếu về sau có tranh chấp.
 */
export function DocumentNeedsReviewBanner({
  needsReview,
  note,
  sourceDocumentId,
  canWrite = false,
  onConfirm,
  pending = false,
}: DocumentNeedsReviewBannerProps) {
  if (!needsReview) return null

  return (
    <div className="mb-3 flex flex-wrap items-start gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />

      <div className="min-w-0 flex-1 text-sm text-amber-900">
        <p className="font-medium">Văn bản này cần rà lại.</p>
        {note && <p className="text-amber-800">{note}</p>}
        {!sourceDocumentId && (
          <p className="mt-1 text-amber-800">
            Mở tab <strong>Quan hệ</strong> để tìm văn bản gốc rồi đối chiếu.
          </p>
        )}
      </div>

      <div className="flex shrink-0 flex-wrap gap-2">
        {/*  Mở TAB MỚI: người rà cần đặt hai bản cạnh nhau mà đọc, chuyển trang
            là mất chỗ đang đứng. */}
        {sourceDocumentId && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              window.open(
                appRoutes.document.documentDetail(sourceDocumentId),
                '_blank',
                'noopener',
              )
            }
          >
            <ExternalLink className="size-4" />
            Mở bản gốc để đối chiếu
          </Button>
        )}

        {canWrite && onConfirm && (
          <Button type="button" size="sm" disabled={pending} onClick={onConfirm}>
            <Check className="size-4" />
            Đã rà xong
          </Button>
        )}
      </div>
    </div>
  )
}
