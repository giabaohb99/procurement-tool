import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { buildHeadcountPlanDepartmentOptions } from '../utils/headcount-plan-options'
import type { HeadcountPlanListItem } from '../types/headcount-plan'
import { buildHeadcountPlanColumns, buildHeadcountPlanCrudConfig } from './headcount-plan-crud'

const BASE = {
  canSeePayroll: false,
  yearOptions: [{ value: '2026', label: '2026' }],
  companyOptions: [
    { value: '1', label: 'DEGO Holding' },
    { value: '2', label: 'DEGO Food' },
  ],
  departmentOptions: buildHeadcountPlanDepartmentOptions([
    { id: 11, name: 'Kế toán' },
    { id: 21, name: 'Kho' },
  ]),
}

const row = (over: Partial<HeadcountPlanListItem> = {}): HeadcountPlanListItem => ({
  id: 1,
  year: 2026,
  period_type: 3,
  period_no: 3,
  company_id: 1,
  company_name: 'AGRIPLANT',
  department_id: 11,
  department_name: 'Kế toán',
  headcount_end: 6,
  total_cost: 123_456_789,
  basis_no: '12/QĐ-BGĐ',
  basis_date: '2026-06-30',
  note: '',
  ...over,
})

const cellOf = (canSeePayroll: boolean, key: string, r: HeadcountPlanListItem) => {
  const col = buildHeadcountPlanColumns(canSeePayroll).find((c) => c.key === key)
  if (!col) throw new Error(`no column ${key}`)
  return render(<>{col.cell(r)}</>)
}

describe('headcount plan list — money column only for labor_contract.read', () => {
  it('has no total cost column without the permission', () => {
    expect(buildHeadcountPlanColumns(false).map((c) => c.key)).not.toContain('total_cost')
  })

  it('shows a real dash (not 0) when the server masks the total for this company', () => {
    //  0 đọc ra «kế hoạch không tốn đồng nào»; backend trả `null` khi che tiền theo pháp nhân.
    cellOf(true, 'total_cost', row({ total_cost: null }))
    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('formats an unmasked total and keeps a real 0 as 0', () => {
    cellOf(true, 'total_cost', row({ total_cost: 0 }))
    expect(screen.getByText('0')).toBeInTheDocument()
  })
})

describe('headcount plan list — period column', () => {
  it.each([
    [1, 1, '2026'],
    [2, 2, 'H2-2026'],
    [3, 3, 'Q3-2026'],
    [4, 7, '07/2026'],
  ])('labels period type %i no %i as %s', (period_type, period_no, label) => {
    cellOf(false, 'period', row({ period_type, period_no }))
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('labels a whole-company plan even when the server left the name blank', () => {
    cellOf(false, 'department_name', row({ department_id: 0, department_name: '' }))
    expect(screen.getByText('Toàn pháp nhân')).toBeInTheDocument()
  })
})

describe('headcount plan list config', () => {
  it('opens a dedicated page for create and edit — the plan has four blocks, no dialog', () => {
    const config = buildHeadcountPlanCrudConfig(BASE)
    expect(config.createRoute).toBe('/hr/headcount-plans/new')
    expect(config.detailRoute?.(7)).toBe('/hr/headcount-plans/7')
    expect(config.formFields).toEqual([])
  })

  it('filters by year, period type, company and department, gated by headcount_plan', () => {
    const config = buildHeadcountPlanCrudConfig(BASE)
    expect(config.entity).toBe('headcount_plan')
    expect(config.quickFilters?.map((q) => q.key)).toEqual(['year', 'period_type', 'company_id', 'department_id'])
    expect(config.quickFilters?.[1].options?.map((o) => o.value)).toEqual(['1', '2', '3', '4'])
  })

  it('keeps the real 0 (whole company) as the first department filter option', () => {
    const dept = buildHeadcountPlanCrudConfig(BASE).quickFilters?.find((q) => q.key === 'department_id')
    expect(dept?.options?.[0]).toEqual({ value: '0', label: 'Toàn pháp nhân' })
    expect(dept?.options).toHaveLength(3)
  })
})
