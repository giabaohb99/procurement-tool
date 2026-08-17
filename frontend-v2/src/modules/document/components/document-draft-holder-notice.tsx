import { AlertTriangle, ArrowRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import type { DocumentVersion } from '../types/document-record'

interface DocumentDraftHolderNoticeProps {
  /** Bản nháp đang mở — bản duy nhất chưa khóa của văn bản. */
  draft: DocumentVersion
  /** Bấm để nhảy tới đúng bản nháp đó. Bỏ trống thì không hiện nút. */
  onOpenDraft?: () => void
  className?: string
}

/**
 * BÁO AI ĐANG GIỮ BẢN NHÁP (C14).
 *
 * Một văn bản chỉ mở được một bản nháp cùng lúc — ràng buộc ép ở tầng dữ liệu
 * bằng cột sinh `open_slot`, nên hai người bấm "mở phiên bản mới" cùng lúc thì
 * đúng một người thắng.
 *
 * Người thua **cần biết hỏi ai**. Câu "đang có bản nháp mở" không đủ: nó nói có
 * chuyện xảy ra nhưng không nói phải làm gì tiếp. Nên chỗ này ghi rõ bản số
 * mấy, ai giữ, mở từ lúc nào, kèm đường sang xem bản đó.
 */
export function DocumentDraftHolderNotice({
  draft,
  onOpenDraft,
  className,
}: DocumentDraftHolderNoticeProps) {
  //  `created_by_name` rỗng khi tài khoản tạo bản nháp đã bị xóa — vẫn phải nói
  //  được là có người giữ, chỉ là không biết tên.
  const holder = draft.created_by_name.trim()

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3',
        className,
      )}
    >
      <AlertTriangle className="size-4 shrink-0 text-amber-700" />

      <div className="min-w-0 flex-1 text-sm text-amber-900">
        <p>
          Bản nháp <span className="font-medium">{draft.version_no}</span> đang do{' '}
          <span className="font-medium">{holder || 'một người khác'}</span> giữ.
        </p>
        <p className="text-amber-800">
          {draft.created_at && `Mở từ ${formatDateTime(draft.created_at)}. `}
          Chốt xong bản này rồi mới mở được phiên bản tiếp theo.
        </p>
      </div>

      {onOpenDraft && (
        <Button type="button" variant="outline" size="sm" onClick={onOpenDraft}>
          Xem bản nháp
          <ArrowRight className="size-4" />
        </Button>
      )}
    </div>
  )
}
