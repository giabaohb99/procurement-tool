import { AlertTriangle, Check, Copy, ExternalLink } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

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
 * BĂNG NGUỒN GỐC / "CẦN RÀ LẠI".
 *
 * Bản clone luôn hiện lối mở bản gốc, kể cả khi chưa có cảnh báo: pháp nhân
 * nhận cần đặt hai bản cạnh nhau để chỉnh bản của mình trước khi ban hành. Khi
 * bản gốc đổi thì cùng băng này chuyển sang trạng thái cảnh báo và cho xác nhận
 * đã rà xong.
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
  const isClone = Boolean(sourceDocumentId)
  if (!needsReview && !isClone) return null

  return (
    <div
      className={cn(
        'mb-3 flex flex-wrap items-start gap-3 rounded-md border px-4 py-3',
        needsReview ? 'border-amber-300 bg-amber-50' : 'border-primary/20 bg-primary/5',
      )}
    >
      {needsReview ? (
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
      ) : (
        <Copy className="mt-0.5 size-4 shrink-0 text-primary" />
      )}

      <div
        className={cn('min-w-0 flex-1 text-sm', needsReview ? 'text-amber-900' : 'text-foreground')}
      >
        {needsReview ? (
          <>
            <p className="font-medium">Văn bản này cần rà lại.</p>
            {note && <p className="text-amber-800">{note}</p>}
            {!sourceDocumentId && (
              <p className="mt-1 text-amber-800">
                Mở tab <strong>Quan hệ</strong> để tìm văn bản gốc rồi đối chiếu.
              </p>
            )}
          </>
        ) : (
          <>
            <p className="font-medium">Đây là bản riêng nhận từ văn bản gốc.</p>
            <p className="text-muted-foreground">
              Mở bản gốc để đối chiếu, sau đó chỉnh nội dung bản này cho pháp nhân hiện tại trước
              khi gửi ban hành.
            </p>
          </>
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
              window.open(appRoutes.document.documentDetail(sourceDocumentId), '_blank', 'noopener')
            }
          >
            <ExternalLink className="size-4" />
            Xem bản gốc
          </Button>
        )}

        {/*  CHỈ khi đang có dấu «cần rà lại». Việc duy nhất của nút này là GỠ
            cái dấu đó, nên bản riêng chưa bị đánh dấu mà bày nút ra thì bấm vào
            chỉ nhận đúng một câu từ chối: *«Văn bản này không có dấu cần rà
            lại»* (`service.py::xac_nhan_ra_soat`). Người dùng gõ xong lý do,
            bấm xác nhận, rồi ăn báo đỏ — mà họ không làm gì sai cả. */}
        {needsReview && canWrite && onConfirm && (
          <Button type="button" size="sm" disabled={pending} onClick={onConfirm}>
            <Check className="size-4" />
            Đã rà xong
          </Button>
        )}
      </div>
    </div>
  )
}
