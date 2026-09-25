import { ArrowRight, Info, ShieldCheck } from 'lucide-react'
import { Fragment } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import type { ApprovalPreviewResult, ApprovalPreviewStep } from '../types/approval-preview'

interface DocumentApproverPreviewLineProps {
  /** `undefined` = chưa có gì để xem trước (đang tải, hoặc chưa đủ Loại/Pháp nhân). */
  preview: ApprovalPreviewResult | undefined
  isLoading: boolean
  className?: string
}

const CAVEAT = 'Dự kiến theo thông tin hiện tại — người duyệt thực tế chốt lúc gửi duyệt.'

/**
 * «Người duyệt dự kiến» dạng MỘT DÒNG trong form tạo văn bản (chốt 24/09/2026 —
 * thay thẻ ghim ở cột phải, cột đó chiếm chỗ của form suốt ba bước). Dòng đọc
 * được ngay: «① Nguyễn A → ② Trần B, Lê C». Chặng chưa tìm ra người thì đỏ,
 * chặng còn chờ nhập ô nào đó thì mờ — đủ để người lập biết có vấn đề; chi
 * tiết từng chặng xem ở tab Phê duyệt (`DocumentApproverPreviewCard`).
 */
export function DocumentApproverPreviewLine({
  preview,
  isLoading,
  className,
}: DocumentApproverPreviewLineProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-x-2 gap-y-1 rounded-md border bg-muted/30 px-3 py-2 text-sm print:hidden',
        className,
      )}
    >
      <span className="flex shrink-0 items-center gap-1.5 font-medium">
        <ShieldCheck className="size-4 text-muted-foreground" />
        Người duyệt dự kiến:
      </span>
      <LineBody preview={preview} isLoading={isLoading} />
      <span title={CAVEAT} aria-label={CAVEAT} className="ml-auto shrink-0 text-muted-foreground">
        <Info className="size-3.5" />
      </span>
    </div>
  )
}

function LineBody({
  preview,
  isLoading,
}: {
  preview: ApprovalPreviewResult | undefined
  isLoading: boolean
}) {
  if (!preview) {
    if (isLoading) return <Skeleton className="h-4 w-48" />
    return <span className="text-muted-foreground">chọn Loại văn bản và Pháp nhân để xem</span>
  }
  if (preview.mode === 'none')
    return <span className="text-muted-foreground">Không cần phê duyệt</span>
  if (preview.mode === 'legacy') {
    return (
      <span className="text-muted-foreground">Duyệt một bước — người có quyền duyệt văn bản</span>
    )
  }
  if (preview.steps.length === 0)
    return <span className="text-muted-foreground">Luồng chưa có chặng nào</span>

  const ccNames = preview.cc
    .flatMap((step) => step.approvers.map((approver) => approver.name))
    .filter(Boolean)
  return (
    <>
      {preview.steps.map((step, index) => (
        <Fragment key={step.seq}>
          {index > 0 && (
            <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
          )}
          <StepChip step={step} />
        </Fragment>
      ))}
      {ccNames.length > 0 && (
        <span className="text-xs text-muted-foreground">· Nhận bản sao: {ccNames.join(', ')}</span>
      )}
    </>
  )
}

function StepChip({ step }: { step: ApprovalPreviewStep }) {
  const names = step.approvers.map((approver) => approver.name).join(', ')
  //  Không ra người mà KHÔNG phải vì còn chờ nhập một ô → lỗi cấu hình luồng, tô đỏ.
  const unresolved = !names && !step.pending_field && Boolean(step.unresolved_reason)
  const text = names || step.unresolved_reason || step.note || step.name || `Chặng ${step.seq}`
  return (
    <span
      title={step.name || undefined}
      className={cn(
        'inline-flex min-w-0 items-center gap-1.5',
        unresolved && 'font-medium text-destructive',
        !names && !unresolved && 'text-muted-foreground',
      )}
    >
      <span
        aria-hidden
        className={cn(
          'grid size-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold',
          unresolved ? 'bg-destructive/15 text-destructive' : 'bg-primary/10 text-primary',
        )}
      >
        {step.seq}
      </span>
      <span className="min-w-0">{text}</span>
    </span>
  )
}
