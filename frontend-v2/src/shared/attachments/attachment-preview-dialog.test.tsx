import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApiModule from '@/core/api'
import { AttachmentPreviewDialog, type PreviewableAttachment } from './attachment-preview-dialog'

/**
 * Lỗi phát hiện lúc kiểm tay bằng Chrome DevTools 03/10/2026 (hộp «Quá trình
 * công tác» nhân sự): hộp này SỐNG trong nhiều trang có `<form>` bọc cả trang
 * (hồ sơ nhân sự…) nhưng nút «Mở tab mới»/«Tải về» không khai `type="button"`
 * — mặc định HTML là `submit` (bẫy 3 của biểu mẫu). `AttachmentPreviewDialog`
 * là component DÙNG CHUNG (`shared/attachments`) nên sửa một chỗ, an toàn cho
 * MỌI nơi dùng nó, không riêng nhân sự.
 */

const fetchBlobUrlMock = vi.fn()
const downloadFileMock = vi.fn()
vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return {
    ...actual,
    fetchBlobUrl: (...args: unknown[]) => fetchBlobUrlMock(...args),
    downloadFile: (...args: unknown[]) => downloadFileMock(...args),
  }
})

function file(overrides: Partial<PreviewableAttachment> = {}): PreviewableAttachment {
  return { id: 1, filename: 'qd.pdf', content_type: 'application/pdf', url: '', ...overrides }
}

describe('AttachmentPreviewDialog — mọi nút phải type="button"', () => {
  it('«Mở tab mới» và «Tải về» đều có type="button", không để mặc định submit', async () => {
    fetchBlobUrlMock.mockResolvedValue('blob:fake')
    render(<AttachmentPreviewDialog file={file()} open onOpenChange={vi.fn()} />)

    const openTab = await screen.findByRole('button', { name: /Mở tab mới/ })
    const download = screen.getByRole('button', { name: /Tải về/ })

    expect((openTab as HTMLButtonElement).type).toBe('button')
    expect((download as HTMLButtonElement).type).toBe('button')
  })
})

describe('AttachmentPreviewDialog — bẫy form lồng: nằm trong <form> không được submit form cha', () => {
  it('bấm «Mở tab mới»/«Tải về» không gọi onSubmit của form bọc ngoài', async () => {
    fetchBlobUrlMock.mockResolvedValue('blob:fake')
    downloadFileMock.mockResolvedValue(undefined)
    const outerSubmit = vi.fn()
    const user = userEvent.setup()

    render(
      <form
        onSubmit={(event) => {
          event.preventDefault()
          outerSubmit()
        }}
      >
        <AttachmentPreviewDialog file={file()} open onOpenChange={vi.fn()} />
      </form>,
    )

    const openTab = await screen.findByRole('button', { name: /Mở tab mới/ })
    await user.click(openTab)
    await user.click(screen.getByRole('button', { name: /Tải về/ }))

    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('kiểu tệp không xem trước được (vd .docx) — vẫn không nút nào submit form cha', async () => {
    const outerSubmit = vi.fn()
    const user = userEvent.setup()

    render(
      <form
        onSubmit={(event) => {
          event.preventDefault()
          outerSubmit()
        }}
      >
        <AttachmentPreviewDialog
          file={file({ filename: 'ho-so.docx', content_type: 'application/msword' })}
          open
          onOpenChange={vi.fn()}
        />
      </form>,
    )

    await waitFor(() => screen.getByText(/không xem trước tại chỗ được/))
    await user.click(screen.getByRole('button', { name: /Mở tab mới/ }))

    expect(outerSubmit).not.toHaveBeenCalled()
  })
})
