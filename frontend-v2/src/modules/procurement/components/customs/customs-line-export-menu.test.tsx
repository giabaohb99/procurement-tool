// bao-CR-718 — menu "Xuất dữ liệu" của thẻ Danh sách: hộp xác nhận "Xuất toàn bộ" phải nêu đúng số dòng + số tệp,
// Đồng ý mới tạo lô (đúng bộ lọc trên query) rồi sang màn chi tiết lô; 409 chỉ đường sang "Lô xuất của tôi".
// Chặn ở tầng `@/core/api` (luật testing.md); hộp xác nhận dùng hàng thật (`ConfirmDialogHost`).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'

import { CustomsLineExportMenu } from './customs-line-export-menu'

const posts: { url: string; params?: Record<string, unknown> }[] = []
let postResult: () => Promise<unknown> = async () => ({})

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    httpClient: {
      ...actual.httpClient,
      post: async (url: string, _body: unknown, config?: { params?: Record<string, unknown> }) => {
        posts.push({ url, params: config?.params })
        return postResult()
      },
    },
  }
})

const downloadFile = vi.fn()
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (...args: unknown[]) => downloadFile(...args),
}))

const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('sonner', () => ({
  toast: {
    error: (...args: unknown[]) => toastError(...args),
    success: (...args: unknown[]) => toastSuccess(...args),
  },
}))

function LocationProbe() {
  const { pathname } = useLocation()
  return <output aria-label="location">{pathname}</output>
}

function build(
  totalRows: number | undefined,
  filterParams: Record<string, string> = { q: 'abamectin' },
  sortParams?: Record<string, string>,
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/procurement/customs-prices?q=abamectin']}>
        <Routes>
          <Route
            path="*"
            element={
              <CustomsLineExportMenu
                filterParams={filterParams}
                sortParams={sortParams}
                filterSummary="Tên hàng: abamectin"
                totalRows={totalRows}
              />
            }
          />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
      <ConfirmDialogHost />
    </QueryClientProvider>,
  )
}

function currentPath() {
  return screen.getByRole('status', { name: 'location' }).textContent
}

async function openMenu() {
  await userEvent.click(screen.getByRole('button', { name: /Xuất dữ liệu/ }))
}

function batchOf(id: number) {
  return {
    id,
    status: 1,
    status_label: 'Đang chờ',
    filter_summary: 'Tên hàng: abamectin',
    filters: { q: 'abamectin' },
    total_rows: 328_374,
    rows_per_file: 50_000,
    file_count: 7,
    files_done: 0,
    rows_done: 0,
    error: null,
    files: [],
    created_at: '2026-11-03T09:00:00',
    created_by: 1,
    started_at: null,
    finished_at: null,
    expires_at: null,
    active: true,
  }
}

beforeEach(() => {
  posts.length = 0
  downloadFile.mockReset()
  toastError.mockReset()
  toastSuccess.mockReset()
  postResult = async () => ({ data: { success: true, message: 'Đã tạo lô xuất #12', data: batchOf(12) } })
})

describe('CustomsLineExportMenu', () => {
  it('keeps Xuất ngay as the old direct download with the exact filter params', async () => {
    downloadFile.mockResolvedValue(undefined)
    build(120, { q: 'abamectin', hs_code: '3808' })
    await openMenu()
    await userEvent.click(await screen.findByText(/Xuất ngay \(tối đa 50\.000 dòng\)/))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const [url, , params] = downloadFile.mock.calls[0] as [string, string, Record<string, string>]
    expect(url).toBe('/api/customs/lines/export')
    expect(params).toEqual({ q: 'abamectin', hs_code: '3808' })
    expect(posts).toHaveLength(0)
  })

  //  duoc-CR-744 — "Xuất ngay" ra tệp theo ĐÚNG thứ tự bảng đang xem; "Xuất toàn bộ" chạy nền theo ID tăng dần
  //  (đọc khối keyset) nên KHÔNG mang thứ tự — gửi sang chỉ làm bộ lọc của lô dính hai khóa lạ.
  it('exports in the order the table shows, but never sends the order to the background batch', async () => {
    downloadFile.mockResolvedValue(undefined)
    build(120, { q: 'abamectin' }, { sort_by: 'price_usd', sort_dir: 'desc' })
    await openMenu()
    await userEvent.click(await screen.findByText(/Xuất ngay \(tối đa 50\.000 dòng\)/))
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const [, , params] = downloadFile.mock.calls[0] as [string, string, Record<string, string>]
    expect(params).toEqual({ q: 'abamectin', sort_by: 'price_usd', sort_dir: 'desc' })

    await openMenu()
    await userEvent.click(await screen.findByText('Xuất toàn bộ theo bộ lọc (chạy nền)'))
    await userEvent.click(await screen.findByRole('button', { name: 'Đồng ý' }))
    await waitFor(() => expect(posts).toHaveLength(1))
    expect(posts[0].params).toEqual({ q: 'abamectin' })
  })

  it('shows rows and the expected file count in the confirm box, and creates nothing on Hủy', async () => {
    build(328_374)
    await openMenu()
    await userEvent.click(await screen.findByText('Xuất toàn bộ theo bộ lọc (chạy nền)'))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('Bộ lọc: Tên hàng: abamectin')
    expect(dialog).toHaveTextContent('328.374')
    expect(dialog).toHaveTextContent('dự kiến 7 tệp')
    expect(dialog).toHaveTextContent('7 ngày')
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())
    expect(posts).toHaveLength(0)
  })

  it('on Đồng ý posts the filter as query params, toasts the backend message and opens the batch', async () => {
    build(328_374)
    await openMenu()
    await userEvent.click(await screen.findByText('Xuất toàn bộ theo bộ lọc (chạy nền)'))
    await userEvent.click(await screen.findByRole('button', { name: 'Đồng ý' }))
    await waitFor(() => expect(currentPath()).toBe('/procurement/customs-prices/exports/12'))
    expect(posts).toEqual([{ url: '/api/customs/export-batches', params: { q: 'abamectin' } }])
    expect(toastSuccess).toHaveBeenCalledWith('Đã tạo lô xuất #12')
  })

  it('on 409 shows the backend sentence with a shortcut to Lô xuất của tôi and stays put', async () => {
    postResult = async () => {
      throw Object.assign(new Error('Request failed'), {
        response: {
          status: 409,
          data: { success: false, error: { message: 'Bạn đang có một lô xuất chưa xong' } },
        },
      })
    }
    build(328_374)
    await openMenu()
    await userEvent.click(await screen.findByText('Xuất toàn bộ theo bộ lọc (chạy nền)'))
    await userEvent.click(await screen.findByRole('button', { name: 'Đồng ý' }))
    await waitFor(() => expect(toastError).toHaveBeenCalledTimes(1))
    const [message, options] = toastError.mock.calls[0] as [
      string,
      { action: { label: string; onClick: () => void } },
    ]
    expect(message).toBe('Bạn đang có một lô xuất chưa xong')
    expect(options.action.label).toBe('Lô xuất của tôi')
    expect(currentPath()).toBe('/procurement/customs-prices')
    options.action.onClick()
    await waitFor(() => expect(currentPath()).toBe('/procurement/customs-prices/exports'))
  })

  it('disables both export items on an empty result but still opens Lô xuất của tôi', async () => {
    build(0)
    await openMenu()
    expect(await screen.findByRole('menuitem', { name: /Xuất ngay/ })).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByRole('menuitem', { name: /Xuất toàn bộ/ })).toHaveAttribute('aria-disabled', 'true')
    await userEvent.click(screen.getByRole('menuitem', { name: /Lô xuất của tôi/ }))
    expect(currentPath()).toBe('/procurement/customs-prices/exports')
  })

  it('blocks Xuất ngay above the 50.000-row cap (the backend would reject it) but allows the background export', async () => {
    build(50_001)
    await openMenu()
    expect(await screen.findByRole('menuitem', { name: /Xuất ngay/ })).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByRole('menuitem', { name: /Xuất toàn bộ/ })).not.toHaveAttribute('aria-disabled')
    expect(screen.getByText(/dự kiến 2 tệp/)).toBeInTheDocument()
  })
})
