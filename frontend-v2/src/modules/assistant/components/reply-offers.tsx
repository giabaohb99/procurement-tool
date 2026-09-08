import { FileDown, FilePlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { downloadFile } from '@/core/api'
import { Button } from '@/shared/ui/button'
import type { DraftOffer, DraftTarget, FileOffer, UpdateOffer } from '../utils/reply-offers'
import { draftNavigation } from '../utils/reply-offers'
import { UpdateProposalCard } from './update-proposal-card'

const DRAFT_LABELS: Record<DraftTarget, string> = {
  survey: 'Tạo yêu cầu báo giá',
  purchase: 'Tạo yêu cầu mua hàng',
  leave: 'Tạo đơn nghỉ phép',
  payment: 'Tạo đề nghị thanh toán',
  ticket: 'Tạo phiếu hỗ trợ',
}

interface ReplyOffersProps {
  draft: DraftOffer | null
  file: FileOffer | null
  /** Đề xuất sửa phiếu (CR-218) — thẻ so sánh cũ/mới + nút 'Xác nhận sửa'. */
  update?: UpdateOffer | null
  /** Người dùng bấm 'Bỏ qua' trên thẻ đề xuất sửa — cha gỡ offer khỏi state. */
  onDismissUpdate?: () => void
  /** Hội thoại đang mở — nút chỉ hiện khi khớp, tránh đeo nút của hội thoại khác. */
  conversationId: number
  /** Đang chờ trợ lý trả lời thì ẩn nút (lượt mới có thể gỡ/thay bản nháp). */
  busy: boolean
  /** Gọi ngay trước khi điều hướng mở form — bong bóng dùng để tự thu gọn. */
  onNavigate?: () => void
}

/**
 * Hai thanh chào hành động dưới luồng chat: mở form phiếu đã điền sẵn (bấm mới mở,
 * phiếu KHÔNG tự tạo — người dùng rà lại rồi tự bấm Tạo trong form) + tải file báo
 * cáo vừa xuất. Dùng chung cho TRANG Trợ lý và BONG BÓNG góc — trước đây chỉ trang
 * có, người chat trong bong bóng bị bot mời "bấm nút bên dưới" mà không có nút nào.
 */
export function ReplyOffers({
  draft,
  file,
  update,
  onDismissUpdate,
  conversationId,
  busy,
  onNavigate,
}: ReplyOffersProps) {
  const navigate = useNavigate()

  const showDraft = draft != null && draft.conversationId === conversationId && !busy
  const showFile = file != null && file.conversationId === conversationId && !busy
  const showUpdate = update != null && update.conversationId === conversationId && !busy

  return (
    <>
      {showUpdate ? (
        <UpdateProposalCard
          //  key theo token: lượt sau đề xuất khác thì thẻ dựng lại từ đầu, không giữ
          //  trạng thái "đã sửa" của đề xuất cũ.
          key={update.proposal.confirm_token}
          offer={update}
          onDismiss={() => onDismissUpdate?.()}
          onNavigate={onNavigate}
        />
      ) : null}

      {showDraft ? (
        <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
          <p className="text-xs text-muted-foreground">
            Trợ lý đã soạn sẵn nội dung phiếu. Mở form để kiểm tra rồi bấm Tạo.
          </p>
          <Button
            size="sm"
            className="shrink-0"
            onClick={() => {
              onNavigate?.()
              const nav = draftNavigation(draft)
              navigate(nav.to, nav.state ? { state: nav.state } : undefined)
            }}
          >
            <FilePlus />
            {DRAFT_LABELS[draft.target]}
          </Button>
        </div>
      ) : null}

      {showFile ? (
        <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
          <p className="min-w-0 truncate text-xs text-muted-foreground">
            Trợ lý đã tạo file báo cáo: {file.filename}
          </p>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0"
            onClick={() => void downloadFile(file.downloadUrl, file.filename).catch(() => {})}
          >
            <FileDown />
            Tải báo cáo
          </Button>
        </div>
      ) : null}
    </>
  )
}
