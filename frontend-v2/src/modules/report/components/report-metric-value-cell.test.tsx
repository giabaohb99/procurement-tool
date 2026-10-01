import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportMetricMeta } from '../types/report-analytics'
import type { ReportTableRow } from '../utils/build-report-table-rows'
import { KpiTrendCard } from './kpi-trend-card'
import { ReportMetricValueCell } from './report-metric-value-cell'
import { describeMetricChange } from '../utils/report-period-comparison'

const metric: ReportMetricMeta = {
  key: 'requests',
  label: 'Số đơn',
  kind: 'int',
  good: 'up',
  helper: false,
  snapshot: false,
}

function totalRow(current: number | null, previous: number | null): ReportTableRow {
  return {
    key: '__total__',
    label: 'Tổng',
    current: { requests: current },
    compare: { requests: previous },
    isTotal: true,
    isEmpty: false,
  }
}

function renderCell(row: ReportTableRow, compare: 'previous' | 'none' = 'previous') {
  return render(
    <TooltipProvider>
      <ReportMetricValueCell row={row} metric={metric} compare={compare} />
    </TooltipProvider>,
  )
}

//  Đại ca chê 01/10/2026: dòng Tổng mỗi ô một badge «Mới» bên dưới con số, ô có
//  ô không, số lệch hàng nhau. Chỉ một mức thay đổi THẬT mới được đứng cạnh số.
describe('ReportMetricValueCell — total row', () => {
  it('shows the signed change on the same line when there is a real change', () => {
    renderCell(totalRow(12, 10))
    expect(screen.getByText('+20%')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('does not print "Mới" when the previous period was 0', () => {
    renderCell(totalRow(2, 0))
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.queryByText('Mới')).not.toBeInTheDocument()
  })

  it('does not print "Không đổi" when both periods are equal', () => {
    renderCell(totalRow(5, 5))
    expect(screen.queryByText('Không đổi')).not.toBeInTheDocument()
  })

  it('prints only the value when comparison is off', () => {
    renderCell(totalRow(12, 10), 'none')
    expect(screen.queryByText('+20%')).not.toBeInTheDocument()
  })

  it('shows a dash, not 0, for a null derived value', () => {
    renderCell(totalRow(null, 3))
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})

describe('KpiTrendCard — change line', () => {
  it('says the previous period had nothing instead of a grey "Mới" pill', () => {
    render(
      <KpiTrendCard
        label="Số đơn"
        value="2"
        changeDescription={describeMetricChange(2, 0, 'int', 'up')}
        changeCaption="so với kỳ trước"
      />,
    )
    expect(screen.getByText('Kỳ trước chưa phát sinh')).toBeInTheDocument()
    expect(screen.queryByText('Mới')).not.toBeInTheDocument()
  })

  it('says "Bằng năm trước" for a flat change against last year', () => {
    render(
      <KpiTrendCard
        label="Số đơn"
        value="5"
        changeDescription={describeMetricChange(5, 5, 'int', 'up')}
        changeCaption="so với năm trước"
      />,
    )
    expect(screen.getByText('Bằng năm trước')).toBeInTheDocument()
  })

  it('renders the eyebrow above the label so bare labels keep their source', () => {
    render(<KpiTrendCard eyebrow="Báo cáo Đặt xe" label="Yêu cầu" value="356" />)
    expect(screen.getByText('Báo cáo Đặt xe')).toBeInTheDocument()
    expect(screen.getByText('Yêu cầu')).toBeInTheDocument()
  })

  it('skips a sparkline that has only one non-zero point', () => {
    const { container } = render(<KpiTrendCard label="Số đơn" value="1" sparkline={[0, 0, 1, 0]} />)
    expect(container.querySelector('[aria-hidden].h-10')).toBeNull()
  })
})
