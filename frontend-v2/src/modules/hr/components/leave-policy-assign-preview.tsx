import { AlertTriangle, Loader2 } from 'lucide-react'

import { Checkbox } from '@/shared/ui/checkbox'
import type { PolicyPreviewItem } from '../types/leave-policy'
import { formatPolicyRange, type LeaveTypeNameLookup } from '../utils/leave-policy-display'
import { LeavePolicyBalanceChanges } from './leave-policy-balance-changes'

interface LeavePolicyAssignPreviewProps {
  /** Chưa đủ ô để xem trước (chưa chọn người / chính sách / ngày). */
  ready: boolean
  isLoading: boolean
  /** Gọi xem trước lỗi (mạng / 4xx / 5xx) — khác hẳn "người này không có trong kết quả". */
  isError: boolean
  /** `undefined` khi đã gọi mà người đó không có trong kết quả (ngoài phạm vi / đã nghỉ việc). */
  item: PolicyPreviewItem | undefined
  closePrevious: boolean
  onClosePreviousChange: (value: boolean) => void
  typeName: LeaveTypeNameLookup
}

/**
 * Khối XEM TRƯỚC của hộp phân bổ một người (duoc-CR-717): chính sách hiện tại, lý do không phân bổ được,
 * ô "Kết thúc chính sách đang hiệu lực" (chỉ khi chồng ngày) và bảng hạn mức năm nay trước → sau.
 *
 * ⚠️ Ô "Kết thúc…" vẫn HIỆN sau khi tick dù xem trước lần hai không còn báo chồng ngày — ẩn đi là người
 * dùng không bỏ tick lại được nữa.
 */
export function LeavePolicyAssignPreview({
  ready,
  isLoading,
  isError,
  item,
  closePrevious,
  onClosePreviousChange,
  typeName,
}: LeavePolicyAssignPreviewProps) {
  if (!ready) {
    return (
      <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
        Chọn nhân sự, chính sách và ngày bắt đầu để xem hạn mức năm nay thay đổi thế nào.
      </p>
    )
  }
  if (isLoading) {
    return (
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Đang tính thử…
      </p>
    )
  }
  if (isError) {
    //  Review L4: lỗi gọi API trước đây rơi xuống nhánh "không tìm thấy nhân sự" — nói sai lý do.
    return (
      <p role="alert" className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 size-4 shrink-0" />
        Không tính thử được — thử đổi một ô hoặc mở lại hộp. Chưa tính thử thì chưa phân bổ được.
      </p>
    )
  }
  if (!item) {
    return (
      <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
        Không tìm thấy nhân sự này trong phạm vi của bạn, hoặc người đó đã nghỉ việc.
      </p>
    )
  }

  if (item.conflict === 'scope') {
    //  Dòng "ngoài phạm vi" của backend không có chính sách hiện tại / hạn mức — chỉ câu lý do là có nghĩa.
    return (
      <p role="alert" className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 size-4 shrink-0" />
        {item.conflict_message || 'Không phân bổ được cho người này (ngoài phạm vi của bạn, hoặc đã nghỉ việc).'}
      </p>
    )
  }

  const showClosePrevious = item.conflict === 'overlap' || closePrevious
  return (
    <div className="space-y-3">
      <p className="text-sm">
        <span className="text-muted-foreground">Chính sách hiện tại: </span>
        {item.current ? (
          <strong>
            {item.current.policy_name} ({formatPolicyRange(item.current.from, item.current.to)})
          </strong>
        ) : (
          <span>Chưa có — đang theo hạn mức của từng loại nghỉ</span>
        )}
      </p>

      {item.conflict && (
        <p role="alert" className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-2 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          {item.conflict === 'self'
            ? 'Không tự phân bổ chính sách cho chính mình — nhờ người khác có quyền làm giúp.'
            : item.conflict_message}
        </p>
      )}

      {showClosePrevious && (
        <label className="flex items-start gap-2 text-sm">
          <Checkbox
            checked={closePrevious}
            onCheckedChange={(v) => onClosePreviousChange(v === true)}
            className="mt-0.5"
          />
          <span>
            Kết thúc chính sách đang hiệu lực
            <span className="block text-xs text-muted-foreground">
              Đặt ngày kết thúc của lượt cũ = ngày bắt đầu mới trừ 1. Chỉ được khi lượt cũ bắt đầu TRƯỚC ngày này.
            </span>
          </span>
        </label>
      )}

      {!item.conflict && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium">Hạn mức quỹ phép năm nay</p>
          <LeavePolicyBalanceChanges changes={item.changes} typeName={typeName} />
        </div>
      )}
    </div>
  )
}
