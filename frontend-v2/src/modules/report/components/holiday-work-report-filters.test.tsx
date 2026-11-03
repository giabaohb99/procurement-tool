import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import type * as CoreApiModule from '@/core/api'

import { HolidayWorkReportFilters } from './holiday-work-report-filters'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn() }
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => entity === 'department' && action === 'read' }),
}))

function SearchProbe() {
  return <p data-testid="search">{useLocation().search}</p>
}

function renderAt(url = '/report/holiday-work') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <HolidayWorkReportFilters />
        <SearchProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockResolvedValue({ items: [{ id: 4, name: 'Kho vận' }], total: 1 })
})

/** duoc-CR-717: ô lọc của báo cáo khóa 30 phải ghi ĐÚNG tên tham số backend đọc. */
describe('HolidayWorkReportFilters', () => {
  it('starts on backend defaults without writing anything to the URL', () => {
    renderAt()
    expect(screen.getByRole('combobox', { name: 'Loại ngày' })).toHaveTextContent('Mọi loại ngày')
    expect(screen.getByRole('switch', { name: 'Gồm phiếu chờ duyệt' })).not.toBeChecked()
    expect(screen.getByRole('combobox', { name: 'Phòng ban' })).toBeInTheDocument()
    expect(screen.getByTestId('search')).toBeEmptyDOMElement()
  })

  it('writes day_kind=1 / 2 and drops it again on "Mọi loại ngày"', async () => {
    const user = userEvent.setup()
    renderAt()
    const trigger = screen.getByRole('combobox', { name: 'Loại ngày' })
    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Ngày lễ' }))
    expect(screen.getByTestId('search')).toHaveTextContent('?day_kind=1')

    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Ngày nghỉ theo lịch' }))
    expect(screen.getByTestId('search')).toHaveTextContent('?day_kind=2')

    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Mọi loại ngày' }))
    await waitFor(() => expect(screen.getByTestId('search')).toBeEmptyDOMElement())
  })

  it('toggles include_pending=1 on and removes it when switched off', async () => {
    const user = userEvent.setup()
    renderAt()
    const toggle = screen.getByRole('switch', { name: 'Gồm phiếu chờ duyệt' })
    await user.click(toggle)
    expect(screen.getByTestId('search')).toHaveTextContent('?include_pending=1')
    await user.click(toggle)
    await waitFor(() => expect(screen.getByTestId('search')).toBeEmptyDOMElement())
  })

  it.each(['9', 'abc', '-1', ''])(
    'shows the default for a hand-typed invalid day_kind=%s and removes it from the URL (review L2)',
    async (raw) => {
      //  Backend trả 422 cho day_kind ngoài 0-2, và URL được gửi nguyên lên backend — phải gỡ, không chỉ che.
      renderAt(`/report/holiday-work?day_kind=${raw}&include_pending=1`)
      expect(screen.getByRole('combobox', { name: 'Loại ngày' })).toHaveTextContent('Mọi loại ngày')
      await waitFor(() => expect(screen.getByTestId('search')).toHaveTextContent(/^\?include_pending=1$/))
    },
  )

  it.each(['yes', 'TRUE', 'on'])('shows the switch ON for include_pending=%s, as the backend counts it', (raw) => {
    //  Backend (`valid_flag`) coi 1/true/yes/on là bật — công tắc nói "tắt" là đọc sai số liệu.
    renderAt(`/report/holiday-work?include_pending=${raw}`)
    expect(screen.getByRole('switch', { name: 'Gồm phiếu chờ duyệt' })).toBeChecked()
  })

  it.each(['0', 'no', ''])('keeps the switch OFF for include_pending=%s', (raw) => {
    renderAt(`/report/holiday-work?include_pending=${raw}`)
    expect(screen.getByRole('switch', { name: 'Gồm phiếu chờ duyệt' })).not.toBeChecked()
  })
})
