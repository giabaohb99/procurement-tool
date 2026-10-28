import { describe, expect, it } from 'vitest'

import { buildHeadcountPlanColumns, buildHeadcountPlanCrudConfig, buildHeadcountPlanFormFields } from './headcount-plan-crud'

const BASE = {
  canSeePayroll: false,
  yearOptions: [{ value: '2026', label: '2026' }],
  companyOptions: [
    { value: '1', label: 'DEGO Holding' },
    { value: '2', label: 'DEGO Food' },
  ],
  departments: [
    { id: 11, name: 'Kế toán', company_id: 1 },
    { id: 21, name: 'Kho', company_id: 2 },
  ],
  defaultYear: 2026,
}

describe('headcount plan screen — salary only for labor_contract.read', () => {
  it('has no salary column and no salary field without the permission', () => {
    expect(buildHeadcountPlanColumns(false).map((c) => c.key)).not.toContain('planned_payroll_monthly')
    expect(buildHeadcountPlanFormFields(BASE).map((f) => f.name)).not.toContain('planned_payroll_monthly')
  })

  it('adds both once the viewer can read labour contracts', () => {
    expect(buildHeadcountPlanColumns(true).map((c) => c.key)).toContain('planned_payroll_monthly')
    expect(buildHeadcountPlanFormFields({ ...BASE, canSeePayroll: true }).map((f) => f.name)).toContain(
      'planned_payroll_monthly',
    )
  })
})

describe('headcount plan form', () => {
  it('locks year, company and department when editing — they are the row key', () => {
    const locked = buildHeadcountPlanFormFields(BASE)
      .filter((f) => f.readonlyOnEdit)
      .map((f) => f.name)
    expect(locked).toEqual(['year', 'company_id', 'department_id'])
  })

  it('offers every department whatever company is chosen, with whole-company first', () => {
    const dept = buildHeadcountPlanFormFields(BASE).find((f) => f.name === 'department_id')
    expect(dept?.options?.map((o) => o.label)).toEqual(['Toàn pháp nhân', 'Kế toán', 'Kho'])
    expect(dept?.defaultValue).toBe('0')
  })

  it('normalises the payload through the config hook', () => {
    const config = buildHeadcountPlanCrudConfig(BASE)
    expect(config.buildPayload?.({ year: '2026', company_id: '1', department_id: '', planned_headcount: '4' })).toMatchObject({
      year: 2026,
      company_id: 1,
      department_id: 0,
      planned_headcount: 4,
    })
  })
})

describe('headcount plan filters', () => {
  it('offers year, company and department quick filters, gated by the new headcount_plan key', () => {
    const config = buildHeadcountPlanCrudConfig(BASE)
    expect(config.entity).toBe('headcount_plan')
    expect(config.quickFilters?.map((q) => q.key)).toEqual(['year', 'company_id', 'department_id'])
  })

  it('uses the same shared department list in the filter, keeping the real 0 (whole company)', () => {
    const dept = buildHeadcountPlanCrudConfig(BASE).quickFilters?.find((q) => q.key === 'department_id')
    expect(dept?.options?.[0]).toEqual({ value: '0', label: 'Toàn pháp nhân' })
    expect(dept?.options).toHaveLength(3)
  })
})
