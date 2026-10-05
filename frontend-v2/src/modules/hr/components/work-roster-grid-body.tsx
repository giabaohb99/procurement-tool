import { Fragment } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import type { WorkRosterDepartmentGroup } from '../utils/work-roster-summary'
import { ROSTER_HEADER_HEIGHT, ROSTER_ROW_GRID, STICKY_LEAVE_SLOTS } from './work-roster-grid-layout'
import { WorkRosterRow } from './work-roster-grid-row'

interface WorkRosterGridBodyProps {
  groups: WorkRosterDepartmentGroup[]
  days: WorkRosterDay[]
  compact: boolean
  rowHeight: number
  todayISO: string
  leaveIds: ReadonlySet<number>
}

type Entry =
  | { kind: 'dept'; group: WorkRosterDepartmentGroup }
  | { kind: 'row'; item: WorkRosterItem; slot: number | null }

/**
 * Chia các hàng (kèm tiêu đề phòng ban) thành từng «ĐỢT»: một đợt mở đầu ở hàng có nghỉ thứ 1, 4, 7… và chứa
 * đúng 3 hàng có nghỉ cùng mọi hàng thường xen giữa. Mỗi đợt là một khung `div` riêng.
 */
function splitIntoBatches(groups: WorkRosterDepartmentGroup[], leaveIds: ReadonlySet<number>): Entry[][] {
  const batches: Entry[][] = [[]]
  let leaveCount = 0
  for (const group of groups) {
    batches[batches.length - 1].push({ kind: 'dept', group })
    for (const item of group.items) {
      let slot: number | null = null
      if (leaveIds.has(item.employee_id)) {
        slot = leaveCount % STICKY_LEAVE_SLOTS
        if (slot === 0 && leaveCount > 0) batches.push([])
        leaveCount += 1
      }
      batches[batches.length - 1].push({ kind: 'row', item, slot })
    }
  }
  return batches
}

/**
 * Thân lưới: hàng có nghỉ phép dính theo TỪNG ĐỢT 3 HÀNG, CHỈ bằng CSS.
 *
 * - Hàng có nghỉ thứ j (0..2) của đợt dính ở `đáy đầu bảng + j·H`.
 * - Hàng dính bị giới hạn trong khung đợt của nó, nên khi đợt sau cuộn tới, đáy khung đợt cũ ĐẨY các hàng dính
 *   lên. Để 3 hàng đi lên CÙNG LÚC như một khối (chứ không xẹp dần từng hàng), hàng j mang `margin-bottom`
 *   (2−j)·H — mép giới hạn của cả 3 trùng nhau — và một miếng đệm `margin-top` âm ngay sau nó trả lại đúng chỗ
 *   đó để bố cục không đổi.
 *
 * Đại ca chốt 05/10/2026: «3 row thì từ row 4 5 6 đẩy lên 1 lượt». Mọi bản dùng JS theo dõi cuộn trước đó
 * (chồng cuốn chiếu, chồng 3 ô) đều bị chê giật/loạn vì JS chạy SAU khi trình duyệt đã cuộn.
 */
export function WorkRosterGridBody({ groups, days, compact, rowHeight, todayISO, leaveIds }: WorkRosterGridBodyProps) {
  const batches = splitIntoBatches(groups, leaveIds)
  return (
    <>
      {batches.map((batch, b) => (
        <div key={b} role="rowgroup" className="flex flex-col">
          {batch.map((entry) => {
            if (entry.kind === 'dept') {
              return (
                <div key={entry.group.key} role="row" className={cn(ROSTER_ROW_GRID, 'border-b border-border/60 bg-muted/40')}>
                  <div role="rowheader" className="col-span-full px-3 py-1 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                    <span className="sticky left-3 inline-block">
                      {entry.group.departmentName} · {entry.group.items.length}
                    </span>
                  </div>
                </div>
              )
            }
            const { item, slot } = entry
            if (slot === null) {
              return <WorkRosterRow key={item.employee_id} item={item} days={days} compact={compact} todayISO={todayISO} />
            }
            const pad = (STICKY_LEAVE_SLOTS - 1 - slot) * rowHeight
            return (
              <Fragment key={item.employee_id}>
                <WorkRosterRow
                  item={item}
                  days={days}
                  compact={compact}
                  todayISO={todayISO}
                  stickyStyle={{ top: ROSTER_HEADER_HEIGHT + slot * rowHeight, marginBottom: pad }}
                />
                {pad > 0 && <div aria-hidden style={{ marginTop: -pad }} />}
              </Fragment>
            )
          })}
        </div>
      ))}
    </>
  )
}
