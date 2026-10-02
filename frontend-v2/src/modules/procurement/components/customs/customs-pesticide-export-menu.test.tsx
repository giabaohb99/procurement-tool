// Nút «Xuất Excel» (2 lựa chọn) của mục «Thuốc BVTV». Chặn ở `@/core/api/download-file` —
// đúng chỗ tải tệp thật nằm (luật testing.md: mock ở tầng `@/core/api`; đường blob không đi qua
// `apiGet`/`apiPost` của barrel nên phải chặn đúng submodule, như `purchase-progress-page.test.tsx`).
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CustomsPesticideExportMenu } from './customs-pesticide-export-menu'

const downloadFile = vi.fn()
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (...args: unknown[]) => downloadFile(...args),
}))

const toastError = vi.fn()
vi.mock('sonner', () => ({ toast: { error: (m: string) => toastError(m), success: vi.fn() } }))

function openMenu() {
  return userEvent.click(screen.getByRole('button', { name: /Xuất Excel/ }))
}

beforeEach(() => {
  downloadFile.mockReset()
  toastError.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CustomsPesticideExportMenu', () => {
  it('sends scope=page plus the exact filter and paging params in use on screen', async () => {
    downloadFile.mockResolvedValue(undefined)
    render(
      <CustomsPesticideExportMenu
        filterParams={{ status: '1', pest_group: 'Thuốc trừ sâu' }}
        page={3}
        pageSize={50}
        pageRowCount={12}
      />,
    )

    await openMenu()
    await userEvent.click(await screen.findByText(/Trang hiện tại \(12 dòng\)/))

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const [url, filename, params] = downloadFile.mock.calls[0] as [
      string,
      string,
      Record<string, string>,
    ]
    expect(url).toBe('/api/customs/pesticides/export')
    //  Tên dự phòng khi backend không trả `Content-Disposition` — khác nhau theo scope để không
    //  đè tên tệp lẫn nhau (xem `exportCustomsPesticides`); tên THẬT luôn lấy từ header, kiểm ở
    //  `download-file.test.ts`.
    expect(filename).toBe('thuoc-bvtv-trang-3.xlsx')
    expect(params).toEqual({
      scope: 'page',
      status: '1',
      pest_group: 'Thuốc trừ sâu',
      page: '3',
      page_size: '50',
    })
  })

  it('sends scope=all with no filter at all, even when the screen is filtered', async () => {
    downloadFile.mockResolvedValue(undefined)
    render(
      <CustomsPesticideExportMenu
        filterParams={{ status: '1', q: 'atrazine' }}
        page={2}
        pageSize={50}
        pageRowCount={5}
      />,
    )

    await openMenu()
    await userEvent.click(await screen.findByText('Toàn bộ danh mục'))

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile.mock.calls[0][1]).toBe('thuoc-bvtv-toan-bo.xlsx')
    const params = downloadFile.mock.calls[0][2] as Record<string, string>
    expect(params).toEqual({ scope: 'all' })
  })

  it('locks the trigger while a download runs and ignores a second click in the meantime', async () => {
    let resolveDownload: () => void = () => {}
    downloadFile.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveDownload = resolve
        }),
    )
    render(
      <CustomsPesticideExportMenu filterParams={{}} page={1} pageSize={50} pageRowCount={0} />,
    )

    await openMenu()
    await userEvent.click(await screen.findByText('Toàn bộ danh mục'))

    const trigger = await screen.findByRole('button', { name: /Đang xuất…/ })
    expect(trigger).toBeDisabled()

    resolveDownload()
    await waitFor(() => expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeEnabled())
    expect(downloadFile).toHaveBeenCalledTimes(1)
  })

  it('reads the backend Vietnamese message out of the blob error instead of a generic failure', async () => {
    const blob = new Blob(
      [JSON.stringify({ success: false, error: { message: 'Đang có lượt xuất khác, thử lại sau.' } })],
      { type: 'application/json' },
    )
    downloadFile.mockRejectedValue({ response: { data: blob } })
    render(
      <CustomsPesticideExportMenu filterParams={{}} page={1} pageSize={50} pageRowCount={0} />,
    )

    await openMenu()
    await userEvent.click(await screen.findByText('Toàn bộ danh mục'))

    await waitFor(() =>
      expect(toastError).toHaveBeenCalledWith('Đang có lượt xuất khác, thử lại sau.'),
    )
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeEnabled()
  })

  it('disables the trigger when the catalog has nothing to export', () => {
    render(
      <CustomsPesticideExportMenu
        filterParams={{}}
        page={1}
        pageSize={50}
        pageRowCount={0}
        disabled
      />,
    )
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeDisabled()
  })
})
