import { describe, expect, it } from 'vitest'

import type { SurveyReportDoc, SurveyRequestReport } from '../types/survey-request-report'
import {
  REPORT_FILTER_ALL,
  currentReportPhaseId,
  filterReportDocs,
  isReportDocLocked,
  latestPlannedDate,
  matchReportDoc,
  nearestExpiry,
  pendingDepends,
  reportDocLateDays,
  reportPercent,
  reportPlanLateDays,
  trackingMarkers,
} from './survey-report-helpers'

function doc(overrides: Partial<SurveyReportDoc>): SurveyReportDoc {
  return {
    id: 1,
    phase_id: 1,
    item_id: 0,
    title: 'Hồ sơ',
    description: '',
    required: true,
    status: 0,
    status_label: 'Chưa bắt đầu',
    file_note: '',
    depends: [],
    start_date: '',
    expires_at: '',
    planned_date: '',
    assignee_id: 0,
    assignee_name: '',
    sort_order: 0,
    ...overrides,
  }
}

function byId(docs: SurveyReportDoc[]): Map<number, SurveyReportDoc> {
  return new Map(docs.map((d) => [d.id, d]))
}

describe('filterReportDocs', () => {
  const docs = [doc({ id: 1, item_id: 0 }), doc({ id: 2, item_id: 7 }), doc({ id: 3, item_id: 8 })]

  it('shows shared docs (item_id = 0) under every item filter', () => {
    expect(filterReportDocs(docs, 7).map((d) => d.id)).toEqual([1, 2])
  })

  it('treats REPORT_FILTER_ALL as no filter — 0 is a real id, not the sentinel', () => {
    // Bẫy «id = 0 làm mốc tất cả» (duoc-CR-322): 0 là hồ sơ CHUNG, sentinel phải là -1.
    expect(filterReportDocs(docs, REPORT_FILTER_ALL)).toHaveLength(3)
    expect(filterReportDocs(docs, 0).map((d) => d.id)).toEqual([1])
  })
})

describe('isReportDocLocked / pendingDepends', () => {
  it('locks a doc while any prerequisite is unfinished, unlocks when all done', () => {
    const a = doc({ id: 1, status: 0 })
    const b = doc({ id: 2, depends: [1] })
    expect(isReportDocLocked(b, byId([a, b]))).toBe(true)

    const aDone = doc({ id: 1, status: 3 })
    expect(isReportDocLocked(b, byId([aDone, b]))).toBe(false)
  })

  it('never locks a doc that is already done — old data must stay toggleable', () => {
    const a = doc({ id: 1, status: 0 })
    const b = doc({ id: 2, status: 3, depends: [1] })
    expect(isReportDocLocked(b, byId([a, b]))).toBe(false)
  })

  it('ignores dead prerequisite ids instead of locking forever', () => {
    // Id chết mà đếm là «chưa xong» thì hồ sơ khóa vĩnh viễn theo một thứ không tồn tại.
    const b = doc({ id: 2, depends: [999] })
    expect(pendingDepends(b, byId([b]))).toEqual([])
    expect(isReportDocLocked(b, byId([b]))).toBe(false)
  })
})

describe('matchReportDoc', () => {
  const d = doc({ title: 'Giấy phép nhập khẩu tiền chất', description: 'Bộ Công An', file_note: 'GP-tienchat.pdf', status_label: 'Đang làm' })

  it('matches Vietnamese text without diacritics and case-insensitively', () => {
    expect(matchReportDoc(d, 'giay phep', 'KNO3')).toBe(true)
    expect(matchReportDoc(d, 'BỘ CÔNG AN', 'KNO3')).toBe(true)
  })

  it('matches word-by-word across fields — words need not be adjacent', () => {
    // «giấy phép» ở tiêu đề còn «công an» ở mô tả — tìm gộp vẫn phải ra.
    expect(matchReportDoc(d, 'giay phep bo cong an', '')).toBe(true)
    expect(matchReportDoc(d, 'giay phep khong lien quan', '')).toBe(false)
  })

  it('searches every text field: file note, status label and item name', () => {
    expect(matchReportDoc(d, 'tienchat.pdf', '')).toBe(true)
    expect(matchReportDoc(d, 'dang lam', '')).toBe(true)
    expect(matchReportDoc(d, 'kno3', 'KNO₃ – Kali Nitrat')).toBe(true)
    // Hồ sơ không gắn nút nào tìm được bằng chữ «chung».
    expect(matchReportDoc(d, 'chung', '')).toBe(true)
    expect(matchReportDoc(d, 'không tồn tại đâu', '')).toBe(false)
  })

  it('treats an empty or whitespace-only query as no filter', () => {
    expect(matchReportDoc(d, '', '')).toBe(true)
    expect(matchReportDoc(d, '   ', '')).toBe(true)
  })
})

function report(overrides: Partial<SurveyRequestReport>): SurveyRequestReport {
  return {
    items: [],
    phases: [],
    docs: [],
    restorable: false,
    restorable_audit_id: 0,
    ...overrides,
  }
}

const twoPhases = [
  { id: 10, name: 'GĐ1', location: '', sort_order: 0 },
  { id: 20, name: 'GĐ2', location: '', sort_order: 1 },
]

describe('currentReportPhaseId / trackingMarkers', () => {
  it('points at the first phase with an unfinished doc, per item track', () => {
    const r = report({
      items: [
        { id: 1, name: 'K2SO4', sort_order: 0 },
        { id: 2, name: 'KNO3', sort_order: 1 },
      ],
      phases: twoPhases,
      docs: [
        doc({ id: 100, phase_id: 10, item_id: 1, status: 3 }),
        doc({ id: 101, phase_id: 20, item_id: 1, status: 0 }),
        doc({ id: 102, phase_id: 10, item_id: 2, status: 0 }),
      ],
    })
    expect(currentReportPhaseId(r, 1)).toBe(20)
    expect(currentReportPhaseId(r, 2)).toBe(10)
    // «Tất cả»: mỗi nút một chấm, nhãn là số thứ tự nút.
    expect(trackingMarkers(r, REPORT_FILTER_ALL)).toEqual([
      { phaseId: 20, label: '1', names: ['K2SO4'] },
      { phaseId: 10, label: '2', names: ['KNO3'] },
    ])
    // Xem một tab: đúng một chấm không số tại giai đoạn hiện tại của tab.
    expect(trackingMarkers(r, 2)).toEqual([{ phaseId: 10, label: '', names: ['KNO3'] }])
  })

  it('merges items standing at the same phase into one +n marker', () => {
    const r = report({
      items: [
        { id: 1, name: 'A', sort_order: 0 },
        { id: 2, name: 'B', sort_order: 1 },
        { id: 3, name: 'C', sort_order: 2 },
      ],
      phases: twoPhases,
      // Một hồ sơ CHUNG chưa xong ở GĐ1 → cả ba nút cùng đứng đó.
      docs: [doc({ id: 100, phase_id: 10, item_id: 0, status: 0 })],
    })
    expect(trackingMarkers(r, REPORT_FILTER_ALL)).toEqual([
      { phaseId: 10, label: '+3', names: ['A', 'B', 'C'] },
    ])
  })

  it('returns no marker for a finished or empty track — nothing left to blink at', () => {
    const done = report({
      items: [{ id: 1, name: 'A', sort_order: 0 }],
      phases: twoPhases,
      docs: [doc({ id: 100, phase_id: 10, item_id: 1, status: 3 })],
    })
    expect(currentReportPhaseId(done, 1)).toBe(null)
    expect(trackingMarkers(done, REPORT_FILTER_ALL)).toEqual([])
    expect(trackingMarkers(report({ phases: twoPhases }), REPORT_FILTER_ALL)).toEqual([])
  })

  it('tracks the whole block as one unnumbered dot when no item buttons exist', () => {
    const r = report({
      phases: twoPhases,
      docs: [doc({ id: 100, phase_id: 20, item_id: 0, status: 0 })],
    })
    expect(trackingMarkers(r, REPORT_FILTER_ALL)).toEqual([
      { phaseId: 20, label: '', names: [] },
    ])
  })
})

describe('reportPercent', () => {
  it('returns 0 for an empty list instead of dividing by zero', () => {
    expect(reportPercent([])).toBe(0)
  })

  it('rounds the done ratio', () => {
    const docs = [doc({ id: 1, status: 3 }), doc({ id: 2 }), doc({ id: 3 })]
    expect(reportPercent(docs)).toBe(33)
  })
})

describe('nearestExpiry', () => {
  it('returns the earliest expiry among unfinished docs', () => {
    const docs = [
      doc({ id: 1, expires_at: '2026-10-20' }),
      doc({ id: 2, expires_at: '2026-09-30' }),
      doc({ id: 3, expires_at: '2026-12-01' }),
    ]
    expect(nearestExpiry(docs)).toBe('2026-09-30')
  })

  it('ignores docs that are already done — their deadline is no longer pending', () => {
    // Hồ sơ xong có hạn sớm nhất nhưng không được tính: việc đã xong hết hạn là chuyện cũ.
    const docs = [
      doc({ id: 1, status: 3, expires_at: '2026-01-01' }),
      doc({ id: 2, status: 0, expires_at: '2026-09-30' }),
    ]
    expect(nearestExpiry(docs)).toBe('2026-09-30')
  })

  it('surfaces an overdue (past) date over a later one — the critical deadline rises first', () => {
    const docs = [
      doc({ id: 1, expires_at: '2026-11-01' }),
      doc({ id: 2, expires_at: '2025-01-15' }),
    ]
    expect(nearestExpiry(docs)).toBe('2025-01-15')
  })

  it('returns empty string when no unfinished doc has an expiry', () => {
    expect(nearestExpiry([])).toBe('')
    expect(nearestExpiry([doc({ id: 1, expires_at: '' })])).toBe('')
    expect(nearestExpiry([doc({ id: 1, status: 3, expires_at: '2026-09-30' })])).toBe('')
  })
})

describe('latestPlannedDate', () => {
  it('returns the farthest planned date — the plan milestone of the whole block', () => {
    const docs = [
      doc({ id: 1, planned_date: '2026-10-20' }),
      doc({ id: 2, planned_date: '2026-12-01' }),
      doc({ id: 3, planned_date: '2026-09-30' }),
    ]
    expect(latestPlannedDate(docs)).toBe('2026-12-01')
  })

  it('counts done docs too — a milestone met on time does not vanish', () => {
    // Khác nearestExpiry: mốc kế hoạch của hồ sơ đã xong vẫn là mốc của cả khối.
    const docs = [
      doc({ id: 1, status: 3, planned_date: '2026-12-01' }),
      doc({ id: 2, planned_date: '2026-09-30' }),
    ]
    expect(latestPlannedDate(docs)).toBe('2026-12-01')
  })

  it('returns empty string when no doc has a planned date', () => {
    expect(latestPlannedDate([])).toBe('')
    expect(latestPlannedDate([doc({ id: 1 }), doc({ id: 2, planned_date: '' })])).toBe('')
  })
})

describe('reportDocLateDays', () => {
  const today = '2026-09-12'

  it('counts days past the planned date for an unfinished doc', () => {
    expect(reportDocLateDays(doc({ planned_date: '2026-09-02' }), today)).toBe(10)
  })

  it('is 0 on the planned date itself and before it — due today is not late yet', () => {
    expect(reportDocLateDays(doc({ planned_date: '2026-09-12' }), today)).toBe(0)
    expect(reportDocLateDays(doc({ planned_date: '2026-09-30' }), today)).toBe(0)
  })

  it('is 0 for a done doc even when its planned date is long past', () => {
    expect(reportDocLateDays(doc({ status: 3, planned_date: '2025-01-01' }), today)).toBe(0)
  })

  it('is 0 without a planned date or with a malformed one — never NaN', () => {
    expect(reportDocLateDays(doc({ planned_date: '' }), today)).toBe(0)
    expect(reportDocLateDays(doc({ planned_date: 'abc' }), today)).toBe(0)
    expect(reportDocLateDays(doc({ planned_date: '2026-09-02' }), '')).toBe(0)
  })

  it('does not depend on the timezone — a one-day gap is exactly 1', () => {
    // Bẫy parseLocalDate: chuỗi chỉ có ngày mà đọc lẫn UTC/địa phương là lệch một ngày.
    expect(reportDocLateDays(doc({ planned_date: '2026-09-11' }), today)).toBe(1)
  })
})

describe('reportPlanLateDays', () => {
  const today = '2026-09-12'

  it('measures lateness against the FARTHEST planned date while any doc is unfinished', () => {
    const docs = [
      doc({ id: 1, status: 3, planned_date: '2026-08-01' }),
      doc({ id: 2, planned_date: '2026-09-05' }),
    ]
    expect(reportPlanLateDays(docs, today)).toBe(7)
  })

  it('is 0 when every doc is done — nothing left to be late', () => {
    const docs = [
      doc({ id: 1, status: 3, planned_date: '2026-08-01' }),
      doc({ id: 2, status: 3, planned_date: '2026-09-05' }),
    ]
    expect(reportPlanLateDays(docs, today)).toBe(0)
  })

  it('is 0 before the milestone, with no milestone, or with no docs', () => {
    expect(reportPlanLateDays([doc({ planned_date: '2026-12-01' })], today)).toBe(0)
    expect(reportPlanLateDays([doc({ planned_date: '' })], today)).toBe(0)
    expect(reportPlanLateDays([], today)).toBe(0)
  })

  it('an unfinished doc without its own planned date still makes the block late', () => {
    // Mốc là của CẢ khối: hồ sơ không có ngày riêng vẫn nằm trong kế hoạch chung.
    const docs = [doc({ id: 1, planned_date: '2026-09-01' }), doc({ id: 2 })]
    expect(reportPlanLateDays(docs, today)).toBe(11)
  })
})
