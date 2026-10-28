import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { HeadcountPlanActual, HeadcountPlanComputed } from '../types/headcount-plan'
import { buildSubPeriods } from '../utils/headcount-plan-periods'
import { HeadcountPlanComputedTable } from './headcount-plan-computed-table'

const PERIODS = buildSubPeriods(1, 1)

const computed: HeadcountPlanComputed = {
  periods: PERIODS,
  headcount: [4, 5, 6, 6],
  items: [{ code: 'LUONG', group_id: 1, name: 'Lương vị trí', values: [10, 20, 30, 40], total: 100 }],
  groups: [{ group_id: 1, name: 'Quỹ lương', values: [10, 20, 30, 40], total: 100 }],
  total: { values: [10, 20, 30, 40], total: 100 },
  avg_per_head: 20,
}

const actual: HeadcountPlanActual = {
  values: [12_000_000, 5_000_000, null, null],
  planned_comparable: [10_000_000, 6_000_000, null, null],
  remaining: [-2_000_000, 1_000_000, null, null],
  headcount: [4, 5, null, null],
  covered_codes: ['LUONG'],
  missing_codes: ['THUONG_13'],
  months_counted: [3, 2, null, null],
}

const rowOf = (label: string) => {
  const cell = screen.getByText(label)
  const row = cell.closest('tr')
  if (!row) throw new Error(`no row ${label}`)
  return within(row)
}

describe('computed table — actual rows (saved plan only)', () => {
  it('shows actual headcount and the three money rows, future sub-periods as a real dash', () => {
    render(<HeadcountPlanComputedTable computed={computed} periods={PERIODS} showMoney isFetching={false} actual={actual} />)
    expect(rowOf('Định biên thực tế').getAllByText('—')).toHaveLength(2)
    expect(rowOf('Thực tế (phần so được)').getByText('12.000.000')).toBeInTheDocument()
    expect(rowOf('Kế hoạch phần so được').getByText('16.000.000')).toBeInTheDocument()
    //  Tổng kỳ của định biên = kỳ con cuối CÓ số (Q2 = 5), không cộng dồn người.
    expect(rowOf('Định biên thực tế').getAllByText('5')).toHaveLength(2)
  })

  it('paints an overrun (negative remaining) red and keeps a surplus plain', () => {
    render(<HeadcountPlanComputedTable computed={computed} periods={PERIODS} showMoney isFetching={false} actual={actual} />)
    const row = rowOf('Còn dư / vượt')
    expect(row.getByText('-2.000.000')).toHaveClass('text-destructive')
    expect(row.getByText('1.000.000')).not.toHaveClass('text-destructive')
  })

  it('keeps actual headcount but drops every money row when money is masked', () => {
    const masked = { ...actual, values: null, planned_comparable: null, remaining: null }
    render(
      <HeadcountPlanComputedTable computed={computed} periods={PERIODS} showMoney={false} isFetching={false} actual={masked} />,
    )
    expect(screen.getByText('Định biên thực tế')).toBeInTheDocument()
    expect(screen.queryByText('Còn dư / vượt')).not.toBeInTheDocument()
    expect(screen.queryByText('Thực tế (phần so được)')).not.toBeInTheDocument()
    expect(screen.queryByText('Tổng chi phí nhân sự')).not.toBeInTheDocument()
  })

  it('drops money rows when the server masked values even if the page thought money was visible', () => {
    render(
      <HeadcountPlanComputedTable
        computed={computed}
        periods={PERIODS}
        showMoney
        isFetching={false}
        actual={{ ...actual, values: null, planned_comparable: null, remaining: null }}
      />,
    )
    expect(screen.queryByText('Còn dư / vượt')).not.toBeInTheDocument()
  })

  it('has no actual rows on an unsaved draft, and prints the notes under the table', () => {
    render(
      <HeadcountPlanComputedTable
        computed={computed}
        periods={PERIODS}
        showMoney
        isFetching={false}
        notes={['Thực tế chưa gồm: Thưởng tháng 13.']}
      />,
    )
    expect(screen.queryByText('Định biên thực tế')).not.toBeInTheDocument()
    expect(screen.getByText('Thực tế chưa gồm: Thưởng tháng 13.')).toBeInTheDocument()
  })
})
