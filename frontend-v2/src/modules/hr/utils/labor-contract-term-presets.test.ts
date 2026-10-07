import { describe, expect, it } from 'vitest'

import { LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
import { endDateRule } from './labor-contract-rules'
import { endDateForPreset, termPresetsFor } from './labor-contract-term-presets'

const months = (n: number) => ({ label: `${n} tháng`, months: n })
const days = (n: number) => ({ label: `${n} ngày`, days: n })

describe('endDateForPreset — theo tháng', () => {
  it('ends the day before the same date N months later, like the printed «12 tháng»', () => {
    expect(endDateForPreset('2026-11-01', months(12))).toBe('2027-10-31')
    expect(endDateForPreset('2026-10-06', months(36))).toBe('2029-10-05')
  })

  it('rolls into the next year correctly across December', () => {
    expect(endDateForPreset('2026-12-15', months(1))).toBe('2027-01-14')
    expect(endDateForPreset('2026-12-01', months(24))).toBe('2028-11-30')
  })

  it('clamps to the end of a shorter target month before stepping back one day (matches backend _add_months)', () => {
    //  31/01 + 1 tháng → kẹp 28/02 → lùi 1 ngày = 27/02. Lệch luật backend thì «Thời hạn» in ra sai.
    expect(endDateForPreset('2026-01-31', months(1))).toBe('2026-02-27')
    expect(endDateForPreset('2027-01-31', months(13))).toBe('2028-02-28') // 2028 nhuận: kẹp 29/02 → 28/02
    expect(endDateForPreset('2026-08-31', months(3))).toBe('2026-11-29')
  })

  it('handles a leap-day start without drifting into March', () => {
    expect(endDateForPreset('2028-02-29', months(12))).toBe('2029-02-27')
    expect(endDateForPreset('2028-02-29', months(48))).toBe('2032-02-28')
  })

  it('never produces a 36-month term that the backend would flag as over 36 months', () => {
    //  Mô phỏng `rules.duration_warnings`: tháng tính CẢ ngày kết thúc, lẻ ngày làm tròn lên.
    //  last = end + 1 ngày; months = chênh năm*12 + chênh tháng, +1 nếu ngày của last > ngày bắt đầu.
    const warnMonths = (start: string, end: string) => {
      const [sy, sm, sd] = start.split('-').map(Number)
      const [ey, em, ed] = end.split('-').map(Number)
      const last = new Date(Date.UTC(ey, em - 1, ed + 1))
      const months = (last.getUTCFullYear() - sy) * 12 + (last.getUTCMonth() + 1 - sm)
      return months + (last.getUTCDate() > sd ? 1 : 0)
    }
    for (const start of ['2026-01-31', '2026-02-28', '2028-02-29', '2026-08-31', '2026-11-30', '2026-12-31']) {
      expect(warnMonths(start, endDateForPreset(start, months(36)))).toBeLessThanOrEqual(36)
    }
  })
})

describe('endDateForPreset — theo ngày (thử việc)', () => {
  it('counts the start day itself, so 60 days never exceeds the legal 60-day cap', () => {
    expect(endDateForPreset('2026-11-01', days(60))).toBe('2026-12-30')
    expect(endDateForPreset('2026-11-01', days(30))).toBe('2026-11-30')
  })

  it('crosses February in a leap year by real day count', () => {
    expect(endDateForPreset('2028-02-01', days(30))).toBe('2028-03-01')
  })
})

describe('endDateForPreset — đầu vào hỏng', () => {
  it.each(['', '2026-13-01', '2026-02-30', '06/10/2026', '2026-1-1', 'abc'])(
    'returns empty instead of a made-up date for %j',
    (start) => {
      expect(endDateForPreset(start, months(12))).toBe('')
    },
  )
})

describe('termPresetsFor', () => {
  it('offers day-based presets for probation and month-based for fixed-term', () => {
    expect(termPresetsFor(1).map((p) => p.label)).toEqual(['30 ngày', '60 ngày'])
    expect(termPresetsFor(2).map((p) => p.label)).toEqual(['12 tháng', '24 tháng', '36 tháng'])
  })

  it('offers nothing when no type is chosen yet', () => {
    expect(termPresetsFor(0)).toEqual([])
  })

  //  Phụ thuộc bộ mã sinh từ backend: loại nào CẤM ngày kết thúc thì tuyệt đối không có nút điền ngày,
  //  loại nào còn ngày kết thúc thì phải có nút. Backend thêm loại mới là bài này báo ngay.
  it.each(LABOR_CONTRACT_TYPE.map((o) => Number(o.value)))(
    'agrees with endDateRule for contract type %i',
    (type) => {
      if (endDateRule(type) === 'forbidden') expect(termPresetsFor(type)).toEqual([])
      else expect(termPresetsFor(type).length).toBeGreaterThan(0)
    },
  )
})
