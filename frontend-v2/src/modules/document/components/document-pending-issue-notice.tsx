import { Send } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

interface DocumentPendingIssueNoticeProps {
  /** Người đang xem có phải người soạn thảo không — quyết định câu nói. */
  isDrafter: boolean
  /** Tên người soạn thảo, để người khác biết phải chờ ai. */
  drafterName?: string
  className?: string
}

/**
 * BĂNG «CHỜ BAN HÀNH» (26/08/2026).
 *
 * Trạng thái này rất dễ đọc nhầm là hệ đứng: chữ ký đã đủ, phiên duyệt đã đóng,
 * mà văn bản vẫn chưa có số hiệu và chưa có hiệu lực. Không nói ra thì người
 * soạn ngồi chờ một cú bấm của người khác, còn người khác thì tưởng xong rồi —
 * văn bản nằm im vô thời hạn.
 *
 * Nên băng này nói HAI câu khác nhau cho hai người khác nhau: người soạn được
 * bảo *bấm đi*, người còn lại được bảo *chờ ai*.
 */
export function DocumentPendingIssueNotice({
  isDrafter,
  drafterName,
  className,
}: DocumentPendingIssueNoticeProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-md border border-sky-300 bg-sky-50 px-4 py-3 text-sm text-sky-900',
        className,
      )}
    >
      <Send className="mt-0.5 size-4 shrink-0 text-sky-700" />
      {isDrafter ? (
        <span>
          Văn bản đã ký đủ các bước và <b>đang chờ bạn ban hành</b>. Bấm <b>Ban hành</b> để
          cấp số hiệu, khóa phiên bản và gửi thông báo — lúc đó bạn chọn được địa chỉ
          đứng tên gửi thư.
        </span>
      ) : (
        <span>
          Văn bản đã ký đủ các bước, <b>chờ người soạn thảo</b>
          {drafterName ? (
            <>
              {' '}
              — <b>{drafterName}</b>
            </>
          ) : null}{' '}
          bấm Ban hành. Chưa bấm thì chưa có số hiệu và chưa có hiệu lực.
        </span>
      )}
    </div>
  )
}
