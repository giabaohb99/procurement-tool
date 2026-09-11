import { AlertTriangle, ArrowRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import type { DocumentRecord, DocumentVersion } from '../types/document-record'

interface DocumentVersionBannerProps {
  document: DocumentRecord
  /** Phiên bản đang mở trên màn hình. */
  version: DocumentVersion
  onGoToCurrent: () => void
}

/**
 * Băng cảnh báo trên bản KHÔNG phải bản đang dùng (C18).
 *
 * Bắt buộc phải có vì bản cũ **không bị xóa và không bị ẩn** — người mở đúng
 * đường dẫn cũ vẫn thấy nội dung bản 1.0 y như thật. Không có băng này thì họ
 * đọc xong rồi làm theo một bản đã hết hiệu lực mà không hề biết.
 *
 * Hai trường hợp khác nhau, nói khác nhau:
 *  - bản cũ đã bị thay thế → chỉ sang bản đang dùng;
 *  - bản mới còn đang duyệt → nói rõ nó CHƯA có hiệu lực, đừng làm theo.
 */
export function DocumentVersionBanner({
  document,
  version,
  onGoToCurrent,
}: DocumentVersionBannerProps) {
  if (version.is_current) return null

  const isNewer = !version.is_locked || version.status < 3
  const label = isNewer
    ? `Bản ${version.version_no} chưa có hiệu lực — bản đang áp dụng là ${document.version_no}.`
    : `Bản ${version.version_no} đã bị thay thế bởi bản ${document.version_no}${
        document.effective_date ? ` từ ngày ${formatDate(document.effective_date)}` : ''
      }.`

  return (
    <div className="mb-3 flex flex-wrap items-center gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
      <AlertTriangle className="size-4 shrink-0 text-amber-700" />
      <p className="min-w-0 flex-1 text-sm text-amber-900">{label}</p>

      {/*  ⚠️ **`max-sm:w-full` — nút xuống HÀNG RIÊNG ở khổ hẹp**, cùng bệnh với
          `document-needs-review-banner`. `flex-wrap` không tự cứu được: ô chữ
          `flex-1` nhường chỗ cho tới khi chỉ còn bằng từ dài nhất, nên hàng không
          bao giờ tràn và nút không bao giờ bị đẩy xuống. Đo ở 390px: nút giữ
          nguyên 185px, câu cảnh báo còn ~150px và rớt thành bốn dòng.

          Câu này là thứ DUY NHẤT nói rằng bản đang đọc không có hiệu lực — bóp
          nó lại để chừa chỗ cho cái nút dẫn đi nơi khác là đổi đúng phần quan
          trọng lấy phần phụ. */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onGoToCurrent}
        className="max-sm:w-full"
      >
        Sang bản đang dùng
        <ArrowRight className="size-4" />
      </Button>
    </div>
  )
}
