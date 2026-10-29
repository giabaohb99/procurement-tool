import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { ReportMeta, ReportMetricMeta, ReportTrendPoint } from '../types/report-analytics'
import { ReportKpiRow } from './report-kpi-row'

function metric(
  overrides: Partial<ReportMetricMeta> & Pick<ReportMetricMeta, 'key' | 'label' | 'kind'>,
): ReportMetricMeta {
  return { good: null, helper: false, snapshot: false, ...overrides }
}

const META: ReportMeta = {
  metrics: [
    metric({ key: 'spend', label: 'Chi phí', kind: 'money', good: 'down' }),
    metric({ key: 'debt', label: 'Công nợ', kind: 'money', good: 'down', snapshot: true }),
    metric({ key: 'on_time_rate', label: 'Giao đúng hạn', kind: 'percent', good: 'up' }),
    //  Không có mặt trong `totals.current` — mô phỏng chỉ số dẫn xuất mẫu số 0.
    metric({ key: 'avg_rate', label: 'Tỷ lệ TB', kind: 'percent', good: 'up' }),
  ],
  dimensions: [],
  group_by: 'none',
}

const TOTALS = {
  current: { spend: 120, debt: 50_000_000, on_time_rate: 74.5 },
  compare: { spend: 100, debt: 40_000_000, on_time_rate: 79.1 },
}

//  `debt` mang giá trị KHÔNG-0 ở đây dù hợp đồng thật của `snapshot` là vắng
//  hẳn khóa đó trong `trend[]` — cố ý, để chứng minh sparkline bị chặn bởi
//  chính cờ `metric.snapshot`, không phải trùng hợp "toàn số 0 nên không vẽ".
const TREND: ReportTrendPoint[] = [
  { key: 'd1', label: '01/09', current: { spend: 10, on_time_rate: 70, debt: 999 }, compare: null },
  { key: 'd2', label: '02/09', current: { spend: 12, on_time_rate: 72, debt: 888 }, compare: null },
]

function renderRow(overrides: Partial<Parameters<typeof ReportKpiRow>[0]> = {}) {
  return render(
    <ReportKpiRow
      meta={META}
      kpis={['spend', 'debt', 'on_time_rate', 'avg_rate']}
      totals={TOTALS}
      trend={TREND}
      compareMode="previous"
      selectedMetric="spend"
      onSelectMetric={vi.fn()}
      isLoading={false}
      {...overrides}
    />,
  )
}

describe('ReportKpiRow — kind: percent uses percentage-point delta, not relative %', () => {
  it('shows "−4,6 điểm" for 74,5 vs 79,1 (kỳ trước), not "−5,8%"', () => {
    renderRow()
    expect(screen.getByText('−4,6 điểm')).toBeInTheDocument()
  })
})

describe('ReportKpiRow — snapshot metric: no sparkline, not clickable', () => {
  it('drops the sparkline even with non-zero trend data for that key', () => {
    const { container } = renderRow()
    //  Chỉ `spend` và `on_time_rate` có sparkline; `debt` (snapshot) và
    //  `avg_rate` (dẫn xuất null) đều không — dù `debt` có dữ liệu KHÔNG-0.
    expect(container.querySelectorAll('.h-10')).toHaveLength(2)
  })

  it('renders the snapshot card without a button role (not selectable for the trend chart)', () => {
    renderRow()
    expect(screen.getByRole('button', { name: /Chi phí/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Công nợ/ })).not.toBeInTheDocument()
    expect(screen.getByText('Số dư hiện tại — không có xu hướng theo kỳ')).toBeInTheDocument()
  })
})

//  duoc-CR-688 — chỉ số thời điểm mà nhóm có số (vd «Định biên cuối kỳ» theo phòng ban) bấm
//  được để biểu đồ linh hoạt vẽ THEO NHÓM; nhóm không có số thì thẻ vẫn tĩnh như trên.
describe('ReportKpiRow — snapshot metric drawable by group', () => {
  it('makes the snapshot card selectable when groups carry it, and reports its key', async () => {
    const onSelectMetric = vi.fn()
    renderRow({ onSelectMetric, groupedSnapshotMetrics: new Set(['debt']) })
    const card = screen.getByRole('button', { name: /Công nợ/ })
    card.click()
    expect(onSelectMetric).toHaveBeenCalledWith('debt')
    expect(screen.getByText('Số dư hiện tại — bấm để vẽ theo nhóm')).toBeInTheDocument()
  })

  it('shows the selected ring on a grouped snapshot card', () => {
    renderRow({ selectedMetric: 'debt', groupedSnapshotMetrics: new Set(['debt']) })
    expect(screen.getByRole('button', { name: /Công nợ/ })).toHaveAttribute('aria-pressed', 'true')
  })

  it('keeps the snapshot card static when the set names a different metric', () => {
    renderRow({ groupedSnapshotMetrics: new Set(['spend']) })
    expect(screen.queryByRole('button', { name: /Công nợ/ })).not.toBeInTheDocument()
  })
})

describe('ReportKpiRow — null derived metric (zero denominator) renders — with no change badge', () => {
  it('shows the dash instead of 0% and skips the ±change line entirely', () => {
    renderRow()
    const card = screen.getByText('Tỷ lệ TB').closest('[data-slot="card"]')
    expect(card).toHaveTextContent('—')
    //  Không có dòng thay đổi nào (không mũi tên, không %/điểm) cho thẻ này.
    expect(card).not.toHaveTextContent('điểm')
  })
})

//  duoc-CR-687 — một số ĐẾM (`int`) có thể về `null` khi backend che nhóm; thẻ phải ra «—»,
//  không «0», và không vẽ mức thay đổi dù kỳ trước có số.
describe('ReportKpiRow — null count metric renders a dash', () => {
  it('shows — for a null int total even when the compare period has a value', () => {
    renderRow({
      meta: { metrics: [metric({ key: 'people', label: 'Tổng lao động', kind: 'int' })], dimensions: [], group_by: 'none' },
      kpis: ['people'],
      totals: { current: { people: null }, compare: { people: 12 } },
      trend: [],
    })
    const card = screen.getByText('Tổng lao động').closest('[data-slot="card"]')
    expect(card).toHaveTextContent('—')
    expect(card).not.toHaveTextContent('0')
    expect(card).not.toHaveTextContent('%')
  })
})
