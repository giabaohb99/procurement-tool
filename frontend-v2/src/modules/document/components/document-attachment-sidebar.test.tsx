import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DocumentVersionFile } from '../api/document-api'
import { DocumentAttachmentSidebar } from './document-attachment-sidebar'

const FILE = {
  id: 7,
  filename: 'Biên bản họp.pdf',
  content_type: 'application/pdf',
  version_id: 1,
  version_no: '1.0',
  is_current_version: true,
} as unknown as DocumentVersionFile

function renderSidebar(props: Partial<Parameters<typeof DocumentAttachmentSidebar>[0]> = {}) {
  const onSelect = vi.fn()
  render(
    <DocumentAttachmentSidebar
      files={[FILE]}
      selectedFileId={null}
      onSelect={onSelect}
      {...props}
    />,
  )
  return { onSelect }
}

//  Chốt 24/09/2026: bấm tệp thì KHUNG CHÍNH đổi sang xem tệp, không mở hộp thoại.
describe('DocumentAttachmentSidebar — cột tệp cạnh trình soạn thảo', () => {
  it('clicking a file hands THAT file to the page (which swaps the editor for the viewer)', async () => {
    const user = userEvent.setup()
    const { onSelect } = renderSidebar()
    await user.click(screen.getByRole('button', { name: /Biên bản họp\.pdf/ }))
    expect(onSelect).toHaveBeenCalledWith(FILE)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('«Bản soạn thảo» goes back to the editor (select null) and is marked current when no file is open', async () => {
    const user = userEvent.setup()
    const { onSelect } = renderSidebar({ selectedFileId: 7 })
    const back = screen.getByRole('button', { name: /Bản soạn thảo/ })
    expect(back).toHaveAttribute('aria-pressed', 'false')
    await user.click(back)
    expect(onSelect).toHaveBeenCalledWith(null)
  })

  //  Đại ca chốt: KHÔNG có ô tải tệp lên ở cột này — thêm/gỡ tệp ở tab Thông tin.
  it('has no upload box', () => {
    renderSidebar()
    expect(screen.queryByText(/tải tệp lên/i)).not.toBeInTheDocument()
  })

  it('the open file is the one marked pressed', () => {
    renderSidebar({ selectedFileId: 7 })
    expect(screen.getByRole('button', { name: /Biên bản họp\.pdf/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: /Bản soạn thảo/ })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })
})
