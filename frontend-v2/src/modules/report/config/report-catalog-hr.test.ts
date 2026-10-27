import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { REPORT_KEY } from '@/shared/constants/statuses'

import { HR_REPORT_CATALOG } from './report-catalog-hr'

/**
 * Bốn báo cáo Nhân sự đợt 3 (duoc-CR-688). Nhãn phải trùng HẲN `REPORT_KEY` sinh từ backend
 * (`report_keys.py` → `gen_status_ts.py`): tab «Báo cáo» của phân quyền đọc nhãn backend, menu
 * đọc nhãn ở đây — lệch một chữ là người gán quyền tưởng đang gán một báo cáo khác.
 */
const WAVE_3 = [
  { key: 21, path: appRoutes.report.payrollFund, entity: 'labor_contract', endpoint: '/api/payroll-fund/summary' },
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

  it('payroll page states the numbers are contract salaries with small groups hidden', () => {
    const entry = HR_REPORT_CATALOG.find((r) => r.key === 21)
    expect(entry?.description).toMatch(/dưới 3 người bị che/)
  })
})
