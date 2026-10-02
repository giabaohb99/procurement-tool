import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportGroupRow, ReportMeta, ReportMetricMeta } from '../types/report-analytics'
import { ReportGroupedTable } from './report-grouped-table'

function metric(
  overrides: Partial<ReportMetricMeta> & Pick<ReportMetricMeta, 'key' | 'label' | 'kind'>,
): ReportMetricMeta {
  return { good: null, helper: false, snapshot: false, ...overrides }
}

const META: ReportMeta = {
  metrics: [
    metric({ key: 'spend', label: 'Chi phí', kind: 'money', good: 'down' }),
    metric({ key: 'debt', label: 'Công nợ', kind: 'money', good: 'down', snapshot: true }),
    metric({ key: 'lines', label: 'Số dòng', kind: 'int', good: 'up' }),
    metric({ key: 'helperx', label: 'Mẫu số phụ', kind: 'int', helper: true }),
  ],
  dimensions: [{ key: 'department', label: 'Bộ phận' }],
  group_by: 'department',
}

const KPIS = ['spend', 'debt']
const TOTALS = {
  current: { spend: 120, debt: 50_000_000, lines: 40 },
  compare: { spend: 100, lines: 30 },
}
//  `groups[].current` KHÔNG có khóa `debt` — đúng hợp đồng backend cho `snapshot`.
const GROUPS: ReportGroupRow[] = [
  {
    key: 'kd',
    label: 'Kinh doanh',
    current: { spend: 70, lines: 25 },
    compare: { spend: 60, lines: 20 },
  },
]

function renderTable(overrides: Partial<ComponentProps<typeof ReportGroupedTable>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <TooltipProvider>
          <ReportGroupedTable
            meta={META}
            kpis={KPIS}
            totals={TOTALS}
            groups={GROUPS}
            compare="previous"
            groupBy="department"
            onGroupByChange={vi.fn()}
            isLoading={false}
            isError={false}
            storageKey="report.__test__.v4"
            {...overrides}
          />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReportGroupedTable — default visible columns are exactly the page kpis', () => {
  it('shows dimension + kpis in order, hides the non-kpi metric and drops the helper entirely', () => {
    renderTable()
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent)
    expect(headers).toEqual(['Bộ phận', 'Chi phí', 'Công nợ'])
    //  `lines` không nằm trong `kpis` — vẫn tồn tại (bật lại được qua menu
    //  "Cột") nhưng KHÔNG hiện sẵn, và `helperx` không bao giờ hiện.
    expect(screen.queryByText('Số dòng')).not.toBeInTheDocument()
    expect(screen.queryByText('Mẫu số phụ')).not.toBeInTheDocument()
  })
})

describe('ReportGroupedTable — group rows show only the value, no inline change text', () => {
  it('renders the group value without a visible ±% next to it (change lives in the tooltip)', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    const groupRow = rows[2] // 0 = header, 1 = Tổng, 2 = Kinh doanh
    expect(groupRow).toHaveTextContent('Kinh doanh')
    //  120 vs 100 kỳ trước của Tổng = "+20%" — dòng NHÓM không được có bất kỳ
    //  chuỗi ±% nào cạnh giá trị của nó.
    expect(within(groupRow).queryByText(/%/)).not.toBeInTheDocument()
  })

  it('reveals the previous value and the change only inside the tooltip on hover', async () => {
    const user = userEvent.setup()
    renderTable()
    const rows = screen.getAllByRole('row')
    const groupRow = rows[2]
    //  `spend` là `kind: 'money'` — giá trị đủ hiện kèm "đ" (`formatReportMetricValue`).
    const valueCell = within(groupRow).getByText('70 đ')
    await user.hover(valueCell)
    expect(await screen.findByText('Kỳ trước: 60 đ')).toBeInTheDocument()
    expect(screen.getByText('Thay đổi: +16,7%')).toBeInTheDocument()
  })
})

describe('ReportGroupedTable — the Tổng row is the only one with a visible change pill', () => {
  it('shows a colored change pill under the Tổng value (spend up is bad, good: down)', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    const totalRow = rows[1]
    expect(totalRow).toHaveTextContent('Tổng')
    const pill = within(totalRow).getByText('+20%')
    expect(pill.closest('span')).toHaveClass('text-destructive')
  })

  it('pins the Tổng row first with a bottom border separating it from group rows', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Tổng')
    expect(rows[1].className).toContain('border-b-2')
  })
})

describe('ReportGroupedTable — snapshot metric: value only on Tổng, — on group rows', () => {
  it('renders the real number on Tổng and a dash on every group row', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    const totalRow = rows[1]
    const groupRow = rows[2]
    expect(within(totalRow).getByText('50.000.000 đ')).toBeInTheDocument()
    expect(within(groupRow).getByText('—')).toBeInTheDocument()
  })
})

describe('ReportGroupedTable — rows with all-zero current values are muted and sorted last', () => {
  it('renders an all-zero group row (present only because the compare period had data) after active rows', () => {
    const groupsWithInactive: ReportGroupRow[] = [
      {
        key: 'kt',
        label: 'Kế toán',
        current: { spend: 0, lines: 0 },
        compare: { spend: 50, lines: 5 },
      },
      ...GROUPS,
    ]
    renderTable({ groups: groupsWithInactive })
    const rows = screen.getAllByRole('row')
    // 0 = header, 1 = Tổng, 2 = active (Kinh doanh), 3 = inactive (Kế toán).
    expect(rows[2]).toHaveTextContent('Kinh doanh')
    expect(rows[3]).toHaveTextContent('Kế toán')
    const inactiveLabel = within(rows[3]).getByText('Kế toán')
    expect(inactiveLabel).toHaveClass('text-muted-foreground')
  })
})
