import { describe, expect, it } from 'vitest'

import type { EmployeeWorkHistory } from '../types/employee-work-history'
import {
  filterDecisionRows,
  sortWorkHistoryNewestFirst,
  workHistoryBadgeVariant,
  workHistorySummaryLine,
  workHistoryTimelineDateLabel,
} from './employee-work-history-display'

function row(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 1,
    employee_id: 1,
    event_type: 3,
    from_date: '2026-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Trưởng phòng',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

describe('filterDecisionRows', () => {
  it('chỉ giữ dòng có decision_no khác rỗng', () => {
    const rows = [row({ id: 1, decision_no: 'QD-01' }), row({ id: 2, decision_no: '' })]
    expect(filterDecisionRows(rows).map((r) => r.id)).toEqual([1])
  })

  it('decision_no chỉ gồm khoảng trắng coi như rỗng', () => {
    expect(filterDecisionRows([row({ decision_no: '   ' })])).toEqual([])
  })

  it('danh sách rỗng → trả rỗng, không ném lỗi', () => {
    expect(filterDecisionRows([])).toEqual([])
  })

  it('mọi dòng đều có decision_no → giữ nguyên tất cả', () => {
    const rows = [row({ id: 1, decision_no: 'A' }), row({ id: 2, decision_no: 'B' })]
    expect(filterDecisionRows(rows)).toHaveLength(2)
  })
})

describe('sortWorkHistoryNewestFirst', () => {
  it('sắp from_date mới nhất lên trước', () => {
    const rows = [
      row({ id: 1, from_date: '2025-01-01' }),
      row({ id: 2, from_date: '2026-06-01' }),
      row({ id: 3, from_date: '2025-12-31' }),
    ]
    expect(sortWorkHistoryNewestFirst(rows).map((r) => r.id)).toEqual([2, 3, 1])
  })

  it('cùng from_date → id lớn hơn (dòng ghi sau) lên trước', () => {
    const rows = [row({ id: 5, from_date: '2026-01-01' }), row({ id: 9, from_date: '2026-01-01' })]
    expect(sortWorkHistoryNewestFirst(rows).map((r) => r.id)).toEqual([9, 5])
  })

  it('không sửa mảng gốc (trả bản sao)', () => {
    const rows = [row({ id: 1, from_date: '2025-01-01' }), row({ id: 2, from_date: '2026-01-01' })]
    const original = [...rows]
    sortWorkHistoryNewestFirst(rows)
    expect(rows).toEqual(original)
  })

  it('danh sách rỗng → trả rỗng', () => {
    expect(sortWorkHistoryNewestFirst([])).toEqual([])
  })

  it('một phần tử → trả nguyên phần tử đó', () => {
    const rows = [row({ id: 1 })]
    expect(sortWorkHistoryNewestFirst(rows).map((r) => r.id)).toEqual([1])
  })
})

describe('workHistoryBadgeVariant', () => {
  it('Thôi việc (6) → destructive', () => {
    expect(workHistoryBadgeVariant(6)).toBe('destructive')
  })

  it('Kiêm nhiệm (4) → outline', () => {
    expect(workHistoryBadgeVariant(4)).toBe('outline')
  })

  it.each([1, 2, 3, 5])('nhóm chính (%d) → default', (eventType) => {
    expect(workHistoryBadgeVariant(eventType)).toBe('default')
  })

  it('Khác (9) → secondary', () => {
    expect(workHistoryBadgeVariant(9)).toBe('secondary')
  })

  it('mã lạ không rơi vào nhóm nào → secondary (an toàn, không ném lỗi)', () => {
    expect(workHistoryBadgeVariant(0)).toBe('secondary')
    expect(workHistoryBadgeVariant(-1)).toBe('secondary')
    expect(workHistoryBadgeVariant(999)).toBe('secondary')
  })
})

describe('workHistorySummaryLine', () => {
  it('đủ ba trường → nối bằng " · " theo thứ tự phòng ban · chức vụ · pháp nhân', () => {
    const r = row({ department_name: 'Phòng KD', position_label: 'Trưởng phòng', company_name: 'DEGO' })
    expect(workHistorySummaryLine(r)).toBe('Phòng KD · Trưởng phòng · DEGO')
  })

  it('thiếu một trường → bỏ hẳn phần đó, không để trống giữa hai dấu ·', () => {
    const r = row({ department_name: '', position_label: 'Trưởng phòng', company_name: 'DEGO' })
    expect(workHistorySummaryLine(r)).toBe('Trưởng phòng · DEGO')
  })

  it('cả ba đều rỗng → chuỗi rỗng', () => {
    const r = row({ department_name: '', position_label: '', company_name: '' })
    expect(workHistorySummaryLine(r)).toBe('')
  })

  it('trường chỉ gồm khoảng trắng → coi như rỗng, bỏ qua', () => {
    const r = row({ department_name: '   ', position_label: 'Trưởng phòng', company_name: 'DEGO' })
    expect(workHistorySummaryLine(r)).toBe('Trưởng phòng · DEGO')
  })
})

describe('workHistoryTimelineDateLabel', () => {
  it('variant "history" + to_date rỗng → "→ nay"', () => {
    const r = row({ from_date: '2026-01-15', to_date: null })
    expect(workHistoryTimelineDateLabel(r, 'history')).toBe('15/01/2026 → nay')
  })

  it('variant "history" + có to_date → khoảng ngày đầy đủ', () => {
    const r = row({ from_date: '2026-01-15', to_date: '2026-03-20' })
    expect(workHistoryTimelineDateLabel(r, 'history')).toBe('15/01/2026 → 20/03/2026')
  })

  it('variant "decision" → đọc decision_date (ngày ký), KHÔNG phải from_date', () => {
    const r = row({ from_date: '2026-01-15', decision_date: '2026-01-10' })
    expect(workHistoryTimelineDateLabel(r, 'decision')).toBe('10/01/2026')
  })

  it('variant "decision" + decision_date null → "—" (không ném lỗi)', () => {
    const r = row({ decision_date: null })
    expect(workHistoryTimelineDateLabel(r, 'decision')).toBe('—')
  })
})
