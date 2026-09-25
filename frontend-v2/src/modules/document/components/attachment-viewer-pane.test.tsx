import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AttachmentViewerPane } from './attachment-viewer-pane'

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(async () => ({ html: '<p>Nội dung</p>' })),
  fetchBlobUrl: vi.fn(async () => 'blob:tep-thu'),
  extractErrorMessage: (error: unknown) => String(error),
}))
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { full_name: 'Người Xem', email: 'x@y' } }),
}))

const CAPTION = /tên bạn được in chìm/

describe('AttachmentViewerPane — in chìm (watermark)', () => {
  beforeEach(() => {
    URL.revokeObjectURL = vi.fn()
  })

  it('stamps the viewer name over the file by default (dialog viewer keeps its deterrent)', async () => {
    render(
      <AttachmentViewerPane
        linkId={1}
        filename="a.pdf"
        contentType="application/pdf"
        documentCode="01/TB"
      />,
    )
    await waitFor(() => expect(screen.getByTitle('a.pdf')).toBeInTheDocument())
    expect(screen.getAllByText(/Người Xem .* 01\/TB/).length).toBeGreaterThan(0)
    expect(screen.getByText(CAPTION)).toBeInTheDocument()
  })

  //  Chốt 24/09/2026: tab «Văn bản» của văn bản chỉ gồm tệp là chỗ đọc hằng
  //  ngày — lớp chữ phủ kín trang gây khó đọc, bỏ ở đó.
  it('watermark={false} renders the file with no stamp and no caption', async () => {
    render(
      <AttachmentViewerPane
        linkId={1}
        filename="a.pdf"
        contentType="application/pdf"
        documentCode="01/TB"
        watermark={false}
      />,
    )
    await waitFor(() => expect(screen.getByTitle('a.pdf')).toBeInTheDocument())
    expect(screen.queryByText(/Người Xem .* 01\/TB/)).not.toBeInTheDocument()
    expect(screen.queryByText(CAPTION)).not.toBeInTheDocument()
  })

  it('watermark={false} also applies to Word files rendered as HTML', async () => {
    render(<AttachmentViewerPane linkId={2} filename="b.docx" watermark={false} />)
    await waitFor(() => expect(screen.getByTitle('b.docx')).toBeInTheDocument())
    expect(screen.queryByText(/Người Xem/)).not.toBeInTheDocument()
  })
})
