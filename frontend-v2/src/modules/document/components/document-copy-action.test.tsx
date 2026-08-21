import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCopyDocument } from '../hooks/use-documents'
import { DocumentCopyAction } from './document-copy-action'

const navigate = vi.fn()
const mutate = vi.fn()

vi.mock('react-router-dom', () => ({ useNavigate: () => navigate }))
vi.mock('../hooks/use-documents', () => ({ useCopyDocument: vi.fn() }))

beforeEach(() => {
  navigate.mockReset()
  mutate.mockReset()
  vi.mocked(useCopyDocument).mockReturnValue({
    mutate,
    isPending: false,
  } as unknown as ReturnType<typeof useCopyDocument>)
})

describe('sao chép văn bản thành bản ghi thử', () => {
  it('ẩn khi người dùng không có quyền tạo văn bản', () => {
    render(<DocumentCopyAction documentId={216} canCreate={false} />)
    expect(screen.queryByRole('button', { name: 'Sao chép' })).not.toBeInTheDocument()
  })

  it('gọi sao chép đúng bản ghi và mở bản nháp mới khi thành công', async () => {
    const user = userEvent.setup()
    render(<DocumentCopyAction documentId={216} canCreate />)

    await user.click(screen.getByRole('button', { name: 'Sao chép' }))

    expect(mutate).toHaveBeenCalledWith(
      216,
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    )
    const options = mutate.mock.calls[0][1]
    options.onSuccess({ id: 999 })
    expect(navigate).toHaveBeenCalledWith('/document/documents/999')
  })

  it('không làm click lan lên dòng bảng', async () => {
    const user = userEvent.setup()
    const openDetail = vi.fn()
    render(
      <div onClick={openDetail}>
        <DocumentCopyAction documentId={216} canCreate placement="row" />
      </div>,
    )

    const button = screen.getByRole('button', { name: 'Sao chép' })
    expect(button).not.toHaveTextContent('Sao chép')
    await user.click(button)
    expect(openDetail).not.toHaveBeenCalled()
  })
})
