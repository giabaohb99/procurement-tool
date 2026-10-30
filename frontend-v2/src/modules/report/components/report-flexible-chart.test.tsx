import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { cloneElement, isValidElement, useEffect, type ReactElement, type ReactNode } from 'react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type * as RechartsModule from 'recharts'

import type { ReportGroupRow, ReportMeta, ReportTrendPoint } from '../types/report-analytics'
import { ReportFlexibleChart } from './report-flexible-chart'

//  jsdom không dựng bố cục nên `ResponsiveContainer` đo ra 0×0 và recharts không vẽ gì. Thay nó
//  bằng một khung cố định để cột/lát THẬT được vẽ ra và bấm được — phần còn lại của recharts
//  chạy nguyên bản.
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof RechartsModule>()
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactNode }) =>
      isValidElement(children)
        ? cloneElement(children as ReactElement<{ width: number; height: number }>, {
            width: 600,
            height: 400,
          })
        : null,
  }
})

const META: ReportMeta = {
  metrics: [
    { key: 'people', label: 'Số người', kind: 'int', good: null, helper: false, snapshot: false },
    { key: 'rate', label: 'Tỷ lệ', kind: 'percent', good: null, helper: false, snapshot: false },
    { key: 'end', label: 'Cuối kỳ', kind: 'int', good: null, helper: false, snapshot: true },
  ],
  dimensions: [{ key: 'department', label: 'Phòng ban' }],
  group_by: 'department',
}

const TREND: ReportTrendPoint[] = [
  { key: '1', label: 'T9', current: { people: 4 }, compare: { people: 2 } },
  { key: '2', label: 'T10', current: { people: 6 }, compare: { people: 3 } },
]

const GROUPS: ReportGroupRow[] = [
  { key: 'kt', label: 'Kế toán', current: { people: 3, rate: 10 }, compare: null },
  { key: 'kd', label: 'Kinh doanh', current: { people: 8, rate: 20 }, compare: null },
  { key: 'an', label: 'Nhóm ẩn', current: { people: null, rate: null }, compare: null },
]

let lastSearch = ''
function SearchSpy() {
  const { search } = useLocation()
  useEffect(() => {
    lastSearch = search
  }, [search])
  return null
}

type Props = Partial<Parameters<typeof ReportFlexibleChart>[0]>

function renderChart(props: Props = {}, url = '/report/test') {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <ReportFlexibleChart
        slug="test"
        meta={META}
        trend={TREND}
        groups={GROUPS}
        metric="people"
        compareMode="previous"
        isLoading={false}
        {...props}
      />
      <SearchSpy />
    </MemoryRouter>,
  )
}

describe('ReportFlexibleChart — default look', () => {
  it('starts as the old trend line of the selected metric with its compare legend', () => {
    renderChart()
    expect(screen.getByText('Xu hướng Số người')).toBeInTheDocument()
    expect(screen.getByText('Kỳ này')).toBeInTheDocument()
    expect(screen.getByText('Kỳ trước')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Đường' })).toHaveAttribute('aria-checked', 'true')
    expect(lastSearch).toBe('')
  })

  it('defaults to "by group" on a hideTrend page and hides the time option', () => {
    renderChart({ hideTrend: true, trend: [] })
    expect(screen.getByText('Số người theo Phòng ban')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Vẽ theo' })).not.toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Cột ngang' })).toHaveAttribute('aria-checked', 'true')
  })

  it('defaults to "by group" for a snapshot metric', () => {
    renderChart({
      metric: 'end',
      groups: [{ key: 'kt', label: 'Kế toán', current: { end: 7 }, compare: null }],
    })
    expect(screen.getByText('Cuối kỳ theo Phòng ban')).toBeInTheDocument()
  })

  it('draws by group when the trend does not carry the metric at all', () => {
    renderChart({ metric: 'rate' })
    expect(screen.getByText('Tỷ lệ theo Phòng ban')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Vẽ theo' })).not.toBeInTheDocument()
  })

  it('ignores chart_by=time for a snapshot metric (no fake flat line)', () => {
    renderChart(
      { metric: 'end', groups: [{ key: 'kt', label: 'Kế toán', current: { end: 7 }, compare: null }] },
      '/report/test?chart_by=time',
    )
    expect(screen.getByText('Cuối kỳ theo Phòng ban')).toBeInTheDocument()
  })

  it('says why a snapshot metric that groups do not carry cannot be drawn', () => {
    renderChart({ metric: 'end' })
    expect(
      screen.getByText('Chỉ số này chỉ có ở dòng Tổng — không chia theo nhóm được.'),
    ).toBeInTheDocument()
  })

  it('shows the skeleton while loading, without controls', () => {
    renderChart({ isLoading: true, trend: [], groups: [] })
    expect(screen.queryByRole('button', { name: 'Tải ảnh PNG' })).not.toBeInTheDocument()
  })
})

describe('ReportFlexibleChart — switching and URL state', () => {
  it('switching to the group axis writes chart_by only and resets the type to hbar', async () => {
    renderChart()
    await userEvent.click(screen.getByRole('combobox', { name: 'Vẽ theo' }))
    await userEvent.click(screen.getByRole('option', { name: 'Phòng ban' }))
    expect(new URLSearchParams(lastSearch).get('chart_by')).toBe('group')
    expect(new URLSearchParams(lastSearch).has('chart_type')).toBe(false)
    expect(screen.getByText('Số người theo Phòng ban')).toBeInTheDocument()
    expect(screen.getByText('1 nhóm bị che không vẽ.')).toBeInTheDocument()
  })

  it('opens the exact view of a shared link', () => {
    renderChart({}, '/report/test?chart_by=group&chart_type=donut&chart_top=5')
    expect(screen.getByRole('radio', { name: 'Vành khuyên' })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByRole('combobox', { name: 'Số nhóm hiện' })).toHaveTextContent('Top 5')
  })

  it('keeps the other page params when writing chart params', async () => {
    renderChart({}, '/report/test?group_by=department&preset=this_year')
    await userEvent.click(screen.getByRole('radio', { name: 'Cột' }))
    const params = new URLSearchParams(lastSearch)
    expect(params.get('chart_type')).toBe('bar')
    expect(params.get('preset')).toBe('this_year')
    expect(params.get('group_by')).toBe('department')
  })

  it('disables donut for a percent metric', () => {
    renderChart({ metric: 'rate' }, '/report/test?chart_by=group')
    expect(screen.getByRole('radio', { name: 'Vành khuyên' })).toBeDisabled()
  })
})

describe('ReportFlexibleChart — click to drill down', () => {
  it('opens the list of the clicked bar group', () => {
    const onSelectGroup = vi.fn()
    const { container } = renderChart({ onSelectGroup }, '/report/test?chart_by=group')
    const bars = container.querySelectorAll('.recharts-bar-rectangle')
    expect(bars.length).toBe(2)
    //  Đã xếp lớn → nhỏ: cột đầu là Kinh doanh (8), không phải Kế toán (thứ tự máy chủ).
    const first = bars[0]?.querySelector('path') ?? bars[0]
    if (!first) throw new Error('no bar')
    fireEvent.click(first)
    expect(onSelectGroup).toHaveBeenCalledWith({ key: 'kd', label: 'Kinh doanh' })
  })

  it('opens the list from a donut legend button (keyboard path)', async () => {
    const onSelectGroup = vi.fn()
    renderChart({ onSelectGroup }, '/report/test?chart_by=group&chart_type=donut')
    await userEvent.click(screen.getByRole('button', { name: 'Xem danh sách Kế toán từ biểu đồ' }))
    expect(onSelectGroup).toHaveBeenCalledWith({ key: 'kt', label: 'Kế toán' })
  })

  it('never offers the merged "Khác" slice as a list', () => {
    const onSelectGroup = vi.fn()
    const groups = ['a', 'b', 'c', 'd', 'e', 'f'].map((k, i) => ({
      key: k,
      label: k,
      current: { people: i + 1 },
      compare: null,
    }))
    renderChart({ onSelectGroup, groups }, '/report/test?chart_by=group&chart_type=donut&chart_top=5')
    expect(screen.getByText('Khác (1 nhóm)')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xem danh sách Khác/ })).not.toBeInTheDocument()
  })

  it('has no clickable legend when the page offers no drilldown', () => {
    renderChart({}, '/report/test?chart_by=group&chart_type=donut')
    expect(screen.queryByRole('button', { name: /Xem danh sách/ })).not.toBeInTheDocument()
  })
})
