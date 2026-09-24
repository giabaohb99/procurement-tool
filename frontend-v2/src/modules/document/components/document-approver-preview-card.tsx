import { AlertTriangle, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { TimelineItem } from '@/shared/ui/timeline-item'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import type {
  ApprovalPreviewApprover,
  ApprovalPreviewCcStep,
  ApprovalPreviewResult,
  ApprovalPreviewStep,
} from '../types/approval-preview'

interface DocumentApproverPreviewCardProps {
  /** `undefined` = chưa có gì để xem trước (đang tải, hoặc chưa đủ Loại/Pháp nhân). */
  preview: ApprovalPreviewResult | undefined
  isLoading: boolean
  className?: string
}

const CAVEAT =
  'Dự kiến theo thông tin hiện tại — người duyệt thực tế chốt lúc gửi duyệt.'

const ONE_STEP_TAIL =
  'sẽ duyệt MỘT BƯỚC: người có quyền duyệt văn bản xem xét và bấm Duyệt/Từ chối trên trang chi tiết.'

/**
 * Thẻ «Người duyệt dự kiến» — xem trước luồng duyệt trên màn tạo văn bản / chi
 * tiết bản nháp (phase 01, duoc-CR-473). Component THUẦN HIỂN THỊ: nhận thẳng
 * kết quả đã gọi API (`useDocumentApprovalPreview`), không tự gọi hook — hai
 * màn dùng nó (tạo mới đang debounce theo form, chi tiết đọc từ bản ghi đã có)
 * có vòng đời dữ liệu khác nhau.
 */
export function DocumentApproverPreviewCard({
  preview,
  isLoading,
  className,
}: DocumentApproverPreviewCardProps) {
  return (
    <Card className={cn('print:hidden', className)}>
      <CardHeader>
        <CardTitle className="text-base">Người duyệt dự kiến</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <PreviewBody preview={preview} isLoading={isLoading} />
        <p className="text-xs text-muted-foreground italic">{CAVEAT}</p>
      </CardContent>
    </Card>
  )
}

function PreviewBody({
  preview,
  isLoading,
}: {
  preview: ApprovalPreviewResult | undefined
  isLoading: boolean
}) {
  if (!preview) {
    if (isLoading) return <PreviewSkeleton />
    return (
      <p className="text-sm text-muted-foreground">
        Chọn Loại văn bản và Pháp nhân để xem người duyệt dự kiến.
      </p>
    )
  }

  if (preview.mode === 'none') {
    return (
      <p className="text-sm text-muted-foreground">
        Loại văn bản này KHÔNG cần phê duyệt.
      </p>
    )
  }

  if (preview.mode === 'legacy') {
    return (
      <p className="text-sm text-muted-foreground">
        {preview.engine_enabled
          ? `Chưa khai luồng phê duyệt nào khớp — ${ONE_STEP_TAIL}`
          : `Bộ máy luồng nhiều bước đang TẮT cho văn bản — ${ONE_STEP_TAIL}`}
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {preview.flow_name && (
        <Badge variant="outline" className="font-normal">
          {preview.flow_name}
        </Badge>
      )}
      {preview.steps.length > 0 && (
        <ol className="flex flex-col">
          {preview.steps.map((step, index) => (
            <TimelineItem
              key={step.seq}
              marker={<StepMarker seq={step.seq} unresolved={Boolean(step.unresolved_reason)} />}
              last={index === preview.steps.length - 1}
            >
              <StepBody step={step} />
            </TimelineItem>
          ))}
        </ol>
      )}
      <CcList cc={preview.cc} />
    </div>
  )
}

function StepMarker({ seq, unresolved }: { seq: number; unresolved: boolean }) {
  return (
    <span
      className={cn(
        'grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold',
        unresolved ? 'bg-destructive/15 text-destructive' : 'bg-primary/10 text-primary',
      )}
      aria-hidden="true"
    >
      {seq}
    </span>
  )
}

/**
 * Nội dung một chặng — bốn nhánh loại trừ nhau, ĐÚNG theo thứ tự backend trả:
 * có người duyệt (kèm ghi chú dự phòng nếu có) → chặng FIELD chưa chọn → chặng
 * tự động qua vì trùng người → chặng KẸT (không tìm được ai, phiếu sẽ dừng).
 */
function StepBody({ step }: { step: ApprovalPreviewStep }) {
  return (
    <div className="space-y-1.5 pb-1">
      <div className="flex flex-wrap items-baseline gap-x-2">
        <span className="text-sm font-medium">{step.name || `Chặng ${step.seq}`}</span>
        {step.rule_label && (
          <span className="text-xs text-muted-foreground">{step.rule_label}</span>
        )}
      </div>

      {step.approvers.length > 0 ? (
        <>
          <ApproverList approvers={step.approvers} />
          {step.fallback_used && step.note && <StepNote tone="warning">{step.note}</StepNote>}
        </>
      ) : step.pending_field ? (
        <StepNote tone="muted">{step.unresolved_reason}</StepNote>
      ) : step.note ? (
        <StepNote tone="muted">{step.note}</StepNote>
      ) : (
        step.unresolved_reason && <StepNote tone="danger">{step.unresolved_reason}</StepNote>
      )}
    </div>
  )
}

function StepNote({ tone, children }: { tone: 'warning' | 'muted' | 'danger'; children: ReactNode }) {
  const Icon = tone === 'danger' ? AlertTriangle : Info
  return (
    <p
      className={cn(
        'flex items-center gap-1 text-xs',
        tone === 'danger' && 'font-medium text-destructive',
        tone === 'warning' && 'text-amber-600 dark:text-amber-500',
        tone === 'muted' && 'text-muted-foreground',
      )}
    >
      <Icon className="size-3.5 shrink-0" />
      {children}
    </p>
  )
}

function ApproverList({ approvers }: { approvers: ApprovalPreviewApprover[] }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {approvers.map((approver) => (
        <li key={approver.employee_id} className="flex items-center gap-2">
          <Avatar size="sm">
            <AvatarFallback>{nameInitials(approver.name)}</AvatarFallback>
          </Avatar>
          <span className="text-sm">
            {approver.name}
            {approver.position && (
              <span className="text-muted-foreground"> · {approver.position}</span>
            )}
          </span>
        </li>
      ))}
    </ul>
  )
}

function CcList({ cc }: { cc: ApprovalPreviewCcStep[] }) {
  const names = cc.flatMap((step) => step.approvers.map((approver) => approver.name)).filter(Boolean)
  if (names.length === 0) return null

  return (
    <p className="text-xs text-muted-foreground">
      <span className="font-medium text-foreground">Nhận bản sao: </span>
      {names.join(', ')}
    </p>
  )
}

function PreviewSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  )
}
