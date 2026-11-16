import { AlertTriangle, Pencil } from 'lucide-react'

import type { PurchaseOrderLineIssue } from '../utils/required-fields'

/**
 * bao-CR-758 — khung vàng *Còn thiếu thông tin bắt buộc — chưa gửi duyệt được*, port từ bản v1
 * (`frontend/src/pages/PurchaseOrderDetail.tsx`, CR-095): nêu TRƯỚC dòng nào còn thiếu ô nào, thay
 * vì để người lập bấm Gửi duyệt rồi mới nhận một câu lỗi dài. Trang chỉ dựng khung khi đơn còn sửa
 * được — đơn đã trình / đã duyệt mà kêu thiếu thì không có đường sửa, chỉ làm rối.
 */
export function PurchaseOrderMissingFieldsNotice({
  issues,
  isMobile = false,
}: {
  issues: PurchaseOrderLineIssue[]
  /** Khổ điện thoại không có cột Hành động — câu nhắc nói "chạm vào thẻ dòng hàng". */
  isMobile?: boolean
}) {
  if (!issues.length) return null
  return (
    <div
      role="status"
      className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs"
    >
      <p className="flex items-center gap-1.5 font-medium">
        <AlertTriangle className="size-3.5" />
        Còn thiếu thông tin bắt buộc — chưa gửi duyệt được
      </p>
      {issues.map((issue) => (
        <p key={issue.lineNumber}>
          Dòng {issue.lineNumber} ({issue.code}): {issue.missing.join(', ')}
        </p>
      ))}
      <p className="flex flex-wrap items-center gap-1 text-muted-foreground">
        {isMobile ? (
          'Chạm vào thẻ dòng hàng để mở Chi tiết dòng và điền.'
        ) : (
          <>
            Bấm <Pencil className="size-3" aria-label="bút chì" /> ở cột Hành động để mở Chi tiết
            dòng và điền.
          </>
        )}
      </p>
    </div>
  )
}
