import { describe, expect, it } from 'vitest'

import {
  addDaysISO,
  coversDay,
  daysInRowOrder,
  formatPeriods,
  groupRequestsByDay,
  overlappingPeriodIndexes,
  periodOn,
  periodsOf,
  type PeriodLike,
} from './leave-periods'
import { LEAVE_SESSION, type LeavePeriod } from '../types/leave'

const { FULL, MORNING, AFTERNOON } = LEAVE_SESSION

function period(from: string, to: string, extra: Partial<LeavePeriod> = {}): LeavePeriod {
  return {
    id: 0,
    from_date: from,
    from_session: FULL,
    to_date: to,
    to_session: FULL,
    days: 0,
    sort_order: 0,
    ...extra,
  }
}

/** Đơn ví dụ của chủ sản phẩm: 27/10 (T3) cả ngày + 03/11 chiều → 07/11 cả ngày. */
function exampleRequest(id = 1) {
  return {
    id,
    from_date: '2026-10-27',
    from_session: FULL,
    to_date: '2026-11-07',
    to_session: FULL,
    total_days: 5.5,
    periods: [
      period('2026-10-27', '2026-10-27', { days: 1 }),
      period('2026-11-03', '2026-11-07', { from_session: AFTERNOON, days: 4.5, sort_order: 1 }),
    ],
  }
}

describe('periodsOf', () => {
  it('falls back to ONE period built from the header when the dump has no periods', () => {
    //  Tab trình duyệt còn bản cũ / đường API chưa gom `periods`: không có nhánh này thì
    //  mọi nơi gọi `.map` trên `undefined` và màn hình trắng.
    for (const periods of [undefined, []]) {
      const out = periodsOf({
        from_date: '2026-01-05',
        from_session: AFTERNOON,
        to_date: '2026-01-07',
        to_session: MORNING,
        total_days: 2,
        periods,
      })
      expect(out).toEqual([
        {
          id: 0,
          from_date: '2026-01-05',
          from_session: AFTERNOON,
          to_date: '2026-01-07',
          to_session: MORNING,
          days: 2,
          sort_order: 0,
        },
      ])
    }
  })

  it('a header without to_date becomes a single-day period, not an open range', () => {
    const [p] = periodsOf({
      from_date: '2026-01-05',
      from_session: FULL,
      to_date: '',
      to_session: FULL,
      total_days: 1,
    })
    expect(p.to_date).toBe('2026-01-05')
  })
})

describe('coversDay / periodOn — gap days are NOT leave', () => {
  it('the gap 28/10 → 02/11 between the two periods is not covered', () => {
    const r = exampleRequest()
    for (const iso of ['2026-10-28', '2026-10-31', '2026-11-01', '2026-11-02']) {
      expect(coversDay(r, iso)).toBe(false)
    }
  })

  it('both ends of every period are covered, the outer window edges are not', () => {
    const r = exampleRequest()
    for (const iso of ['2026-10-27', '2026-11-03', '2026-11-05', '2026-11-07']) {
      expect(coversDay(r, iso)).toBe(true)
    }
    expect(coversDay(r, '2026-10-26')).toBe(false)
    expect(coversDay(r, '2026-11-08')).toBe(false)
  })

  it('returns the period that contains the day, so the day view can say first/last OF THAT period', () => {
    expect(periodOn(exampleRequest(), '2026-11-07')?.from_date).toBe('2026-11-03')
    expect(periodOn(exampleRequest(), '2026-10-30')).toBeUndefined()
  })
})

describe('formatPeriods — same sentence as backend period_text', () => {
  it('writes the owner example exactly like the backend', () => {
    expect(formatPeriods(exampleRequest().periods)).toBe('27/10/2026 · 03/11 (chiều) → 07/11/2026')
  })

  it('a single full-day period is just the date', () => {
    expect(formatPeriods([period('2026-10-27', '2026-10-27')])).toBe('27/10/2026')
  })

  it('a single-day morning-only period says (sáng), an afternoon-only says (chiều)', () => {
    expect(formatPeriods([period('2026-10-27', '2026-10-27', { to_session: MORNING })])).toBe(
      '27/10/2026 (sáng)',
    )
    expect(
      formatPeriods([
        period('2026-10-27', '2026-10-27', { from_session: AFTERNOON, to_session: AFTERNOON }),
      ]),
    ).toBe('27/10/2026 (chiều)')
  })

  it('ending in the morning marks the end date', () => {
    expect(formatPeriods([period('2026-10-27', '2026-10-29', { to_session: MORNING })])).toBe(
      '27/10/2026 → 29/10/2026 (sáng)',
    )
  })

  it('shows the year on a later period start only when it differs from the first period', () => {
    expect(
      formatPeriods([period('2026-12-30', '2026-12-30'), period('2027-01-04', '2027-01-04')]),
    ).toBe('30/12/2026 · 04/01/2027')
  })

  it('an empty list is an empty string, not a crash', () => {
    expect(formatPeriods([])).toBe('')
  })
})

describe('overlappingPeriodIndexes', () => {
  const p = (
    from: string,
    to: string,
    from_session: number = FULL,
    to_session: number = FULL,
  ): PeriodLike => ({
    from_date: from,
    to_date: to,
    from_session,
    to_session,
  })

  it('no overlap → empty set', () => {
    expect(overlappingPeriodIndexes([p('2026-10-27', '2026-10-27'), p('2026-11-03', '2026-11-07')]).size).toBe(0)
  })

  it('flags BOTH rows, whatever order the user typed them in', () => {
    const out = overlappingPeriodIndexes([p('2026-11-03', '2026-11-07'), p('2026-10-27', '2026-11-03')])
    expect([...out].sort()).toEqual([0, 1])
  })

  it('same day morning in one row and afternoon in another still counts as overlap (backend rule)', () => {
    const out = overlappingPeriodIndexes([
      p('2026-11-03', '2026-11-03', FULL, MORNING),
      p('2026-11-03', '2026-11-05', AFTERNOON, FULL),
    ])
    expect(out.size).toBe(2)
  })

  it('a long period swallowing two short ones flags all three, but not the untouched fourth', () => {
    const out = overlappingPeriodIndexes([
      p('2026-11-01', '2026-11-20'),
      p('2026-11-05', '2026-11-06'),
      p('2026-11-10', '2026-11-12'),
      p('2026-12-01', '2026-12-01'),
    ])
    expect([...out].sort()).toEqual([0, 1, 2])
  })

  it('rows still missing a date are ignored instead of matching everything', () => {
    expect(overlappingPeriodIndexes([p('', ''), p('2026-11-03', '2026-11-07')]).size).toBe(0)
  })
})

describe('addDaysISO', () => {
  it('crosses month and year ends in local time', () => {
    expect(addDaysISO('2026-10-31', 1)).toBe('2026-11-01')
    expect(addDaysISO('2026-12-31', 1)).toBe('2027-01-01')
    expect(addDaysISO('2028-02-28', 1)).toBe('2028-02-29')
  })
})

describe('groupRequestsByDay — calendar spreading', () => {
  it('puts the request ONLY on days inside its periods, never on gap days', () => {
    const map = groupRequestsByDay([exampleRequest()], '2026-10-01', '2026-11-30')
    expect([...map.keys()].sort()).toEqual([
      '2026-10-27',
      '2026-11-03',
      '2026-11-04',
      '2026-11-05',
      '2026-11-06',
      '2026-11-07',
    ])
  })

  it('clips to the visible window', () => {
    const map = groupRequestsByDay([exampleRequest()], '2026-11-01', '2026-11-04')
    expect([...map.keys()].sort()).toEqual(['2026-11-03', '2026-11-04'])
  })

  it('an old single-period request still covers its whole range', () => {
    const old = { ...exampleRequest(), periods: undefined, from_date: '2026-10-27', to_date: '2026-10-29' }
    expect([...groupRequestsByDay([old], '2026-10-01', '2026-10-31').keys()]).toEqual([
      '2026-10-27',
      '2026-10-28',
      '2026-10-29',
    ])
  })

  it('odd data with overlapping periods lists the request once per day', () => {
    const odd = {
      ...exampleRequest(),
      periods: [period('2026-10-27', '2026-10-28'), period('2026-10-28', '2026-10-29')],
    }
    const map = groupRequestsByDay([odd], '2026-10-01', '2026-10-31')
    expect(map.get('2026-10-28')).toHaveLength(1)
  })

  it('a window entirely inside the gap yields nothing', () => {
    expect(groupRequestsByDay([exampleRequest()], '2026-10-28', '2026-11-02').size).toBe(0)
  })
})

describe('daysInRowOrder', () => {
  const p = (from: string, to: string): PeriodLike => ({
    from_date: from,
    to_date: to,
    from_session: FULL,
    to_session: FULL,
  })

  it('maps sorted estimate days back to the rows the user typed out of order', () => {
    const rows = [p('2026-11-03', '2026-11-07'), p('2026-10-27', '2026-10-27')]
    //  Backend trả theo ngày: 27/10 trước (1 ngày), 03/11 sau (4.5 ngày).
    expect(daysInRowOrder(rows, [{ days: 1 }, { days: 4.5 }])).toEqual([4.5, 1])
  })

  it('matches by the dates the server echoes back, whatever order it uses', () => {
    const rows = [p('2026-11-03', '2026-11-07'), p('2026-10-27', '2026-10-27')]
    const estimated = [
      { from_date: '2026-10-27', to_date: '2026-10-27', days: 1 },
      { from_date: '2026-11-03', to_date: '2026-11-07', days: 4.5 },
    ]
    expect(daysInRowOrder(rows, estimated)).toEqual([4.5, 1])
    //  Ngày trả về không khớp hàng nào (bản ước lượng cũ) → hàng đó chưa có số, không bịa.
    expect(daysInRowOrder([rows[0], p('2026-12-01', '2026-12-01')], estimated)).toEqual([4.5, undefined])
  })

  it('a stale estimate with a different row count is ignored, not misassigned', () => {
    expect(daysInRowOrder([p('2026-10-27', '2026-10-27')], [{ days: 1 }, { days: 2 }])).toBeUndefined()
    expect(daysInRowOrder([p('2026-10-27', '2026-10-27')], undefined)).toBeUndefined()
  })
})
