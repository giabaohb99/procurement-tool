import { useMemo } from 'react'

import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { describeRosterCell, indexCellsByDate } from '../utils/work-roster-cell'
import { groupByDepartment, pickLeaveRowIds, summarizeRosterDay } from '../utils/work-roster-summary'
import type { WorkRosterMode } from '../utils/work-roster-range'
import { WorkRosterGridBody } from './work-roster-grid-body'
import { WorkRosterGridHeader, type WorkRosterColumnInfo } from './work-roster-grid-header'
import { rosterColumnsStyle, rosterRowHeight } from './work-roster-grid-layout'

interface WorkRosterGridProps {
  days: WorkRosterDay[]
  items: WorkRosterItem[]
  mode: WorkRosterMode
  todayISO: string
}

/**
 * Lưới nhân sự × ngày. Cột tên dính trái, đầu bảng dính trên; nhân sự gom theo phòng ban (thứ tự backend
 * đã xếp). Hàng có nghỉ phép dính theo từng đợt 3 hàng (xem `WorkRosterGridBody`). Hàng tổng «Nghỉ (trang
 * này)» tính trên các hàng ĐANG XEM (trang hiện tại), không phải cả công ty.
 *
 * Dựng bằng `div` + vai trò ARIA của bảng, không bằng `<table>` — lý do ở `work-roster-grid-layout.ts`.
 */
export function WorkRosterGrid({ days, items, mode, todayISO }: WorkRosterGridProps) {
  const compact = mode === 'month'
  const groups = useMemo(() => groupByDepartment(items), [items])
  const cellMaps = useMemo(() => items.map(indexCellsByDate), [items])
  const leaveIds = useMemo(() => pickLeaveRowIds(items, cellMaps, days), [items, cellMaps, days])
  const columns = useMemo<WorkRosterColumnInfo[]>(
    () =>
      days.map((d) => {
        //  Cột «đóng» = MỌI hàng đang xem đều nghỉ theo lịch / lễ → tiêu đề cũng sọc mờ cho thành dải.
        const closed =
          items.length > 0 &&
          cellMaps.every((m) => {
            const state = describeRosterCell(m.get(d.date)).state
            return state === 'off' || state === 'holiday'
          })
        return { date: d.date, closed, ...summarizeRosterDay(cellMaps, d.date) }
      }),
    [days, items, cellMaps],
  )

  return (
    <div className="max-h-[70dvh] min-h-0 overflow-auto rounded-md border bg-card">
      <div role="table" style={rosterColumnsStyle(mode, days.length)} className="w-max min-w-full text-sm">
        <WorkRosterGridHeader days={days} columns={columns} mode={mode} todayISO={todayISO} />
        <WorkRosterGridBody
          groups={groups}
          days={days}
          compact={compact}
          rowHeight={rosterRowHeight(mode)}
          todayISO={todayISO}
          leaveIds={leaveIds}
        />
      </div>
    </div>
  )
}
