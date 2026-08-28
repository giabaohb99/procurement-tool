import { Check, Loader2, MoveRight, PencilLine, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { assistantApi } from '../api/assistant-api'
import type { ConfirmUpdateResult } from '../types/assistant'
import type { UpdateOffer } from '../utils/reply-offers'

interface UpdateProposalCardProps {
  offer: UpdateOffer
  /** Người dùng bấm 'Bỏ qua' — gỡ thẻ (token vẫn tự hết hạn ở backend). */
  onDismiss: () => void
  /** Gọi trước khi điều hướng mở phiếu — bong bóng chat dùng để tự thu gọn. */
  onNavigate?: () => void
}

/**
 * Thẻ xác nhận đề xuất sửa phiếu (CR-218, khuôn 2 — tầng GHI có xác nhận): trợ lý chỉ
 * ĐỀ XUẤT (cũ → mới); hệ thống chỉ ghi khi CHÍNH NGƯỜI DÙNG bấm 'Xác nhận sửa' ở đây.
 * Token trong đề xuất buộc vào người hỏi và hết hạn sau 15 phút; backend kiểm lại toàn
 * bộ quyền/phạm vi/trạng thái tại thời điểm bấm nên thẻ cũ bấm lại chỉ ăn lỗi, không
 * ghi bậy.
 */
export function UpdateProposalCard({ offer, onDismiss, onNavigate }: UpdateProposalCardProps) {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState<ConfirmUpdateResult | null>(null)

  const { proposal } = offer

  const handleConfirm = async () => {
    setSaving(true)
    try {
      setDone(await assistantApi.confirmUpdate(proposal.confirm_token))
    } catch {
      // Token hết hạn / mất quyền / phiếu đổi trạng thái — tầng API đã toast lỗi,
      // thẻ giữ nguyên để người dùng đọc lại đề xuất rồi tự bỏ qua.
    } finally {
      setSaving(false)
    }
  }

  const openDocument = (url: string) => {
    onNavigate?.()
    navigate(url)
  }

  if (done) {
    return (
      <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
        <p className="flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
          <Check className="size-4 shrink-0 text-success" />
          <span className="truncate">
            Đã sửa {done.entity_label} {done.code}: {done.updated_fields.join(', ')}.
          </span>
        </p>
        <Button size="sm" variant="outline" className="shrink-0" onClick={() => openDocument(done.url)}>
          Mở phiếu
        </Button>
      </div>
    )
  }

  return (
    <div className="border-t bg-muted/40 px-4 py-2.5">
      <div className="flex items-center gap-1.5 text-xs font-medium">
        <PencilLine className="size-3.5 text-primary" />
        <span>
          Đề xuất sửa {proposal.entity_label} {proposal.code}
          <span className="font-normal text-muted-foreground"> ({proposal.doc_status_label})</span>
        </span>
      </div>

      <ul className="mt-1.5 space-y-1">
        {proposal.changes.map((change) => (
          <li key={change.field} className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-muted-foreground">{change.label}:</span>
            <span className="break-all line-through opacity-60">{change.old || '(trống)'}</span>
            <MoveRight className="size-3 shrink-0 text-muted-foreground" />
            <span className="break-all font-medium">{change.new}</span>
          </li>
        ))}
      </ul>

      <div className="mt-2 flex items-center justify-end gap-2">
        <Button type="button" size="sm" variant="ghost" disabled={saving} onClick={onDismiss}>
          <X />
          Bỏ qua
        </Button>
        <Button type="button" size="sm" disabled={saving} onClick={() => void handleConfirm()}>
          {saving ? <Loader2 className="animate-spin" /> : <Check />}
          Xác nhận sửa
        </Button>
      </div>
    </div>
  )
}
