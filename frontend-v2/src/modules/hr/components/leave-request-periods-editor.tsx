import { Plus } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { LEAVE_SESSION, MAX_LEAVE_PERIODS } from '../types/leave'
import { isHourlyForm, type LeaveFormValues, type LeavePeriodValue } from '../utils/leave-form-values'
import { addDaysISO, overlappingPeriodIndexes } from '../utils/leave-periods'
import { LeaveRequestPeriodRow } from './leave-request-period-row'

type PeriodsPatch = Partial<Pick<LeaveFormValues, 'periods' | 'from_time' | 'to_time'>>

interface LeaveRequestPeriodsEditorProps {
  periods: LeavePeriodValue[]
  fromTime: string
  toTime: string
  /** Số ngày từng hàng, THEO THỨ TỰ HÀNG trên form; phần tử `undefined` = chưa tính được. */
  rowDays?: (number | undefined)[]
  totalDays?: number
  /** Câu lỗi backend trả lúc ước lượng (vắt năm, chồng ngày…) — chỉ có ở đơn nhiều khoảng. */
  estimateError?: string
  onChange: (patch: PeriodsPatch) => void
}

/**
 * Danh sách KHOẢNG NGÀY của đơn nghỉ + nút "+ Thêm khoảng ngày" (duoc-CR-683).
 *
 * Trả về các phần tử con của LƯỚI hai cột của form (không tự bọc lưới): đơn một khoảng nhờ
 * vậy vẫn là hai ô "Từ ngày" · "Đến ngày" đứng cạnh nhau như trước.
 *
 * Luật (khớp `request_periods.check_*` ở backend, backend vẫn là chốt cuối):
 * - nghỉ THEO GIỜ chỉ một khoảng → ẩn nút thêm, và từ hai khoảng thì mục "Theo giờ" bị khóa;
 * - tối đa `MAX_LEAVE_PERIODS` khoảng;
 * - các khoảng không chồng ngày — báo đỏ ngay dưới hàng, không đợi bấm Lưu;
 * - nhiều khoảng phải cùng một năm — để backend nói (câu 422 hiện ở cuối danh sách).
 */
export function LeaveRequestPeriodsEditor({
  periods,
  fromTime,
  toTime,
  rowDays,
  totalDays,
  estimateError,
  onChange,
}: LeaveRequestPeriodsEditorProps) {
  const multi = periods.length > 1
  const hourly = isHourlyForm({ periods })
  const overlaps = overlappingPeriodIndexes(periods)
  const full = periods.length >= MAX_LEAVE_PERIODS

  const setRow = (index: number, patch: Partial<LeavePeriodValue>, extra: PeriodsPatch = {}) =>
    onChange({ periods: periods.map((p, i) => (i === index ? { ...p, ...patch } : p)), ...extra })

  /**
   * Đổi ô BUỔI. Chọn "Theo giờ" ở một đầu thì đầu kia theo luôn (backend đòi hai ô buổi
   * giống nhau). Bỏ "Theo giờ" thì XÓA khoảng giờ: giữ lại là lưu một khoảng giờ mà tờ đơn
   * không còn khai theo giờ nữa.
   */
  const setSession = (index: number, which: 'from_session' | 'to_session', next: number) => {
    const other = which === 'from_session' ? 'to_session' : 'from_session'
    const current = periods[index]
    if (next === LEAVE_SESSION.HOURLY) {
      setRow(index, { [which]: next, [other]: next })
      return
    }
    const leavingHourly = current[other] === LEAVE_SESSION.HOURLY
    const wasHourly = current[which] === LEAVE_SESSION.HOURLY || leavingHourly
    setRow(
      index,
      { [which]: next, ...(leavingHourly ? { [other]: LEAVE_SESSION.FULL } : null) },
      wasHourly ? { from_time: '', to_time: '' } : {},
    )
  }

  //  Hàng mới bắt đầu NGAY SAU ngày cuối của hàng cuối, cả ngày → cả ngày: thứ người dùng
  //  gần như luôn muốn là "đợt sau", và mặc định trùng ngày thì vừa bấm đã ăn báo đỏ.
  const addRow = () => {
    const last = periods[periods.length - 1]
    const base = last?.to_date || last?.from_date
    const start = base ? addDaysISO(base, 1) : ''
    onChange({
      periods: [
        ...periods,
        { from_date: start, from_session: LEAVE_SESSION.FULL, to_date: start, to_session: LEAVE_SESSION.FULL },
      ],
    })
  }

  const removeRow = (index: number) => onChange({ periods: periods.filter((_, i) => i !== index) })

  return (
    <>
      {periods.map((period, index) => (
        <LeaveRequestPeriodRow
          //  Hàng không có id ổn định (form mới), chỉ số là đủ: bỏ hàng giữa thì các ô
          //  có kiểm soát nhận đúng giá trị mới từ `periods`.
          key={index}
          index={index}
          period={period}
          multi={multi}
          days={rowDays?.[index]}
          overlapping={overlaps.has(index)}
          fromTime={hourly && !multi ? fromTime : undefined}
          toTime={hourly && !multi ? toTime : undefined}
          onDateChange={(key, v) => setRow(index, { [key]: v })}
          onSessionChange={(key, v) => setSession(index, key, v)}
          onTimeChange={(key, v) => onChange({ [key]: v })}
          onRemove={() => removeRow(index)}
        />
      ))}

      {!hourly && (
        <div className="space-y-1 md:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="-ml-2 h-7 text-primary"
              disabled={full}
              onClick={addRow}
            >
              <Plus className="size-4" />
              Thêm khoảng ngày
            </Button>
            {multi && (
              <span className="text-sm font-medium tabular-nums">
                {typeof totalDays === 'number'
                  ? `Cộng ${periods.length} khoảng: ${totalDays} ngày`
                  : `${periods.length} khoảng ngày`}
              </span>
            )}
          </div>
          {full && (
            <p className="text-xs text-muted-foreground">{`Tối đa ${MAX_LEAVE_PERIODS} khoảng ngày.`}</p>
          )}
          {multi && (
            <p className="text-xs text-muted-foreground">Nghỉ theo giờ chỉ khai một khoảng ngày.</p>
          )}
          {multi && estimateError && <p className="text-xs text-destructive">{estimateError}</p>}
        </div>
      )}
    </>
  )
}
