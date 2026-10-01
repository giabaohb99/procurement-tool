import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useSearchParams } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { useReportFilters } from './use-report-filters'

function Probe() {
  const filters = useReportFilters({ defaultGroupBy: 'department' })
  const [searchParams] = useSearchParams()

  return (
    <>
      <span data-testid="url">{searchParams.toString()}</span>
      <span data-testid="preset">{filters.preset}</span>
      <span data-testid="compare">{filters.compare}</span>
      <span data-testid="groupBy">{filters.groupBy}</span>
      <span data-testid="companyId">{filters.companyId}</span>
      <span data-testid="from">{filters.from}</span>
      <span data-testid="to">{filters.to}</span>
      <span data-testid="queryParams">{JSON.stringify(filters.queryParams)}</span>
      <button type="button" onClick={() => filters.setPreset('last_7_days')}>
        7 ngày qua
      </button>
      <button type="button" onClick={() => filters.setPreset('custom')}>
        Tùy chọn
      </button>
      <button type="button" onClick={() => filters.setCustomRange('2026-08-01', '2026-08-31')}>
        Áp dụng khoảng
      </button>
      <button type="button" onClick={() => filters.setCompare('none')}>
        Không so sánh
      </button>
      <button type="button" onClick={() => filters.setGroupBy('item_group')}>
        Xem theo nhóm hàng
      </button>
      <button type="button" onClick={() => filters.setCompanyId('7')}>
        Công ty 7
      </button>
      <button
        type="button"
        onClick={() =>
          filters.applyPeriod({ preset: 'this_year', from: '', to: '', compare: 'year' })
        }
      >
        Áp dụng: Năm nay, so cùng kỳ
      </button>
      <button
        type="button"
        onClick={() =>
          filters.applyPeriod({
            preset: 'custom',
            from: '2026-03-01',
            to: '2026-03-31',
            compare: 'none',
          })
        }
      >
        Áp dụng: Tùy chọn 03/2026, không so sánh
      </button>
      <button type="button" onClick={() => filters.resetFilters({ groupBy: true, period: true })}>
        Đặt lại bộ lọc (kèm kỳ)
      </button>
      <button type="button" onClick={() => filters.resetFilters({ groupBy: true })}>
        Đặt lại bộ lọc (chỉ Xem theo)
      </button>
    </>
  )
}

function build(url = '/report/test') {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Probe />
    </MemoryRouter>,
  )
}

//  H2-FE (review 01/10/2026) — trang có `ReportPageConfig.defaultPreset` (vd
//  Quỹ phép năm → "this_year") phải mở sẵn ở preset ĐÓ, không phải mặc định
//  chung "this_month", và "Đặt lại bộ lọc" cũng phải đưa kỳ về ĐÚNG preset đó.
function ProbeWithDefaultPreset({ defaultPreset }: { defaultPreset?: string }) {
  const filters = useReportFilters({ defaultGroupBy: 'department', defaultPreset })
  return (
    <>
      <span data-testid="preset">{filters.preset}</span>
      <button type="button" onClick={() => filters.setPreset('this_year')}>
        Năm nay
      </button>
      <button type="button" onClick={() => filters.setPreset('today')}>
        Hôm nay
      </button>
      <button type="button" onClick={() => filters.resetFilters({ period: true })}>
        Đặt lại kỳ
      </button>
    </>
  )
}

function buildWithDefaultPreset(defaultPreset?: string, url = '/report/test') {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <ProbeWithDefaultPreset defaultPreset={defaultPreset} />
    </MemoryRouter>,
  )
}

describe('useReportFilters — defaultPreset (page-level override)', () => {
  it('opens at the page-configured preset instead of the shared default, with a clean URL', () => {
    buildWithDefaultPreset('this_year')
    expect(screen.getByTestId('preset')).toHaveTextContent('this_year')
  })

  it('selecting the page default back clears the URL param (it is the implicit default now)', async () => {
    const user = userEvent.setup()
    buildWithDefaultPreset('this_year')
    await user.click(screen.getByRole('button', { name: 'Hôm nay' }))
    expect(screen.getByTestId('preset')).toHaveTextContent('today')
    await user.click(screen.getByRole('button', { name: 'Năm nay' }))
    expect(screen.getByTestId('preset')).toHaveTextContent('this_year')
  })

  it('"Đặt lại bộ lọc" returns to the page default, not the shared "this_month"', async () => {
    const user = userEvent.setup()
    buildWithDefaultPreset('this_year')
    await user.click(screen.getByRole('button', { name: 'Hôm nay' }))
    await user.click(screen.getByRole('button', { name: 'Đặt lại kỳ' }))
    expect(screen.getByTestId('preset')).toHaveTextContent('this_year')
  })

  it('an invalid defaultPreset silently falls back to "this_month" instead of breaking', () => {
    buildWithDefaultPreset('khong-ton-tai')
    expect(screen.getByTestId('preset')).toHaveTextContent('this_month')
  })

  it('omitting defaultPreset keeps the shared "this_month" default', () => {
    buildWithDefaultPreset(undefined)
    expect(screen.getByTestId('preset')).toHaveTextContent('this_month')
  })
})

describe('useReportFilters — defaults', () => {
  it('defaults to preset=this_month, compare=previous, groupBy=defaultGroupBy with a clean URL', () => {
    build()
    expect(screen.getByTestId('preset')).toHaveTextContent('this_month')
    expect(screen.getByTestId('compare')).toHaveTextContent('previous')
    expect(screen.getByTestId('groupBy')).toHaveTextContent('department')
    expect(screen.getByTestId('companyId')).toHaveTextContent('all')
    expect(screen.getByTestId('url')).toBeEmptyDOMElement()
  })

  it('sends the default filters as explicit backend params even though the URL stays clean', () => {
    build()
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params).toMatchObject({
      preset: 'this_month',
      compare: 'previous',
      group_by: 'department',
    })
    expect(params).not.toHaveProperty('date_from')
    expect(params).not.toHaveProperty('company_id')
  })
})

describe('useReportFilters — legacy ?year= links', () => {
  it('maps a bare ?year=2025 to preset=custom with the full calendar year, without rewriting the URL', () => {
    build('/report/test?year=2025')
    expect(screen.getByTestId('preset')).toHaveTextContent('custom')
    expect(screen.getByTestId('from')).toHaveTextContent('2025-01-01')
    expect(screen.getByTestId('to')).toHaveTextContent('2025-12-31')
    //  Suy ra lúc ĐỌC — URL hiển thị vẫn còn `year=2025`, không bị viết đè.
    expect(screen.getByTestId('url')).toHaveTextContent('year=2025')
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params).toMatchObject({
      preset: 'custom',
      date_from: '2025-01-01',
      date_to: '2025-12-31',
    })
    expect(params).not.toHaveProperty('year')
  })

  it('ignores ?year= once an explicit ?preset= is present', () => {
    build('/report/test?year=2025&preset=today')
    expect(screen.getByTestId('preset')).toHaveTextContent('today')
  })

  it('changing any filter drops the legacy year param for good', async () => {
    const user = userEvent.setup()
    build('/report/test?year=2025')
    await user.click(screen.getByRole('button', { name: '7 ngày qua' }))
    expect(screen.getByTestId('url')).not.toHaveTextContent('year=')
    expect(screen.getByTestId('preset')).toHaveTextContent('last_7_days')
  })
})

describe('useReportFilters — setPreset', () => {
  it('writes a non-default preset and clears the URL when picking the default back', async () => {
    const user = userEvent.setup()
    build()
    await user.click(screen.getByRole('button', { name: '7 ngày qua' }))
    expect(screen.getByTestId('url')).toHaveTextContent('preset=last_7_days')
    expect(screen.getByTestId('url')).not.toHaveTextContent('date_from')
  })

  it('switching to "custom" seeds a non-empty date range instead of sending an empty one', async () => {
    const user = userEvent.setup()
    build()
    await user.click(screen.getByRole('button', { name: 'Tùy chọn' }))
    expect(screen.getByTestId('preset')).toHaveTextContent('custom')
    expect(screen.getByTestId('from')).not.toBeEmptyDOMElement()
    expect(screen.getByTestId('to')).not.toBeEmptyDOMElement()
  })
})

describe('useReportFilters — setCustomRange', () => {
  it('applies a chosen range and switches preset to custom in one URL write', async () => {
    const user = userEvent.setup()
    build()
    await user.click(screen.getByRole('button', { name: 'Áp dụng khoảng' }))
    expect(screen.getByTestId('preset')).toHaveTextContent('custom')
    expect(screen.getByTestId('from')).toHaveTextContent('2026-08-01')
    expect(screen.getByTestId('to')).toHaveTextContent('2026-08-31')
  })
})

describe('useReportFilters — extra page filters ride along on the URL', () => {
  it('forwards an unrelated URL param (a page-specific extra filter) into queryParams untouched', () => {
    build('/report/test?department_id=12')
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params.department_id).toBe('12')
  })
})

describe('useReportFilters — compare / groupBy / company', () => {
  it('setCompare / setGroupBy / setCompanyId each write independently without clobbering the others', async () => {
    const user = userEvent.setup()
    build()
    await user.click(screen.getByRole('button', { name: 'Không so sánh' }))
    await user.click(screen.getByRole('button', { name: 'Xem theo nhóm hàng' }))
    await user.click(screen.getByRole('button', { name: 'Công ty 7' }))

    expect(screen.getByTestId('compare')).toHaveTextContent('none')
    expect(screen.getByTestId('groupBy')).toHaveTextContent('item_group')
    expect(screen.getByTestId('companyId')).toHaveTextContent('7')
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params).toMatchObject({ compare: 'none', group_by: 'item_group', company_id: '7' })
  })
})

//  M6 — chốt cho bẫy đã ghi ở JSDoc của `resetFilters`: TRƯỚC đây trang lỗi gọi
//  `setGroupBy` rồi `setPreset` liên tiếp trong cùng một lần bấm, và lượt ghi
//  URL thứ hai đọc lại URL CŨ nên xóa mất thay đổi của lượt đầu. `resetFilters`
//  phải ghi CẢ HAI trong một lượt duy nhất.
describe('useReportFilters — resetFilters writes group_by AND period in one URL write', () => {
  it('clears both group_by and the custom period together, not just the last one', async () => {
    const user = userEvent.setup()
    build('/report/test?group_by=supplier&preset=custom&date_from=2001-01-01&date_to=2001-01-31')

    await user.click(screen.getByRole('button', { name: 'Đặt lại bộ lọc (kèm kỳ)' }))

    expect(screen.getByTestId('groupBy')).toHaveTextContent('department')
    expect(screen.getByTestId('preset')).toHaveTextContent('this_month')
    expect(screen.getByTestId('from')).toBeEmptyDOMElement()
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params).not.toHaveProperty('date_from')
    expect(params.group_by).toBe('department')
  })

  it('leaves the period untouched when only group_by is asked to reset', async () => {
    const user = userEvent.setup()
    build('/report/test?group_by=supplier&preset=custom&date_from=2001-01-01&date_to=2001-01-31')

    await user.click(screen.getByRole('button', { name: 'Đặt lại bộ lọc (chỉ Xem theo)' }))

    expect(screen.getByTestId('groupBy')).toHaveTextContent('department')
    expect(screen.getByTestId('preset')).toHaveTextContent('custom')
    expect(screen.getByTestId('from')).toHaveTextContent('2001-01-01')
  })
})

//  `ReportPeriodControl` gói preset + khoảng ngày tùy chọn + so sánh vào MỘT
//  nút "Áp dụng" — `applyPeriod` phải ghi cả ba trong ĐÚNG MỘT lượt
//  `setSearchParams`, đúng bẫy đã ghi ở JSDoc của nó (hai lượt liên tiếp thì
//  lượt sau đọc URL CŨ và đè mất lượt trước — lỗi thật ở màn Lịch nghỉ).
describe('useReportFilters — applyPeriod writes preset + compare (+ date range) in one URL write', () => {
  it('writes a non-default preset and compare together from a single call', async () => {
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('button', { name: 'Áp dụng: Năm nay, so cùng kỳ' }))

    expect(screen.getByTestId('preset')).toHaveTextContent('this_year')
    expect(screen.getByTestId('compare')).toHaveTextContent('year')
    const params = JSON.parse(screen.getByTestId('queryParams').textContent ?? '{}')
    expect(params).toMatchObject({ preset: 'this_year', compare: 'year' })
    expect(params).not.toHaveProperty('date_from')
  })

  it('includes date_from/date_to only for preset=custom, and clears compare back to default cleanly', async () => {
    const user = userEvent.setup()
    build()

    await user.click(
      screen.getByRole('button', { name: 'Áp dụng: Tùy chọn 03/2026, không so sánh' }),
    )

    expect(screen.getByTestId('preset')).toHaveTextContent('custom')
    expect(screen.getByTestId('from')).toHaveTextContent('2026-03-01')
    expect(screen.getByTestId('to')).toHaveTextContent('2026-03-31')
    expect(screen.getByTestId('compare')).toHaveTextContent('none')
    //  `compare=none` không phải mặc định (`previous`) nên PHẢI còn trên URL —
    //  khác `preset`/`date_from`/`date_to`, những khóa này không hề bị xóa nhầm.
    expect(screen.getByTestId('url')).toHaveTextContent('compare=none')
  })

  it('does not clobber group_by or company_id already on the URL', async () => {
    const user = userEvent.setup()
    build('/report/test?group_by=supplier&company_id=7')

    await user.click(screen.getByRole('button', { name: 'Áp dụng: Năm nay, so cùng kỳ' }))

    expect(screen.getByTestId('groupBy')).toHaveTextContent('supplier')
    expect(screen.getByTestId('companyId')).toHaveTextContent('7')
  })
})
