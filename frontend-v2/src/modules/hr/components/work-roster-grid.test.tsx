import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ROSTER_DAYS, rosterCell, rosterItem, rosterLeave } from './work-roster-fixture'
import { WorkRosterGrid } from './work-roster-grid'

const IT = { id: 4, name: 'Lập trình & IT' }
const KT = { id: 7, name: 'Kế toán' }

function cellsFor(over: Record<string, Partial<ReturnType<typeof rosterCell>>> = {}) {
  return ROSTER_DAYS.map((d) => rosterCell(d.date, over[d.date] ?? {}))
}

function renderGrid(items: Parameters<typeof WorkRosterGrid>[0]['items'], mode: 'week' | 'month' = 'week') {
  return render(
    <MemoryRouter>
      <WorkRosterGrid days={ROSTER_DAYS} items={items} mode={mode} todayISO="2026-10-05" />
    </MemoryRouter>,
  )
}

describe('WorkRosterGrid', () => {
  it('groups rows by department with a headcount in each group header', () => {
    renderGrid([
      rosterItem(1, 'An', IT, cellsFor()),
      rosterItem(2, 'Bình', IT, cellsFor()),
      rosterItem(3, 'Chi', KT, cellsFor()),
    ])
    expect(screen.getByText('Lập trình & IT · 2')).toBeInTheDocument()
    expect(screen.getByText('Kế toán · 1')).toBeInTheDocument()
    expect(screen.getByText('Bình')).toBeInTheDocument()
  })

  it('marks the current day column with aria-current and shows the shared holiday name on the column header', () => {
    renderGrid([rosterItem(1, 'An', IT, cellsFor())])
    const headers = screen.getAllByRole('columnheader')
    expect(headers.find((h) => h.getAttribute('aria-current') === 'date')).toHaveTextContent('5/10')
    expect(screen.getByTitle('Nghỉ bù')).toBeInTheDocument()
  })

  it('counts working and off per day in the summary row, a half-day leave still counting as working', () => {
    renderGrid([
      rosterItem(1, 'An', IT, cellsFor()),
      rosterItem(2, 'Bình', IT, cellsFor({ '2026-10-05': { leave: rosterLeave() } })),
      rosterItem(3, 'Chi', IT, cellsFor({ '2026-10-05': { leave: rosterLeave({ afternoon: false }) } })),
    ])
    const total = screen.getByTitle('Đang làm 2 · Nghỉ 1')
    expect(total).toHaveTextContent('1')
    //  Ngày không ai nghỉ thì ô tổng để trống, không in số 0.
    expect(screen.getAllByTitle(/Nghỉ 0/)[0].querySelector('[aria-hidden]')).toBeNull()
  })

  it('links only cells that carry a leave request to that request', () => {
    renderGrid([
      rosterItem(1, 'An', IT, cellsFor({ '2026-10-05': { leave: rosterLeave({ request_id: 77 }) } })),
    ])
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links.every((l) => l.getAttribute('href') === '/hr/leave-requests/77')).toBe(true)
    expect(links[0]).toHaveAccessibleName(/Phép năm \(đã duyệt\)/)
  })

  it('says pending in the accessible name of a pending leave cell', () => {
    renderGrid([
      rosterItem(1, 'An', IT, cellsFor({ '2026-10-05': { leave: rosterLeave({ is_approved: false }) } })),
    ])
    expect(screen.getAllByRole('link')[0]).toHaveAccessibleName(/chờ duyệt/)
  })

  it('prints short text in week cells and leaves ordinary and scheduled-off month cells blank', () => {
    const items = [rosterItem(1, 'An', IT, cellsFor({ '2026-10-11': { work_kind: 1 } }))]
    const week = renderGrid(items, 'week')
    expect(within(week.container).getAllByText('08:00 – 17:00').length).toBeGreaterThan(0)
    expect(within(week.container).getByText('Nghỉ')).toBeInTheDocument()
    week.unmount()

    const month = renderGrid(items, 'month')
    expect(within(month.container).queryByText('08:00 – 17:00')).toBeNull()
    expect(within(month.container).queryByText('Nghỉ')).toBeNull()
  })

  it('survives an empty roster and an employee missing cells for a day', () => {
    const empty = renderGrid([])
    expect(empty.container.querySelectorAll('[data-leave-row], [role=row] [role=cell] a')).toHaveLength(0)
    expect(screen.queryAllByRole('rowheader').map((h) => h.textContent)).toEqual(['Nghỉ (trang này)'])
    empty.unmount()

    renderGrid([rosterItem(1, 'An', IT, [])])
    expect(screen.getByText('An')).toBeInTheDocument()
    //  Thiếu ô thì báo «chưa có dữ liệu» chứ không bịa là đi làm hay nghỉ.
    expect(screen.getAllByTitle(/Chưa có dữ liệu/)).toHaveLength(ROSTER_DAYS.length)
    expect(screen.getAllByTitle('Đang làm 0 · Nghỉ 0')).toHaveLength(ROSTER_DAYS.length)
  })

  it('renders department id 0 as a group with a fallback name', () => {
    renderGrid([rosterItem(1, 'An', { id: 0, name: '' }, cellsFor())])
    expect(screen.getByText('Chưa có phòng ban · 1')).toBeInTheDocument()
  })

  //  Hàng tổng chỉ vẽ viên thuốc khi cột không đóng — số liệu phải còn trong cây truy cập cho trình đọc màn hình.
  it('exposes working/off counts to screen readers even when the pill is hidden', () => {
    renderGrid([rosterItem(1, 'An', IT, cellsFor({ '2026-10-11': { work_kind: 1 } }))])
    expect(screen.getByText('Đi làm 0, nghỉ 1')).toHaveClass('sr-only')
    expect(screen.getAllByText('Đi làm 1, nghỉ 0').length).toBeGreaterThan(0)
  })

  //  Lễ riêng của pháp nhân người đó nằm ở ô, không ở tiêu đề cột.
  it('names a company-only holiday on the cell tooltip while the header stays blank', () => {
    renderGrid([rosterItem(1, 'An', IT, cellsFor({ '2026-10-11': { is_holiday: true, holiday_name: 'Lễ riêng' } }))])
    expect(screen.getByTitle('An · 2026-10-11 — Ngày lễ: Lễ riêng')).toBeInTheDocument()
    expect(screen.queryByTitle('Lễ riêng')).toBeNull()
  })

  describe('sticky leave rows', () => {
    const LEAVE_DAY = '2026-10-05'
    const withLeave = (id: number, name: string, over: Partial<ReturnType<typeof rosterLeave>> = {}) =>
      rosterItem(id, name, IT, cellsFor({ [LEAVE_DAY]: { leave: rosterLeave({ request_id: id, ...over }) } }))
    const stickyNames = () =>
      Array.from(document.querySelectorAll('[data-leave-row] [role=rowheader]')).map((th) => th.textContent)

    //  05/10/2026: đại ca chê bản khối ghim riêng trên đầu (tên lặp hai lần). Hàng có nghỉ phải dính
    //  TẠI CHỖ, chồng theo thứ tự hàng, và mỗi người chỉ xuất hiện MỘT lần.
    it('makes the leave rows themselves sticky in place, without a duplicated pinned block', () => {
      renderGrid([
        rosterItem(1, 'An', IT, cellsFor()),
        withLeave(2, 'Bình'),
        withLeave(3, 'Chi', { is_approved: false }),
        rosterItem(4, 'Dũng', IT, cellsFor({ [LEAVE_DAY]: { work_kind: 1 } })),
      ])
      expect(stickyNames()).toEqual(['BìnhNV2', 'ChiNV3'])
      expect(screen.getAllByText('Bình')).toHaveLength(1)
      expect(screen.queryByText(/Có nghỉ phép trong kỳ/)).toBeNull()
    })

    it('keeps rows without leave, or with leave only on a holiday, non-sticky', () => {
      renderGrid([
        rosterItem(1, 'An', IT, cellsFor()),
        rosterItem(2, 'Bình', IT, cellsFor({ [LEAVE_DAY]: { is_holiday: true, leave: rosterLeave() } })),
      ])
      expect(stickyNames()).toEqual([])
    })

    //  05/10/2026: «3 row thì từ row 4 5 6 đẩy lên 1 lượt» — mỗi đợt 3 hàng có nghỉ nằm chung MỘT khung để
    //  trình duyệt tự đẩy cả khối (CSS thuần). Hàng j dính ở đáy đầu bảng + j·H, lề dưới (2−j)·H.
    it('groups leave rows into batches of 3 that stick at stacked offsets under the header', () => {
      renderGrid(Array.from({ length: 7 }, (_, i) => withLeave(i + 1, `Người${i + 1}`)))
      const rows = Array.from(document.querySelectorAll<HTMLElement>('[data-leave-row]'))
      expect(rows).toHaveLength(7)
      expect(rows.map((r) => r.style.top)).toEqual(['76px', '116px', '156px', '76px', '116px', '156px', '76px'])
      expect(rows.map((r) => r.style.marginBottom)).toEqual(['80px', '40px', '0px', '80px', '40px', '0px', '80px'])
      //  Ba khung đợt: [1,2,3] · [4,5,6] · [7] — hàng 4 và 7 mở đợt mới.
      const batchOf = (r: HTMLElement) => r.closest('[role=rowgroup]')
      expect(new Set(rows.map(batchOf)).size).toBe(3)
      expect(batchOf(rows[0])).toBe(batchOf(rows[2]))
      expect(batchOf(rows[3])).not.toBe(batchOf(rows[2]))
    })

    it('uses the month row height for offsets in month view', () => {
      renderGrid([withLeave(1, 'A'), withLeave(2, 'B')], 'month')
      const rows = Array.from(document.querySelectorAll<HTMLElement>('[data-leave-row]'))
      expect(rows.map((r) => r.style.top)).toEqual(['76px', '108px'])
    })
  })
})
