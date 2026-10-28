import { Paperclip } from 'lucide-react'

import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'

interface HeadcountPlanAttachmentsProps {
  planId: number
  /** `files_hidden` của chi tiết — người xem không được xem lương của pháp nhân này. */
  hidden: boolean
  canManage: boolean
}

/**
 * Tệp đính kèm của kế hoạch — khuôn chứng từ dùng chung (`/api/attachments`, entity `headcount_plan`).
 *
 * ⚠️ Bị che thì KHÔNG dựng thẻ tệp: tệp có thể là bảng tính chi phí nên backend che cùng luật tiền, và
 * cửa `/api/attachments` cũng chặn — dựng thẻ là ăn 403 ngay lúc mở trang. Câu thay thế nói rõ là CÓ
 * thể có tệp, không phải «chưa ai đính kèm».
 */
export function HeadcountPlanAttachments({ planId, hidden, canManage }: HeadcountPlanAttachmentsProps) {
  if (hidden) {
    return (
      <p className="flex items-center gap-2 rounded-md border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground">
        <Paperclip className="size-4 shrink-0" />
        Tệp đính kèm chỉ hiện với người được xem lương của pháp nhân này.
      </p>
    )
  }
  return <DocumentAttachmentsCard entity="headcount_plan" entityId={planId} canManage={canManage} />
}
