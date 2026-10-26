import { AlertTriangle, Check, CircleCheck, CircleX, Loader2, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { assistantApi } from '../api/assistant-api'
import type { ApprovalProposal, ConfirmApprovalResult } from '../types/assistant'

interface ApprovalProposalCardProps {
  proposal: ApprovalProposal
  /** Người dùng bấm 'Bỏ qua' — gỡ thẻ (token vẫn tự hết hạn ở backend). */
  onDismiss: () => void
  /** Gọi trước khi điều hướng mở phiếu — bong bóng chat dùng để tự thu gọn. */
  onNavigate?: () => void
}

const STALE_MESSAGE = 'Phiếu đã thay đổi, hỏi lại AI để có đề xuất mới.'

/** Lỗi 409 = phiếu đã đổi trạng thái / sang chặng khác từ lúc đề xuất: token cũ không dùng lại được nữa. */
function isStale(error: unknown): boolean {
  return (error as { response?: { status?: number } } | null)?.response?.status === 409
}

/**
 * Thẻ xác nhận DUYỆT / TỪ CHỐI một phiếu qua Trợ lý web (kh-AI2-7, cùng khuôn với thẻ sửa phiếu CR-218): trợ lý chỉ ĐỀ
 * XUẤT; hệ thống chỉ ghi khi chính người dùng bấm nút xác nhận ở đây. Một thẻ một phiếu — không có duyệt hàng loạt.
 * Backend kiểm lại người duyệt + chặng tại lúc bấm; phiếu đã đổi (409) thì thẻ bảo hỏi lại AI và gỡ nút xác nhận.
 */
export function ApprovalProposalCard({ proposal, onDismiss, onNavigate }: ApprovalProposalCardProps) {
  const navigate = useNavigate()
  //  Chặn bấm đúp ngay trong tick: `saving` là state nên chỉ đúng ở lần render sau.
  const busy = useRef(false)
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState<ConfirmApprovalResult | null>(null)
  const [error, setError] = useState<{ message: string; stale: boolean } | null>(null)
  const rejecting = proposal.action === 'reject'
  const verb = rejecting ? 'từ chối' : 'duyệt'

  const handleConfirm = async () => {
    if (busy.current) return
    busy.current = true
    setSaving(true)
    setError(null)
    try {
      setDone(await assistantApi.confirmApproval(proposal.confirm_token))
    } catch (err) {
      setError(isStale(err) ? { message: STALE_MESSAGE, stale: true } : { message: extractErrorMessage(err), stale: false })
    } finally {
      busy.current = false
      setSaving(false)
    }
  }

  if (done) {
    return (
      <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
        <p className="flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
          <Check className="size-4 shrink-0 text-success" />
          <span className="truncate">
            Đã {done.approved ? 'duyệt' : 'từ chối'} {done.entity_label} {done.code}.
          </span>
        </p>
        <Button
          size="sm"
          variant="outline"
          className="shrink-0"
          onClick={() => {
            onNavigate?.()
            navigate(done.url)
          }}
        >
          Mở phiếu
        </Button>
      </div>
    )
  }

  return (
    <div className="border-t bg-muted/40 px-4 py-2.5">
      <div className="flex items-center gap-1.5 text-xs font-medium">
        {rejecting ? (
          <CircleX className="size-3.5 text-destructive" />
        ) : (
          <CircleCheck className="size-3.5 text-primary" />
        )}
        <span>
          Đề xuất {verb} {proposal.entity_label} {proposal.code}
          <span className="font-normal text-muted-foreground"> ({proposal.step})</span>
        </span>
      </div>

      <dl className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-xs">
        {proposal.summary
          .filter((row) => row.value)
          .map((row) => (
            <div key={row.label} className="contents">
              <dt className="text-muted-foreground">{row.label}:</dt>
              <dd className="break-words">{row.value}</dd>
            </div>
          ))}
        {proposal.note ? (
          <div className="contents">
            <dt className="text-muted-foreground">{rejecting ? 'Lý do từ chối' : 'Ghi chú'}:</dt>
            <dd className="break-words font-medium">{proposal.note}</dd>
          </div>
        ) : null}
      </dl>

      {error ? (
        <p className="mt-1.5 flex items-start gap-1.5 text-xs text-destructive" role="alert">
          <AlertTriangle className="mt-px size-3.5 shrink-0" />
          <span>{error.message}</span>
        </p>
      ) : (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Phiếu chưa được {verb} — chỉ ghi khi bạn bấm Xác nhận {verb}.
        </p>
      )}

      <div className="mt-2 flex items-center justify-end gap-2">
        <Button type="button" size="sm" variant="ghost" disabled={saving} onClick={onDismiss}>
          <X />
          Bỏ qua
        </Button>
        {error?.stale ? null : (
          <Button
            type="button"
            size="sm"
            variant={rejecting ? 'destructive' : 'default'}
            disabled={saving}
            onClick={() => void handleConfirm()}
          >
            {saving ? <Loader2 className="animate-spin" /> : <Check />}
            Xác nhận {verb}
          </Button>
        )}
      </div>
    </div>
  )
}
