// bao-CR-718 — màn chi tiết một lô xuất (đích của chuông "xuất xong"): bảng tệp với nút Tải từng tệp (tắt khi
// tệp đã bị dọn), nút Dừng chỉ khi lô còn chạy (có xác nhận), và tự hỏi lại mỗi 3 giây CHỈ khi lô còn active.
// Chặn ở tầng `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'

import type { CustomsExportBatch } from '../types/customs'
import { CustomsExportDetailPage } from './customs-export-detail-page'

const gets: string[] = []
const posts: string[] = []
let responses: CustomsExportBatch[] = []
let getError: unknown = null

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string) => {
      gets.push(url)
      if (getError) throw getError
      //  Lần hỏi thứ n trả bản thứ n; hết bản thì giữ bản cuối.
      return responses[Math.min(gets.length - 1, responses.length - 1)]
    },
    apiPost: async (url: string) => {
      posts.push(url)
      //  Từ giờ máy chủ trả bản đã dừng cho mọi lần hỏi lại.
      const stopped = { ...responses[responses.length - 1], status: 5, status_label: 'Đã dừng', active: false }
      responses = [stopped]
      return stopped
    },
  }
})

const downloadFile = vi.fn()
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (...args: unknown[]) => downloadFile(...args),
}))

vi.mock('sonner', () => ({ toast: { error: vi.fn(), success: vi.fn() } }))

function batch(patch: Partial<CustomsExportBatch> = {}): CustomsExportBatch {
  return {
    id: 12,
    status: 2,
    status_label: 'Đang xuất',
    filter_summary: 'Tên hàng: abamectin · Mã HS: 3808',
    filters: { q: 'abamectin', hs_code: '3808' },
    total_rows: 120_000,
    rows_per_file: 50_000,
    file_count: 3,
    files_done: 2,
    rows_done: 100_000,
    error: null,
    files: [
      { part: 1, filename: 'tra-cuu-thi-truong-lo-12-tep-01.xlsx', rows: 50_000, size: 12_800_000, available: false },
      { part: 2, filename: 'tra-cuu-thi-truong-lo-12-tep-02.xlsx', rows: 50_000, size: 12_800_000, available: true },
    ],
    created_at: '2026-11-03T09:00:00',
    created_by: 1,
    started_at: '2026-11-03T09:00:05',
    finished_at: null,
    expires_at: '2026-11-10T09:00:00',
    active: true,
    ...patch,
  }
}

function build(url = '/procurement/customs-prices/exports/12') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/procurement/customs-prices/exports/:id" element={<CustomsExportDetailPage />} />
        </Routes>
      </MemoryRouter>
      <ConfirmDialogHost />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  gets.length = 0
  posts.length = 0
  responses = [batch()]
  getError = null
  downloadFile.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('CustomsExportDetailPage', () => {
  it('lists the written files with progress, filter and expiry, and downloads one file by part', async () => {
    downloadFile.mockResolvedValue(undefined)
    build()
    expect(await screen.findByText('tra-cuu-thi-truong-lo-12-tep-02.xlsx')).toBeInTheDocument()
    expect(screen.getByText('Tên hàng: abamectin · Mã HS: 3808')).toBeInTheDocument()
    expect(screen.getByText('Đang xuất')).toBeInTheDocument()
    expect(screen.getByText(/Tệp xong:/)).toHaveTextContent('Tệp xong: 2/3 · Dòng đã ghi: 100.000/120.000')
    //  Mốc giờ backend là UTC trần → hiện giờ Việt Nam (+7).
    expect(screen.getByText('10/11/2026 16:00')).toBeInTheDocument()

    //  Tệp 1 đã bị dọn → nút tắt; tệp 2 còn → tải đúng đường của tệp đó.
    expect(screen.getByRole('button', { name: 'Tải tệp 1' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Tải tệp 2' }))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile.mock.calls[0][0]).toBe('/api/customs/export-batches/12/files/2')
    expect(downloadFile.mock.calls[0][1]).toBe('tra-cuu-thi-truong-lo-12-tep-02.xlsx')
  })

  it('stops a running batch only after confirmation, then hides Dừng', async () => {
    build()
    await userEvent.click(await screen.findByRole('button', { name: /Dừng/ }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('Tệp đã xong vẫn tải được')
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(posts).toHaveLength(0)

    await userEvent.click(screen.getByRole('button', { name: /Dừng/ }))
    await userEvent.click(await screen.findByRole('button', { name: 'Dừng lô' }))
    await waitFor(() => expect(posts).toEqual(['/api/customs/export-batches/12/cancel']))
    await waitFor(() => expect(screen.queryByRole('button', { name: /^Dừng$/ })).not.toBeInTheDocument())
    expect(await screen.findByText('Đã dừng')).toBeInTheDocument()
  })

  it('has no Dừng button on a finished batch and shows the backend error', async () => {
    responses = [batch({ status: 4, status_label: 'Lỗi', active: false, error: 'Worker chết giữa chừng' })]
    build()
    expect(await screen.findByText('Lỗi: Worker chết giữa chừng')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Dừng/ })).not.toBeInTheDocument()
  })

  it('polls every 3 seconds while active and stops polling once the batch is done', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    responses = [
      batch(),
      batch({
        status: 3,
        status_label: 'Xong',
        active: false,
        files_done: 3,
        rows_done: 120_000,
        finished_at: '2026-11-03T09:01:10',
      }),
    ]
    build()
    expect(await screen.findByText('Đang xuất')).toBeInTheDocument()
    expect(gets).toHaveLength(1)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3_100)
    })
    await waitFor(() => expect(screen.getByText('Xong')).toBeInTheDocument())
    expect(gets).toHaveLength(2)

    //  Lô xong → thôi hỏi, kể cả đợi thêm ba nhịp.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000)
    })
    expect(gets).toHaveLength(2)
  })

  it('never polls a batch that is already finished', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    responses = [batch({ status: 3, status_label: 'Xong', active: false })]
    build()
    expect(await screen.findByText('Xong')).toBeInTheDocument()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000)
    })
    expect(gets).toHaveLength(1)
  })

  it('explains a 403 (someone else batch) with the backend sentence instead of a blank page', async () => {
    getError = Object.assign(new Error('Request failed'), {
      response: { status: 403, data: { success: false, error: { message: 'Chỉ người đã xuất được xem lô này' } } },
    })
    build()
    expect(await screen.findByText('Chỉ người đã xuất được xem lô này')).toBeInTheDocument()
  })

  it('does not call the API for a garbage id', async () => {
    build('/procurement/customs-prices/exports/abc')
    expect(await screen.findByText(/Không tìm thấy lô xuất/)).toBeInTheDocument()
    expect(gets).toHaveLength(0)
  })
})
