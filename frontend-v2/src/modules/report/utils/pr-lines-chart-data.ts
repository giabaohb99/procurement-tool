import { PR_LINE_STATUS } from '@/shared/constants/statuses'
import type { ChartDatum } from '@/shared/ui/chart'

import type { PrLinesSummary } from '../types/report-summary'
import { fillYearMonths, orderByLifecycle } from './chart-series'

/** Một cột tháng của biểu đồ chồng «đã đặt / chưa đặt». */
export interface PrLinesMonthPoint {
  /** "T1".."T12". */
  label: string
  /** Dòng đã rời trạng thái chưa đặt (đã đặt · đã nhận · hoàn thành). */
  handled: number
  /** Dòng CHƯA ĐƯỢC ĐẶT — thứ báo cáo này sinh ra để soi. */
  idle: number
}

/** 12 tháng của `year`, tách dòng đã đặt / chưa đặt. */
export function fillPrLinesMonths(
  year: number,
  byMonth: PrLinesSummary['by_month'],
): PrLinesMonthPoint[] {
  return fillYearMonths(year, byMonth, ['lines', 'idle_lines'] as const).map((m) => ({
    label: m.label,
    //  Chặn âm: dữ liệu lệch (idle > lines) không được vẽ ra khúc cột âm.
    handled: Math.max(0, m.lines - m.idle_lines),
    idle: m.idle_lines,
  }))
}

/** Số dòng theo tiến độ, xếp theo vòng đời dòng YCMH (hủy đứng cuối). */
export function orderPrLineStatuses(byStatus: PrLinesSummary['by_line_status']): ChartDatum[] {
  return orderByLifecycle(
    PR_LINE_STATUS,
    byStatus.map((s) => ({ code: s.code, value: s.lines })),
  )
}

/** Tên NSTM để vẽ: tên hồ sơ → mã → «(Chưa gán NSTM)» khi dòng chưa giao ai. */
export function labelAssignee(a: { code: string; name: string }): string {
  return a.name || a.code || '(Chưa gán NSTM)'
}
