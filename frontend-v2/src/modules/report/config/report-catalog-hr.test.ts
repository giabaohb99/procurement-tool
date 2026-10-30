import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { REPORT_KEY } from '@/shared/constants/statuses'

import { HR_REPORT_CATALOG } from './report-catalog-hr'

/**
 * Bốn báo cáo Nhân sự đợt 3 (duoc-CR-688). Nhãn phải trùng HẲN `REPORT_KEY` sinh từ backend
 * (`report_keys.py` → `gen_status_ts.py`): tab "Báo cáo" của phân quyền đọc nhãn backend, menu
 * đọc nhãn ở đây — lệch một chữ là người gán quyền tưởng đang gán một báo cáo khác.
 */
const WAVE_3 = [
  { key: 21, path: appRoutes.report.payrollFund, entity: 'employee', endpoint: '/api/payroll-fund/summary' },
  { key: 22, path: appRoutes.report.benefitAudience, entity: 'employee', endpoint: '/api/benefit-audience/summary' },
  { key: 23, path: appRoutes.report.managementSpan, entity: 'employee', endpoint: '/api/management-span/summary' },
  { key: 24, path: appRoutes.report.workMoves, entity: 'employee', endpoint: '/api/work-moves/summary' },
] as const

describe('HR_REPORT_CATALOG — đợt 3', () => {
  it.each(WAVE_3)('report key $key has the backend label, gate, route and endpoint', (want) => {
    const entry = HR_REPORT_CATALOG.find((r) => r.key === want.key)
    expect(entry, `thiếu khóa ${want.key}`).toBeDefined()
    const backend = REPORT_KEY.find((o) => o.value === String(want.key))
    expect(entry?.label).toBe(backend?.label)
    expect(entry).toMatchObject({ path: want.path, entity: want.entity, endpoint: want.endpoint, group: 'Nhân sự' })
  })

  it('uses the four agreed routes', () => {
    expect([
      appRoutes.report.payrollFund,
      appRoutes.report.benefitAudience,
      appRoutes.report.managementSpan,
      appRoutes.report.workMoves,
    ]).toEqual(['/report/payroll-fund', '/report/benefit-audience', '/report/management-span', '/report/work-moves'])
  })

  it('keeps salary totals and occasion budgets off the shared overview strip', () => {
    for (const key of [21, 22]) {
      expect(HR_REPORT_CATALOG.find((r) => r.key === key)?.overviewKpis).toEqual([])
    }
  })

  it('payroll page states the numbers come from the profile salary field with small groups hidden', () => {
    // duoc-CR-693: nguồn là ô lương ở hồ sơ, không còn là lương trên HĐLĐ.
    const entry = HR_REPORT_CATALOG.find((r) => r.key === 21)
    expect(entry?.description).toMatch(/dưới 3 người bị che/)
    expect(entry?.description).toMatch(/hồ sơ/)
    expect(entry?.description).not.toMatch(/hợp đồng lao động/)
  })
})

/**
 * Báo cáo Nhân sự đợt 4 (duoc-CR-689). Cùng luật nhãn với đợt 3: phải trùng HẲN `REPORT_KEY`.
 * Khóa 25 "Số người kế hoạch so với thực tế" ĐÃ BỎ cùng Kế hoạch nhân sự (duoc-CR-692) — không tái cấp.
 */
const WAVE_4 = [
  { key: 26, path: '/report/attendance', entity: 'employee', endpoint: '/api/attendance-report/summary' },
  { key: 27, path: '/report/profile-changes', entity: 'employee', endpoint: '/api/profile-change-report/summary' },
  { key: 28, path: '/report/room-usage', entity: 'room_booking', endpoint: '/api/room-usage/summary' },
  { key: 29, path: '/report/legal-watch', entity: 'employee', endpoint: '/api/legal-watch/summary' },
] as const

describe('HR_REPORT_CATALOG — đợt 4', () => {
  it.each(WAVE_4)('report key $key has the backend label, gate, route and endpoint', (want) => {
    const entry = HR_REPORT_CATALOG.find((r) => r.key === want.key)
    expect(entry, `thiếu khóa ${want.key}`).toBeDefined()
    const backend = REPORT_KEY.find((o) => o.value === String(want.key))
    expect(backend, `REPORT_KEY chưa sinh khóa ${want.key}`).toBeDefined()
    expect(entry?.label).toBe(backend?.label)
    expect(entry).toMatchObject({ path: want.path, entity: want.entity, endpoint: want.endpoint, group: 'Nhân sự' })
  })

  it('keeps sensitive and period-capped reports off the shared overview strip', () => {
    //  29 đòi `employee_sensitive.read`; 26 chặn kỳ > 92 ngày — trang Tổng quan chọn "Năm nay" là hỏng.
    for (const key of [26, 29]) {
      expect(HR_REPORT_CATALOG.find((r) => r.key === key)?.overviewKpis).toEqual([])
    }
  })

  it('every wave-4 page loads a component', async () => {
    for (const { key } of WAVE_4) {
      const entry = HR_REPORT_CATALOG.find((r) => r.key === key)
      expect(typeof (await entry?.load())).toBe('function')
    }
  })
})

describe('HR_REPORT_CATALOG — khóa 25 đã bỏ (duoc-CR-692)', () => {
  it('no longer lists the headcount-plan report nor reuses key 25', () => {
    expect(HR_REPORT_CATALOG.find((r) => r.key === 25)).toBeUndefined()
    expect(HR_REPORT_CATALOG.some((r) => r.path === '/report/headcount-plan')).toBe(false)
    expect(REPORT_KEY.find((o) => o.value === '25')).toBeUndefined()
  })
})
