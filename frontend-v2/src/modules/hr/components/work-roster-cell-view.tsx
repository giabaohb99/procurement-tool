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
  /**
   * Người xem xếp ca được (duoc-CR-761): ô thành NÚT mở hộp xếp ca, kể cả ô có đơn nghỉ (hộp xếp ca có link sang
   * đơn). Vắng = ô như cũ (ô có đơn nghỉ là link sang đơn).
   */
  onEdit?: () => void
  /** Câu đặt ĐẦU tooltip (vd "Đã có đơn nghỉ — sửa đơn trước" khi ô không xếp ca được). */
  hint?: string
}

/**
 * Một ô của lưới "Xem lịch". Nguyên tắc: NGOẠI LỆ NỔI, NGÀY THƯỜNG LÙI.
 *
 * · Đi làm bình thường: không nền, không khung (tuần: giờ làm chữ mờ nhỏ).
 * · Nghỉ theo lịch: nền sọc mờ; Lễ: nền đỏ nhạt (chữ "Lễ" chỉ ở ô tuần).
 * · Nghỉ phép ĐÃ DUYỆT: thẻ đặc màu info lọt trong ô; CHỜ DUYỆT: thẻ viền nét đứt, nền nhạt.
 * · Nghỉ nửa buổi: thẻ chỉ phủ nửa ô — TRÁI = buổi sáng, PHẢI = buổi chiều.
 * · Ô có đơn nghỉ là link sang `/hr/leave-requests/:id`.
 * · Ca XẾP THEO NGÀY (duoc-CR-761): thẻ đặc màu ca (tím) + chữ trắng, các khung giờ đủ HH:MM; nghỉ do xếp ca cũng
 *   nổi thẻ ca. Thẻ nghỉ phép vẽ ĐÈ lên thẻ ca, nên nghỉ nửa buổi vẫn thấy nửa còn lại là ca.
 *
 * ⚠️ Chữ nhìn thấy được ẩn khỏi trình đọc màn hình (`aria-hidden`) và thay bằng
 * một câu đầy đủ `sr-only` — "P" hay "S" đọc ra chẳng nói được gì.
 */
export function WorkRosterCellView({ cell, compact = false, label, onEdit, hint }: WorkRosterCellViewProps) {
  const view = describeRosterCell(cell)
  const described = label ? `${label} — ${view.description}` : view.description
  const tooltip = hint ? `${hint} · ${described}` : described
  const isLeave = view.state === 'leave' || view.state === 'partial'
  const isPartial = view.state === 'partial'
  const visible = view.state === 'unknown' ? '' : compact ? view.glyph : view.shortLabel || view.glyph
  const shiftLines = view.shiftLines.length > 0 ? view.shiftLines : [view.shortLabel]
  const clickable = onEdit !== undefined || view.leaveRequestId !== null

  const className = cn(
    'relative flex w-full items-center justify-center overflow-hidden text-xs outline-none',
    compact ? 'h-8 text-[11px]' : 'h-10',
    view.state === 'off' && !view.isShift && 'bg-muted',
    view.state === 'holiday' && 'bg-destructive/10',
    clickable && 'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset hover:brightness-95',
    onEdit && 'cursor-pointer hover:bg-accent/60',
  )

  const body = (
    <>
      {view.isShift && view.state !== 'holiday' && (
        //  Thẻ ca: cả ô. Ô tuần 1–2 dòng khung giờ (`shiftCellLines`), ô tháng một ký hiệu ("4h" / "N").
        <span
          aria-hidden
          className={cn(
            'absolute inset-0.5 flex flex-col items-center justify-center overflow-hidden rounded-sm bg-shift px-0.5 leading-tight text-shift-foreground tabular-nums',
            !compact && shiftLines.length > 1 && 'text-[10px]',
            !compact && shiftLines.length <= 1 && 'text-[11px]',
          )}
        >
          {compact ? (
            <span className="truncate">{view.glyph}</span>
          ) : (
            shiftLines.map((line, i) => (
              <span key={i} className="max-w-full truncate">
                {line}
              </span>
            ))
          )}
        </span>
      )}
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
      {!isLeave && !(view.isShift && view.state !== 'holiday') && visible && (
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

  if (onEdit) {
    return (
      <button type="button" onClick={onEdit} title={tooltip} className={className}>
        {body}
      </button>
    )
  }
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
