import { CalendarDays, ChevronDown } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'

import {
  REPORT_PRESETS,
  resolveLocalCompareRange,
  resolveLocalPresetRange,
  type ReportPresetKey,
} from '../config/report-period-presets'
import type { ReportCompareMode, ReportPeriod } from '../types/report-analytics'
import { formatReportRange as rangeLabel } from '../utils/format-report-range'
import { ReportCompareToggle } from './report-compare-toggle'
import { ReportPeriodPopoverPresets } from './report-period-popover-presets'
import { ReportPeriodRangeCalendar } from './report-period-range-calendar'

export interface ReportPeriodInput {
  preset: ReportPresetKey
  from: string
  to: string
  compare: ReportCompareMode
}

interface ReportPeriodControlProps extends ReportPeriodInput {
  /** Kỳ ĐÃ TÍNH LẠI trả về cùng dữ liệu — nguồn thật của khoảng ngày hiện trên nút. */
  period?: ReportPeriod
  /** Ghi CẢ preset/khoảng ngày/so sánh trong MỘT lượt — `filters.applyPeriod`. */
  onApply: (input: ReportPeriodInput) => void
}

/**
 * Ô "Kỳ báo cáo" kiểu Haravan — MỘT nút bấm (preset đậm + khoảng ngày mờ) thay
 * cho cặp ô Select "Kỳ" / "So sánh" cũ. Bấm mở popover: cột trái 10 preset cố
 * định, cột phải lịch 2 tháng + segment "So sánh với" + "Hủy"/"Áp dụng".
 *
 * Mọi lựa chọn trong popover chỉ đổi bản NHÁP cục bộ (state của chính component
 * này) — ghi lên URL đúng MỘT lần khi bấm "Áp dụng" (`onApply`), tránh bẫy hai
 * lượt `setSearchParams` chồng nhau đã ghi ở `useReportFilters.applyPeriod`.
 */
export function ReportPeriodControl({
  preset,
  from,
  to,
  compare,
  period,
  onApply,
}: ReportPeriodControlProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<ReportPeriodInput>({ preset, from, to, compare })

  const appliedFrom =
    period?.date_from || (preset === 'custom' ? from : resolveLocalPresetRange(preset)[0])
  const appliedTo =
    period?.date_to || (preset === 'custom' ? to : resolveLocalPresetRange(preset)[1])
  const presetText = REPORT_PRESETS.find((p) => p.key === preset)?.label ?? ''

  const compareRange =
    compare !== 'none' && period?.compare_from && period?.compare_to
      ? [period.compare_from, period.compare_to]
      : resolveLocalCompareRange(appliedFrom, appliedTo, compare)
  const compareText =
    compare === 'none'
      ? 'Không so sánh'
      : compareRange
        ? `So với ${rangeLabel(compareRange[0], compareRange[1])}`
        : ''

  const draftRange =
    draft.preset === 'custom' ? [draft.from, draft.to] : resolveLocalPresetRange(draft.preset)
  //  Chỉ "Tùy chọn khoảng ngày" mới cần đủ hai đầu — mọi preset khác backend tự
  //  tính, nháp luôn coi như đủ. Thiếu chốt này thì bấm MỘT ngày rồi "Áp dụng"
  //  ngay sẽ gửi `to: ''`, và `applyPeriod` mồi lại bằng khoảng "Tùy chọn" mặc
  //  định — một khoảng ngày người dùng không hề chọn (cùng bẫy `DateRangePicker`
  //  đã vá, xem `shared/ui/date-range-picker.tsx`).
  const canApply = draft.preset !== 'custom' || (draft.from !== '' && draft.to !== '')

  function handleOpenChange(next: boolean) {
    //  Nạp lại bản nháp mỗi lần MỞ (không phải mỗi lần đóng) — bấm ra ngoài =
    //  hủy, lần mở sau phải thấy đúng kỳ đang áp dụng, không phải nháp dở dang.
    if (next) setDraft({ preset, from, to, compare })
    setOpen(next)
  }

  function selectPreset(next: ReportPresetKey) {
    if (next === 'custom') {
      //  Mồi một khoảng CÓ SẴN (giữ nguyên nếu đang chỉnh dở, không thì lấy
      //  khoảng của preset đang chọn) — tránh lịch trống trơn không biết bấm đâu.
      setDraft((d) => ({
        ...d,
        preset: 'custom',
        from: d.from || draftRange[0],
        to: d.to || draftRange[1],
      }))
      return
    }
    setDraft((d) => ({ ...d, preset: next }))
  }

  function pickDay(nextFrom: string, nextTo: string) {
    setDraft((d) => ({ ...d, preset: 'custom', from: nextFrom, to: nextTo }))
  }

  function apply() {
    onApply(draft)
    setOpen(false)
  }

  return (
    <div className="flex flex-col gap-0.5">
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            className="h-9 min-w-0 justify-start gap-2 px-3 font-normal"
          >
            <CalendarDays className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <span className="truncate">
              <span className="font-semibold text-foreground">{presetText}</span>
              <span className="ml-1.5 text-muted-foreground max-sm:hidden">
                {rangeLabel(appliedFrom, appliedTo)}
              </span>
            </span>
            <ChevronDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          </Button>
        </PopoverTrigger>

        <PopoverContent
          align="start"
          //  Radix chỉ khóa cuộn của TRANG NỀN khi popover mở
          //  (`data-scroll-locked` trên `<body>`), KHÔNG tự co nội dung popover
          //  vừa màn hình. Khổ điện thoại: hai tháng lịch xếp dọc + hàng preset +
          //  segment so sánh + chân "Hủy"/"Áp dụng" dễ cao hơn khoảng trống THẬT
          //  còn lại phía dưới nút bấm (khác 85vh cố định — nút nằm càng gần đáy
          //  màn hình thì khoảng trống thật càng hẹp hơn 85% chiều cao màn hình).
          //  `--radix-popover-content-available-height` là biến Radix tự tính
          //  đúng khoảng trống đó (cùng cách `SelectContent` đã dùng ở
          //  `shared/ui/select.tsx`) — thiếu chốt này thì chân nút bị đẩy khuất
          //  dưới mép màn hình mà không cách nào cuộn tới (nền đã khóa cuộn).
          className="max-h-[min(85vh,var(--radix-popover-content-available-height))] w-[min(94vw,760px)] overflow-y-auto p-0"
        >
          <div className="flex flex-col sm:flex-row">
            <ReportPeriodPopoverPresets value={draft.preset} onSelect={selectPreset} />

            <div className="flex min-w-0 flex-1 flex-col">
              <ReportPeriodRangeCalendar from={draftRange[0]} to={draftRange[1]} onPick={pickDay} />

              <div className="border-t p-3">
                <p className="mb-2 text-sm font-medium text-foreground">So sánh với</p>
                <ReportCompareToggle
                  value={draft.compare}
                  onChange={(next) => setDraft((d) => ({ ...d, compare: next }))}
                />
              </div>

              {/*  `sticky bottom-0` — khổ điện thoại nội dung phía trên (lịch 2
                   tháng xếp dọc) hay cao hơn viewport; ghim chân nút để luôn
                   bấm được mà không phải cuộn dò, `bg-popover` che phần đang
                   cuộn qua bên dưới nó (cùng lý do nền phải ĐỤC ở `docs/ui/table.md`). */}
              <div className="sticky bottom-0 flex items-center justify-end gap-2 border-t bg-popover p-3">
                <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)}>
                  Hủy
                </Button>
                <Button type="button" size="sm" disabled={!canApply} onClick={apply}>
                  Áp dụng
                </Button>
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      <p className="pl-1 text-xs text-muted-foreground">{compareText}</p>
    </div>
  )
}
