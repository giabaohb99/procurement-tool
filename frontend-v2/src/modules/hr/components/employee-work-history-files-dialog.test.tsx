import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApiModule from '@/core/api'
import type * as WorkHistoryApiModule from '../api/employee-work-history-api'
import type { WorkHistoryFile } from '../types/employee-work-history'
import { EmployeeWorkHistoryFilesDialog } from './employee-work-history-files-dialog'

const fetchFilesMock = vi.fn()
const uploadFilesMock = vi.fn()
const deleteFileMock = vi.fn()
vi.mock('../api/employee-work-history-api', async (importOriginal) => {
  const actual = await importOriginal<typeof WorkHistoryApiModule>()
  return {
    ...actual,
    fetchWorkHistoryFiles: (...args: unknown[]) => fetchFilesMock(...args),
    uploadWorkHistoryFiles: (...args: unknown[]) => uploadFilesMock(...args),
    deleteWorkHistoryFile: (...args: unknown[]) => deleteFileMock(...args),
  }
})

const fetchBlobUrlMock = vi.fn()
vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, fetchBlobUrl: (...args: unknown[]) => fetchBlobUrlMock(...args), downloadFile: vi.fn() }
})

function file(overrides: Partial<WorkHistoryFile> = {}): WorkHistoryFile {
  return {
    id: 1,
    file_id: 1,
    filename: 'qd.pdf',
    url: '',
    content_type: 'application/pdf',
    size: 1024,
    ...overrides,
  }
}

function renderDialog(
  options: { editable?: boolean; outerSubmit?: () => void } = {},
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const node = (
    <QueryClientProvider client={queryClient}>
      <EmployeeWorkHistoryFilesDialog
        open
        onOpenChange={vi.fn()}
        historyId={7}
        employeeId={42}
        editable={options.editable ?? true}
      />
    </QueryClientProvider>
  )
  if (options.outerSubmit) {
    return render(
      <form
        onSubmit={(event) => {
          event.preventDefault()
          options.outerSubmit?.()
        }}
      >
        {node}
      </form>,
    )
  }
  return render(node)
}

describe('EmployeeWorkHistoryFilesDialog', () => {
  it('editable=false → không vùng thả tệp, không nút «Gỡ tệp»; vẫn xem/tải được', async () => {
    fetchFilesMock.mockResolvedValue([file()])
    renderDialog({ editable: false })

    expect(screen.queryByText(/Kéo tệp vào đây/)).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Xem trước qd\.pdf/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Tải về qd\.pdf/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gỡ tệp' })).not.toBeInTheDocument()
  })

  it('editable=true + rỗng → câu mời kéo tệp, có vùng thả', async () => {
    fetchFilesMock.mockResolvedValue([])
    renderDialog({ editable: true })

    expect(await screen.findByText('Chưa có tệp nào. Kéo tệp vào vùng trên để tải lên.')).toBeInTheDocument()
    expect(screen.getByText(/Kéo tệp vào đây/)).toBeInTheDocument()
  })
})

/**
 * BẪY 1 (form lồng) — hộp này sống NGANG HÀNG với `<form>` đã chặn lan của hộp
 * Sửa (`employee-work-history-form-dialog.tsx`), và chính nó lại mở tiếp
 * `AttachmentPreviewDialog` lồng bên trong. Phát hiện lúc kiểm tay bằng Chrome
 * DevTools 03/10/2026: mở Sửa → Quản lý tệp → Xem trước → đóng từng hộp —
 * nghi có lần bắn `PATCH /api/employees/:id` (submit cả form hồ sơ).
 */
describe('EmployeeWorkHistoryFilesDialog — bẫy form lồng: không submit form cha', () => {
  it('mở Xem trước rồi bấm Mở tab mới/Tải về trong hộp xem trước → form cha KHÔNG submit', async () => {
    fetchFilesMock.mockResolvedValue([file()])
    fetchBlobUrlMock.mockResolvedValue('blob:fake')
    const outerSubmit = vi.fn()
    const user = userEvent.setup()
    renderDialog({ outerSubmit })

    await user.click(await screen.findByRole('button', { name: /Xem trước qd\.pdf/ }))
    const openTab = await screen.findByRole('button', { name: /Mở tab mới/ })
    await user.click(openTab)
    await user.click(screen.getByRole('button', { name: /Tải về$/ }))

    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('đóng hộp xem trước rồi đóng hộp tệp (nút Close) → form cha KHÔNG submit', async () => {
    fetchFilesMock.mockResolvedValue([file()])
    fetchBlobUrlMock.mockResolvedValue('blob:fake')
    const outerSubmit = vi.fn()
    const user = userEvent.setup()
    renderDialog({ outerSubmit })

    await user.click(await screen.findByRole('button', { name: /Xem trước qd\.pdf/ }))
    await waitFor(() => screen.getByRole('button', { name: /Mở tab mới/ }))

    //  Đóng mọi hộp còn mở theo thứ tự trong-ra-ngoài qua nút Close (X) của Radix.
    for (const label of ['close', 'close']) {
      const closeButtons = screen.queryAllByRole('button', { name: new RegExp(label, 'i') })
      if (closeButtons.length === 0) break
      await user.click(closeButtons[closeButtons.length - 1])
    }

    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('tải tệp mới lên (change input ẩn) rồi mở Xem trước → vẫn không submit form cha', async () => {
    fetchFilesMock.mockResolvedValue([file()])
    uploadFilesMock.mockResolvedValue([file({ id: 2, filename: 'moi.pdf' })])
    fetchBlobUrlMock.mockResolvedValue('blob:fake')
    const outerSubmit = vi.fn()
    renderDialog({ outerSubmit })

    await screen.findByRole('button', { name: /Xem trước qd\.pdf/ })
    const fileInput = document.querySelector('input[type="file"]')
    if (!fileInput) throw new Error('Không thấy input chọn tệp')
    const { fireEvent } = await import('@testing-library/react')
    fireEvent.change(fileInput, {
      target: { files: [new File(['noi dung'], 'moi.pdf', { type: 'application/pdf' })] },
    })

    await waitFor(() => expect(uploadFilesMock).toHaveBeenCalledTimes(1))
    expect(outerSubmit).not.toHaveBeenCalled()
  })
})
