// bao-CR-718 — "Lô xuất của tôi": bảng lô của chính mình, bấm dòng mở chi tiết lô, rỗng thì chỉ cách tạo lô.
// Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsExportListPage } from './customs-export-list-page'

const calls: { url: string; params?: Record<string, unknown> }[] = []
let items: unknown[] = []

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      return { total: items.length, items }
    },
  }
})

function LocationProbe() {
  const { pathname } = useLocation()
  return <output aria-label="location">{pathname}</output>
}

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/procurement/customs-prices/exports']}>
        <Routes>
          <Route path="/procurement/customs-prices/exports" element={<CustomsExportListPage />} />
          <Route path="*" element={null} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  calls.length = 0
  items = []
})

describe('CustomsExportListPage', () => {
  it('lists my batches with filter, status, file progress and opens the batch on row click', async () => {
    items = [
      {
        id: 12,
        status: 2,
        status_label: 'Đang xuất',
        filter_summary: 'Tên hàng: abamectin',
        filters: {},
        total_rows: 328_374,
        rows_per_file: 50_000,
        file_count: 7,
        files_done: 3,
        rows_done: 150_000,
        error: null,
        files: [],
        created_at: '2026-11-03T02:00:00',
        created_by: 1,
        started_at: null,
        finished_at: null,
        expires_at: null,
        active: true,
      },
    ]
    build()
    expect(await screen.findByText('Tên hàng: abamectin')).toBeInTheDocument()
    expect(calls[0]).toEqual({ url: '/api/customs/export-batches', params: { page: 1, page_size: 20 } })
    expect(screen.getByText('Đang xuất')).toBeInTheDocument()
    expect(screen.getByText('3/7')).toBeInTheDocument()
    expect(screen.getByText('328.374')).toBeInTheDocument()
    expect(screen.getByText('Giữ mãi')).toBeInTheDocument()
    await userEvent.click(screen.getByText('#12'))
    await waitFor(() =>
      expect(screen.getByRole('status', { name: 'location' })).toHaveTextContent(
        '/procurement/customs-prices/exports/12',
      ),
    )
  })

  it('tells the user how to create a batch when there is none', async () => {
    build()
    expect(await screen.findByText(/Chưa có lô xuất nào/)).toBeInTheDocument()
  })
})
