import { fireEvent, render, screen, within } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { describe, expect, it } from 'vitest'

import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HeadcountPlanActual, HeadcountPlanComputed } from '../types/headcount-plan'
import { buildSubPeriods } from '../utils/headcount-plan-periods'
import { HeadcountPlanComputedTable } from './headcount-plan-computed-table'

const M = COST_CALC_METHOD_CODE
const PERIODS = buildSubPeriods(1, 1)

const computed: HeadcountPlanComputed = {
  periods: PERIODS,
  headcount: [4, 5, 6, 6],
  items: [
    { code: 'LUONG', group_id: 1, name: 'Lương', values: [10, 20, 30, 40], total: 100 },
    { code: 'BH', group_id: 2, name: 'Bảo hiểm + công đoàn', values: [1, 2, 3, 4], total: 10 },
    { code: 'QUA', group_id: 3, name: 'Quà 8/3', values: [5, 0, 0, 0], total: 5 },
  ],
  groups: [],
  total: { values: [16, 22, 33, 44], total: 115 },
  avg_per_head: 20,
}
const COST_ITEMS = [
  { code: 'LUONG', calc_method: M.PER_HEAD_MONTH },
  { code: 'BH', calc_method: M.PERCENT_OF },
  { code: 'QUA', calc_method: M.PER_HEAD_ONCE },
]

const actual: HeadcountPlanActual = {
  values: [12_000_000, 5_000_000, null, null],
  planned_comparable: [10_000_000, 6_000_000, null, null],
  remaining: [-2_000_000, 1_000_000, null, null],
  headcount: [4, 5, null, null],
  covered_codes: ['LUONG'],
  missing_codes: ['THUONG_13'],
  months_counted: [3, 2, null, null],
}

const renderTable = (over: Partial<ComponentProps<typeof HeadcountPlanComputedTable>> = {}) =>
  render(
    <HeadcountPlanComputedTable
      computed={computed}
      periods={PERIODS}
      totalLabel="Cả năm"
      costItems={COST_ITEMS}
      headcounts={[4, 5, 6, 6]}
      showMoney
      isFetching={false}
      {...over}
    />,
  )

const rowOf = (label: string) => {
  const cell = screen.getByText(label)
  const row = cell.closest('tr')
  if (!row) throw new Error(`no row ${label}`)
  return within(row)
}

describe('Tổng table — rows by kind of cost', () => {
  it('shows headcount, one row per kind and the grand total under «Cả năm»', () => {
    renderTable()
    expect(screen.getByText('Cả năm')).toBeInTheDocument()
    expect(rowOf('Số người').getAllByText('6')).toHaveLength(3)
    expect(rowOf('Lương + phụ cấp').getByText('100')).toBeInTheDocument()
    expect(rowOf('Bảo hiểm').getByText('10')).toBeInTheDocument()
    expect(rowOf('Thưởng, quà, chi khác').getAllByText('5')).toHaveLength(2)
    expect(rowOf('TỔNG').getByText('115')).toBeInTheDocument()
  })

  it('opens a row into its individual costs on click', () => {
    renderTable()
    expect(screen.queryByText('Quà 8/3')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Thưởng, quà, chi khác/ }))
    expect(screen.getByText('Quà 8/3')).toBeInTheDocument()
  })

  it('keeps only the headcount row when money is hidden — no row of dashes that reads «no salary yet»', () => {
    renderTable({ showMoney: false, computed: { ...computed, items: [], total: null, money_hidden: true } })
    expect(screen.getByText('Số người')).toBeInTheDocument()
    expect(screen.queryByText('Lương + phụ cấp')).not.toBeInTheDocument()
    expect(screen.queryByText('TỔNG')).not.toBeInTheDocument()
  })

  it('still shows headcount before the engine has answered (new plan, no company yet)', () => {
    renderTable({ computed: null, headcounts: [1, 1, 2, 2] })
    expect(rowOf('Số người').getAllByText('2')).toHaveLength(3)
    expect(rowOf('TỔNG').getAllByText('—')).toHaveLength(5)
  })
})

describe('Tổng table — actual rows (saved plan only)', () => {
  it('shows actual headcount and the three money rows, future sub-periods as a real dash', () => {
    renderTable({ actual })
    expect(rowOf('Số người thực tế').getAllByText('—')).toHaveLength(2)
    expect(rowOf('Thực tế (phần so được)').getByText('12.000.000')).toBeInTheDocument()
    expect(rowOf('Kế hoạch phần so được').getByText('16.000.000')).toBeInTheDocument()
    //  Tổng kỳ của số người = kỳ con cuối CÓ số (Q2 = 5), không cộng dồn người.
    expect(rowOf('Số người thực tế').getAllByText('5')).toHaveLength(2)
  })

  it('paints an overrun (negative remaining) red and keeps a surplus plain', () => {
    renderTable({ actual })
    const row = rowOf('Còn dư / vượt')
    expect(row.getByText('-2.000.000')).toHaveClass('text-destructive')
    expect(row.getByText('1.000.000')).not.toHaveClass('text-destructive')
  })

  it('keeps actual headcount but drops every money row when money is masked', () => {
    renderTable({ showMoney: false, actual: { ...actual, values: null, planned_comparable: null, remaining: null } })
    expect(screen.getByText('Số người thực tế')).toBeInTheDocument()
    expect(screen.queryByText('Còn dư / vượt')).not.toBeInTheDocument()
    expect(screen.queryByText('Thực tế (phần so được)')).not.toBeInTheDocument()
  })

  it('drops money rows when the server masked values even if the page thought money was visible', () => {
    renderTable({ actual: { ...actual, values: null, planned_comparable: null, remaining: null } })
    expect(screen.queryByText('Còn dư / vượt')).not.toBeInTheDocument()
  })

  it('has no actual rows on an unsaved draft, and prints the notes under the table', () => {
    renderTable({ notes: ['Thực tế chưa gồm: Thưởng tháng 13.'] })
    expect(screen.queryByText('Số người thực tế')).not.toBeInTheDocument()
    expect(screen.getByText('Thực tế chưa gồm: Thưởng tháng 13.')).toBeInTheDocument()
  })
})
