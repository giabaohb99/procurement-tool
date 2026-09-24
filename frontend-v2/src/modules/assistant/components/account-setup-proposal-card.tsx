import { Check, Loader2, Minus, Plus, ShieldCheck, TriangleAlert, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { assistantApi } from '../api/assistant-api'
import type {
  AccountSetupLine,
  AccountSetupProposal,
  ConfirmAccountSetupResult,
} from '../types/assistant'

interface AccountSetupProposalCardProps {
  proposal: AccountSetupProposal
  /** Người dùng bấm 'Bỏ qua' — gỡ thẻ (token vẫn tự hết hạn ở backend). */
  onDismiss: () => void
  /** Gọi trước khi điều hướng mở màn Phân quyền — bong bóng chat dùng để tự thu gọn. */
  onNavigate?: () => void
}

/** Biểu tượng + màu cho từng kết cục của một dòng — chữ vẫn là của backend. */
function LineStatusIcon({ status }: { status: AccountSetupLine['status'] }) {
  if (status === 'thêm') return <Plus className="size-3.5 shrink-0 text-success" />
  if (status === 'bỏ') return <Minus className="size-3.5 shrink-0 text-destructive" />
  return <Check className="size-3.5 shrink-0 text-muted-foreground" />
}

/**
 * Thẻ xác nhận đề xuất lập / chỉnh BỘ TÀI KHOẢN thu mua (bao-CR-435) — cùng khuôn với thẻ
 * sửa phiếu: trợ lý chỉ ĐỀ XUẤT từng dòng thêm / bỏ / không đổi; hệ thống chỉ gán vai trò
 * và ghi phạm vi khi CHÍNH NGƯỜI DÙNG bấm 'Xác nhận' ở đây. Token hết hạn sau 15 phút và
 * backend kiểm lại quyền / phạm vi / chống tự nâng quyền tại thời điểm bấm.
 * Mọi dòng «không đổi» thì không có nút xác nhận — tài khoản đã đúng bộ.
 */
export function AccountSetupProposalCard({
  proposal,
  onDismiss,
  onNavigate,
}: AccountSetupProposalCardProps) {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState<ConfirmAccountSetupResult | null>(null)

  const handleConfirm = async () => {
    setSaving(true)
    try {
      setDone(await assistantApi.confirmAccountSetup(proposal.confirm_token))
    } catch {
      // Token hết hạn / mất quyền / bị chốt chống tự nâng quyền — tầng API đã toast lỗi,
      // thẻ giữ nguyên để người dùng đọc lại đề xuất rồi tự bỏ qua.
    } finally {
      setSaving(false)
    }
  }

  const openPermissions = (url: string) => {
    onNavigate?.()
    navigate(url)
  }

  if (done) {
    const what = done.updated.length ? done.updated.join(', ') : 'không có gì đổi'
    return (
      <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
        <p className="flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
          <Check className="size-4 shrink-0 text-success" />
          <span className="truncate">
            Bộ tài khoản {done.target_label}: {what}. Vai trò hiện có: {done.roles.join(', ')}.
          </span>
        </p>
        <Button size="sm" variant="outline" className="shrink-0" onClick={() => openPermissions(done.url)}>
          Mở phân quyền
        </Button>
      </div>
    )
  }

  const nothingToChange = proposal.changed === 0
  const { employee } = proposal

  return (
    <div className="border-t bg-muted/40 px-4 py-2.5">
      <div className="flex items-center gap-1.5 text-xs font-medium">
        <ShieldCheck className="size-3.5 text-primary" />
        <span>
          {nothingToChange ? 'Bộ tài khoản đã đúng' : 'Đề xuất lập bộ tài khoản'}: {proposal.target_label}
          {employee.department ? (
            <span className="font-normal text-muted-foreground"> ({employee.department})</span>
          ) : null}
        </span>
      </div>

      <ul className="mt-1.5 space-y-1">
        {proposal.lines.map((line) => (
          <li
            key={`${line.kind}:${line.role_code}:${line.label}`}
            className={cn('flex items-center gap-1.5 text-xs', line.status === 'không đổi' && 'opacity-70')}
          >
            <LineStatusIcon status={line.status} />
            <span className={cn('min-w-0 break-words', line.status === 'bỏ' && 'line-through')}>
              {line.label}
            </span>
            <span className="shrink-0 text-muted-foreground">· {line.status}</span>
          </li>
        ))}
      </ul>

      {proposal.warnings.length ? (
        <ul className="mt-1.5 space-y-1">
          {proposal.warnings.map((warning) => (
            <li key={warning} className="flex items-start gap-1.5 text-xs text-warning">
              <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
              <span className="min-w-0 break-words">{warning}</span>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-2 flex items-center justify-end gap-2">
        <Button type="button" size="sm" variant="ghost" disabled={saving} onClick={onDismiss}>
          <X />
          {nothingToChange ? 'Đóng' : 'Bỏ qua'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={() => openPermissions(proposal.url)}
        >
          Mở phân quyền
        </Button>
        {nothingToChange ? null : (
          <Button type="button" size="sm" disabled={saving} onClick={() => void handleConfirm()}>
            {saving ? <Loader2 className="animate-spin" /> : <Check />}
            Xác nhận
          </Button>
        )}
      </div>
    </div>
  )
}
