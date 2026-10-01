// Cột «Tìm thuốc khác» + «Tra cứu nhanh» của trang chi tiết thuốc BVTV (01/10/2026). Khẳng định
// ĐƯỜNG mở ra (tên tham số phải khớp mục «Thuốc BVTV»: pq · pgroup · psector · pstatus=all).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsPesticideLookupSidebar } from './customs-pesticide-lookup-sidebar'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: vi.fn(async () => ({
      total: 6919,
      last_loaded_at: null,
      statuses: [],
      pest_groups: [
        { value: 'Thuốc trừ sâu', count: 2794 },
        { value: 'Thuốc trừ bệnh', count: 2383 },
      ],
      sectors: [{ value: 'THUỐC TRỪ MỐI', count: 30 }],
      manual_count: 0,
      banned_rules: 0,
      banned_count: 0,
    })),
  }
})

function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output aria-label="location">{`${pathname}${search}`}</output>
}

function renderSidebar() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/procurement/customs-prices/pesticides/1']}>
        <Routes>
          <Route
            path="*"
            element={<CustomsPesticideLookupSidebar currentPestGroup="Thuốc trừ bệnh" />}
          />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function currentSearch() {
  const text = screen.getByRole('status', { name: 'location' }).textContent ?? ''
  const [pathname, search = ''] = text.split('?')
  return { pathname, params: new URLSearchParams(search) }
}

describe('CustomsPesticideLookupSidebar', () => {
  it('lists every pest group with its count and marks the current one', async () => {
    renderSidebar()
    const current = await screen.findByRole('link', { name: /Thuốc trừ bệnh/ })
    expect(current).toHaveAttribute('aria-current', 'true')
    expect(screen.getByRole('link', { name: /Thuốc trừ sâu/ })).not.toHaveAttribute('aria-current')
    expect(screen.getByText('2.794')).toBeInTheDocument()
  })

  it('quick links open the list filtered by that group on every status', async () => {
    renderSidebar()
    const link = await screen.findByRole('link', { name: /Thuốc trừ sâu/ })
    const url = new URL(link.getAttribute('href') ?? '', 'http://x')
    expect(url.pathname).toBe('/procurement/customs-prices/pesticides')
    expect(url.searchParams.get('pgroup')).toBe('Thuốc trừ sâu')
    expect(url.searchParams.get('pstatus')).toBe('all')
  })

  it('submits the keyword to the list with the list URL names (Enter works too)', async () => {
    renderSidebar()
    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm thuốc BVTV' }), ' abamectin {Enter}')
    const { pathname, params } = currentSearch()
    expect(pathname).toBe('/procurement/customs-prices/pesticides')
    expect(params.get('pq')).toBe('abamectin')
    expect(params.has('pgroup')).toBe(false)
  })

  it('keeps "Xóa bộ lọc" disabled until something is typed or chosen, then clears it', async () => {
    renderSidebar()
    const reset = screen.getByRole('button', { name: 'Xóa bộ lọc' })
    expect(reset).toBeDisabled()
    const box = screen.getByRole('textbox', { name: 'Tìm thuốc BVTV' })
    await userEvent.type(box, 'x')
    expect(reset).toBeEnabled()
    await userEvent.click(reset)
    expect(box).toHaveValue('')
    expect(reset).toBeDisabled()
  })
})
