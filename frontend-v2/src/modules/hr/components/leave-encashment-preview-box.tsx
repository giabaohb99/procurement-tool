import { Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import {
  formatEncashDays,
  LEAVE_ENCASHMENT_REASON,
  type LeaveEncashmentPreview,
} from '../types/leave-encashment'

interface LeaveEncashmentPreviewBoxProps {
  preview?: LeaveEncashmentPreview
  isLoading: boolean
  /** Câu lỗi backend trả cho `/preview` (422 thiếu ngày nghỉ việc, quỹ năm trước chưa có…). */
  errorMessage?: string
  /** Bấm "Dùng hết" — điền đúng số được thanh toán vào ô số ngày. Vắng = không có nút. */
  onUseAll?: (days: number) => void
}

/**
 * Dải "SỐ NGÀY ĐƯỢC THANH TOÁN" trên form phiếu (duoc-CR-719, mục 4 của phase 04) — bố cục phẳng: một dải nền xám nhạt,
 * mỗi dòng một cặp nhãn : số, đi từ số dư tới kết quả để người lập không phải tự trừ.
 *
 * Luật tính (D5/D6) do BACKEND làm (`encashment_math`); dải này chỉ đọc lại từng số backend trả, KHÔNG tự tính lại.
 *  · Cuối năm: số dùng được − phần mang sang chưa dùng − số phải giữ lại, rồi kẹp theo trần năm còn lại.
 *  · Nghỉ việc: trả hết số chưa nghỉ, không giữ lại, không trần (Điều 113 khoản 3 Bộ luật Lao động).
 */
export function LeaveEncashmentPreviewBox(props: LeaveEncashmentPreviewBoxProps) {
  return (
    <div aria-label="Số ngày được thanh toán" role="group" className="rounded-md bg-muted/50 px-3 py-2.5 text-sm">
      <PreviewBody {...props} />
    </div>
  )
}

function PreviewBody({ preview, isLoading, errorMessage, onUseAll }: LeaveEncashmentPreviewBoxProps) {
  if (isLoading) {
    return (
      <p className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Đang tính số ngày…
      </p>
    )
  }
  if (errorMessage) {
    return (
      <p role="alert" className="text-destructive">
        {errorMessage}
      </p>
    )
  }
  if (!preview) {
    return <p className="text-muted-foreground">Chọn loại nghỉ để xem số ngày được thanh toán.</p>
  }
  if (!preview.has_balance) {
    return (
      <p className="text-muted-foreground">
        Chưa có quỹ phép năm {preview.balance_year} của loại nghỉ này nên chưa có ngày nào để thanh toán.
      </p>
    )
  }

  const isResignation = preview.reason_kind === LEAVE_ENCASHMENT_REASON.RESIGNATION
  return (
    <div className="space-y-2">
      <dl className="space-y-1">
        <Row label={`Số ngày còn dùng được năm ${preview.balance_year}`} value={days(preview.available)} />
        {!isResignation && preview.unused_carried > 0 && (
          <Row label="Phần mang sang từ năm trước chưa dùng (không thanh toán)" value={`− ${days(preview.unused_carried)}`} />
        )}
        {!isResignation && preview.non_encashable_days > 0 && (
          <Row label="Phải giữ lại theo loại nghỉ" value={`− ${days(preview.non_encashable_days)}`} />
        )}
        {!isResignation && preview.cap_remaining !== null && (
          <Row
            label={`Trần mỗi năm ${formatEncashDays(preview.max_encashable_days)} ngày, đã thanh toán ${formatEncashDays(preview.already_encashed)} ngày`}
            value={`còn ${days(preview.cap_remaining)}`}
          />
        )}
        {!isResignation && preview.cap_remaining === null && preview.already_encashed > 0 && (
          <Row label="Năm này đã thanh toán (loại nghỉ không đặt trần)" value={days(preview.already_encashed)} />
        )}
      </dl>
      {isResignation && (
        <p className="text-muted-foreground">
          Nghỉ việc: được thanh toán hết số ngày chưa nghỉ, kể cả phần mang sang, không giữ lại và không áp trần năm.
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/70 pt-2">
        <p>
          Được thanh toán tối đa{' '}
          <strong className="text-base tabular-nums">{formatEncashDays(preview.encashable)}</strong> ngày
          <span className="text-xs text-muted-foreground"> (làm tròn xuống theo nửa ngày)</span>
        </p>
        {onUseAll && preview.encashable > 0 && (
          <Button type="button" variant="outline" size="sm" onClick={() => onUseAll(preview.encashable)}>
            Dùng hết {formatEncashDays(preview.encashable)} ngày
          </Button>
        )}
      </div>
    </div>
  )
}

function days(value: number): string {
  return `${formatEncashDays(value)} ngày`
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="min-w-0 text-muted-foreground">{label}</dt>
      <dd className="shrink-0 font-medium tabular-nums">{value}</dd>
    </div>
  )
}
