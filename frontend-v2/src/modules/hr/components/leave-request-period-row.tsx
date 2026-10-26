import { X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { LeavePeriodValue } from '../utils/leave-form-values'
import { LeaveDateSessionField } from './leave-date-session-field'

interface LeaveRequestPeriodRowProps {
  index: number
  period: LeavePeriodValue
  /** Đơn có từ hai khoảng trở lên — hàng mới có khung, tiêu đề, số ngày riêng và nút bỏ. */
  multi: boolean
  /** Số ngày của riêng hàng này; `undefined` = đang tính hoặc chưa tính được. */
  days?: number
  /** Hàng chồng ngày với một hàng khác (kiểm sớm ở giao diện, backend vẫn là chốt cuối). */
  overlapping: boolean
  /** Hai ô giờ — chỉ truyền khi đơn MỘT khoảng đang khai «Theo giờ». */
  fromTime?: string
  toTime?: string
  onDateChange: (key: 'from_date' | 'to_date', value: string) => void
  onSessionChange: (key: 'from_session' | 'to_session', value: number) => void
  onTimeChange: (key: 'from_time' | 'to_time', value: string) => void
  onRemove: () => void
}

/**
 * MỘT khoảng ngày trên form đơn nghỉ (duoc-CR-683).
 *
 * Đơn một khoảng dựng Y HỆT trước đây: hai ô «Từ ngày» · «Đến ngày» nằm trần trong lưới của
 * form, cùng nhãn và cùng tên ô buổi («Buổi bắt đầu» · «Buổi kết thúc»). Chỉ từ hai khoảng
 * mới bọc khung, có tiêu đề «Khoảng ngày N», số ngày của khoảng và nút bỏ — người dùng đơn
 * thường không phải đọc thêm chữ nào.
 */
export function LeaveRequestPeriodRow({
  index,
  period,
  multi,
  days,
  overlapping,
  fromTime,
  toTime,
  onDateChange,
  onSessionChange,
  onTimeChange,
  onRemove,
}: LeaveRequestPeriodRowProps) {
  const suffix = multi ? ` khoảng ${index + 1}` : ''
  const rowLabel = multi ? `Khoảng ngày ${index + 1}` : undefined
  const reversed = Boolean(period.from_date && period.to_date && period.to_date < period.from_date)

  const fields = (
    <>
      {/*  Hai đầu ngày GIỮ NGUYÊN khi chọn «Theo giờ», chỉ mọc thêm ô giờ: nghỉ *từ 14:00
           ngày 07 đến 10:00 ngày 09* là tờ đơn có thật. */}
      <LeaveDateSessionField
        label="Từ ngày"
        rowLabel={rowLabel}
        date={period.from_date}
        session={period.from_session}
        sessionLabel={`Buổi bắt đầu${suffix}`}
        time={fromTime}
        timeLabel="Từ giờ"
        hourlyDisabled={multi}
        onDateChange={(v) => onDateChange('from_date', v)}
        onSessionChange={(v) => onSessionChange('from_session', v)}
        onTimeChange={(v) => onTimeChange('from_time', v)}
      />
      <LeaveDateSessionField
        label="Đến ngày"
        rowLabel={rowLabel}
        date={period.to_date}
        session={period.to_session}
        sessionLabel={`Buổi kết thúc${suffix}`}
        time={toTime}
        timeLabel="Đến giờ"
        hourlyDisabled={multi}
        onDateChange={(v) => onDateChange('to_date', v)}
        onSessionChange={(v) => onSessionChange('to_session', v)}
        onTimeChange={(v) => onTimeChange('to_time', v)}
      />
    </>
  )

  const problems = (
    <>
      {reversed && (
        <p className="text-xs text-destructive md:col-span-2">
          «Đến ngày» phải từ «Từ ngày» trở đi.
        </p>
      )}
      {overlapping && (
        <p className="text-xs text-destructive md:col-span-2">
          Khoảng này chồng ngày với một khoảng khác — các khoảng không được trùng ngày.
        </p>
      )}
    </>
  )

  if (!multi) {
    return (
      <>
        {fields}
        {problems}
      </>
    )
  }

  return (
    <div
      className={cn(
        'space-y-3 rounded-md border px-3 py-2.5 md:col-span-2',
        overlapping && 'border-destructive/60',
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">
          {`Khoảng ngày ${index + 1}`}
          {typeof days === 'number' && (
            <span className="font-normal text-muted-foreground tabular-nums">{` · ${days} ngày`}</span>
          )}
        </span>
        {/*  `type="button"`: nút nằm trong `<form>` của trang, thiếu là bấm «Bỏ» thành LƯU. */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8"
          aria-label={`Bỏ khoảng ngày ${index + 1}`}
          onClick={onRemove}
        >
          <X className="size-4" />
        </Button>
      </div>
      <div className="grid items-start gap-x-4 gap-y-3 md:grid-cols-2">
        {fields}
        {problems}
      </div>
    </div>
  )
}
