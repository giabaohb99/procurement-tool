import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import type { WorkRosterCell } from '../types/work-roster'
import { describeRosterCell } from '../utils/work-roster-cell'

interface WorkRosterCellViewProps {
  cell: WorkRosterCell | undefined
  /** Ô tháng: một ký tự, chỉ ngoại lệ mới có chữ. `false` = ô tuần có chữ ngắn. */
  compact?: boolean
  /** Tiền tố tooltip, thường là tên nhân sự — ô nhỏ không tự nói được ai/ngày nào. */
  label?: string
}

/**
 * Một ô của lưới «Xem lịch». Nguyên tắc: NGOẠI LỆ NỔI, NGÀY THƯỜNG LÙI.
 *
 * · Đi làm bình thường: không nền, không khung (tuần: giờ làm chữ mờ nhỏ).
 * · Nghỉ theo lịch: nền sọc mờ; Lễ: nền đỏ nhạt (chữ «Lễ» chỉ ở ô tuần).
 * · Nghỉ phép ĐÃ DUYỆT: thẻ đặc màu info lọt trong ô; CHỜ DUYỆT: thẻ viền nét đứt, nền nhạt.
 * · Nghỉ nửa buổi: thẻ chỉ phủ nửa ô — TRÁI = buổi sáng, PHẢI = buổi chiều.
 * · Ô có đơn nghỉ là link sang `/hr/leave-requests/:id`.
 *
 * ⚠️ Chữ nhìn thấy được ẩn khỏi trình đọc màn hình (`aria-hidden`) và thay bằng
 * một câu đầy đủ `sr-only` — «P» hay «S» đọc ra chẳng nói được gì.
 */
export function WorkRosterCellView({ cell, compact = false, label }: WorkRosterCellViewProps) {
  const view = describeRosterCell(cell)
  const tooltip = label ? `${label} — ${view.description}` : view.description
  const isLeave = view.state === 'leave' || view.state === 'partial'
  const isPartial = view.state === 'partial'
  const visible = view.state === 'unknown' ? '' : compact ? view.glyph : view.shortLabel || view.glyph

  const className = cn(
    'relative flex w-full items-center justify-center overflow-hidden text-xs outline-none',
    compact ? 'h-8 text-[11px]' : 'h-10',
    view.state === 'off' && 'bg-muted',
    view.state === 'holiday' && 'bg-destructive/10',
    view.leaveRequestId !== null &&
      'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset hover:brightness-95',
  )

  const body = (
    <>
      {isLeave && (
        //  Thẻ nghỉ: cả ô, hoặc một nửa (trái = sáng, phải = chiều). Chữ nằm TRONG thẻ để đủ tương phản.
        <span
          aria-hidden
          className={cn(
            'absolute inset-y-0.5 flex items-center justify-center overflow-hidden rounded-sm px-0.5 font-medium',
            isPartial ? 'w-[calc(50%-2px)]' : 'inset-x-0.5',
            isPartial && (view.morningOff ? 'left-0.5' : 'right-0.5'),
            view.isPending
              ? 'border border-dashed border-info bg-info/10 text-info'
              : 'bg-leave-approved text-leave-approved-foreground',
            isPartial && !compact && 'text-[10px]',
          )}
        >
          <span className="truncate">{view.shortLabel && !compact ? view.shortLabel : view.glyph}</span>
        </span>
      )}
      {!isLeave && visible && (
        <span
          aria-hidden
          className={cn(
            'max-w-full truncate px-1 tabular-nums',
            view.state === 'working' ? 'text-[11px] text-muted-foreground' : 'text-muted-foreground',
            view.state === 'holiday' && 'font-medium text-destructive',
          )}
        >
          {visible}
        </span>
      )}
      <span className="sr-only">{tooltip}</span>
    </>
  )

  if (view.leaveRequestId !== null) {
    return (
      <Link to={appRoutes.hr.leaveRequestDetail(view.leaveRequestId)} title={tooltip} className={className}>
        {body}
      </Link>
    )
  }
  return (
    <div title={tooltip} className={className}>
      {body}
    </div>
  )
}
