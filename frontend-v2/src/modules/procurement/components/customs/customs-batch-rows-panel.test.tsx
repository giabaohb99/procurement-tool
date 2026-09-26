// bao-CR-496 — hộp nhật ký từng dòng: tổng theo kết cục ở đầu, bấm ô là lọc và về trang 1.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CustomsBatchRowsPanel } from './customs-batch-rows-panel'

const api = { rows: vi.fn(), summary: vi.fn() }
vi.mock('../../api/customs-saved-filter-api', () => ({
  fetchCustomsSavedFilters: vi.fn(),
  createCustomsSavedFilter: vi.fn(),
  updateCustomsSavedFilter: vi.fn(),
  deleteCustomsSavedFilter: vi.fn(),
  fetchCustomsBatchRows: (id: number, p: unknown) => api.rows(id, p),
  fetchCustomsBatchRowSummary: (id: number) => api.summary(id),
}))

function mount() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <CustomsBatchRowsPanel batchId={5} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  api.summary.mockResolvedValue({ total: 4, new: 2, error: 1, duplicate: 1, labels: {} })
  api.rows.mockResolvedValue({
    total: 4,
    page: 1,
    page_size: 50,
    items: [
      { id: 1, row_no: 2, row_status: 1, row_status_label: 'Thêm mới', product_name: 'ATRAZINE 97% TECH', message: 'Thêm mới' },
      { id: 2, row_no: 3, row_status: 2, row_status_label: 'Lỗi', product_name: '', message: 'Không đọc được Ngày đăng ký — bỏ dòng' },
      { id: 3, row_no: 4, row_status: 3, row_status_label: 'Trùng trong lô', product_name: 'ATRAZINE 97% TECH', message: 'Giống hệt dòng 2 trong cùng tệp — vẫn ghi vào bảng giá, cần rà tay' },
    ],
  })
})

describe('CustomsBatchRowsPanel — bao-CR-496', () => {
  it('shows counts per outcome and every data row with its outcome badge', async () => {
    mount()
    expect(await screen.findByRole('button', { name: 'Tất cả: 4' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Thêm mới: 2' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lỗi: 1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Trùng trong lô: 1' })).toBeInTheDocument()
    expect(await screen.findByText(/giống hệt dòng 2/i)).toBeInTheDocument()
    expect(api.rows).toHaveBeenCalledWith(5, { page: 1, page_size: 50, row_status: undefined })
  })

  it('clicking an outcome chip refetches with that status', async () => {
    mount()
    await userEvent.click(await screen.findByRole('button', { name: 'Trùng trong lô: 1' }))
    await waitFor(() =>
      expect(api.rows).toHaveBeenLastCalledWith(5, { page: 1, page_size: 50, row_status: 3 }),
    )
    expect(screen.getByRole('button', { name: 'Trùng trong lô: 1' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('tells the user when a batch predates per-row logging', async () => {
    api.summary.mockResolvedValue({ total: 0, new: 0, error: 0, duplicate: 0, labels: {} })
    api.rows.mockResolvedValue({ total: 0, page: 1, page_size: 50, items: [] })
    mount()
    expect(await screen.findByText(/nạp trước khi có nhật ký từng dòng/i)).toBeInTheDocument()
  })
})
