import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'
import {
  ProcurementListCloneModeButton,
  ProcurementListCloneRowButton,
} from './procurement-list-clone-controls'

const post = vi.fn()
vi.mock('@/core/api/http-client', () => ({ httpClient: { post: (...args: unknown[]) => post(...args) } }))

function renderRowButton(code?: string) {
  return render(
    <MemoryRouter initialEntries={['/list']}>
      <Routes>
        <Route
          path="/list"
          element={
            <ProcurementListCloneRowButton
              apiPath="/api/purchase-requests"
              id={42}
              code={code}
              toDetail={(id) => `/detail/${id}`}
              successMessage="Đã nhân bản phiếu yêu cầu mua hàng"
              errorMessage="Nhân bản phiếu thất bại"
            />
          }
        />
        <Route path="/detail/:id" element={<p>Trang phiếu mới</p>} />
      </Routes>
      <ConfirmDialogHost />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  post.mockReset().mockResolvedValue({ data: { message: '', data: { id: 99 } } })
})

describe('ProcurementListCloneModeButton — nút bật chế độ nhân bản của bản v1', () => {
  it('reads Nhân bản when off and Xong when on, with the v1 tooltip', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    const { rerender } = render(<ProcurementListCloneModeButton active={false} onToggle={onToggle} />)

    const button = screen.getByRole('button', { name: 'Nhân bản' })
    expect(button).toHaveAttribute(
      'title',
      'Bật chế độ nhân bản: hiện cột Thao tác để nhân bản từng phiếu',
    )
    await user.click(button)
    expect(onToggle).toHaveBeenCalledTimes(1)

    rerender(<ProcurementListCloneModeButton active onToggle={onToggle} />)
    expect(screen.getByRole('button', { name: 'Xong' })).toHaveAttribute('aria-pressed', 'true')
  })
})

describe('ProcurementListCloneRowButton — hỏi Nhân bản phiếu trước khi tạo', () => {
  it('asks with the v1 box Nhân bản phiếu naming the code, and Hủy creates nothing', async () => {
    const user = userEvent.setup()
    renderRowButton('PYC-0007')

    await user.click(screen.getByRole('button', { name: 'Nhân bản PYC-0007' }))
    expect(await screen.findByRole('alertdialog', { name: 'Nhân bản phiếu' })).toBeInTheDocument()
    expect(screen.getByText(/Bạn chắc chắn muốn nhân bản phiếu "PYC-0007"\?/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(post).not.toHaveBeenCalled()
  })

  it('names the row button after its code but still shows the plain v1 word', () => {
    renderRowButton('PYC-0007')
    const button = screen.getByRole('button', { name: 'Nhân bản PYC-0007' })
    expect(button).toHaveTextContent(/^Nhân bản$/)
  })

  it('falls back to phiếu này when the row has no code', async () => {
    const user = userEvent.setup()
    renderRowButton()

    await user.click(screen.getByRole('button', { name: 'Nhân bản' }))
    expect(await screen.findByText(/Bạn chắc chắn muốn nhân bản phiếu này\?/)).toBeInTheDocument()
    //  Hộp xác nhận là kho TOÀN CỤC (zustand): bỏ ngỏ là bài sau mở ra đã thấy hộp cũ đè lên.
    await user.click(screen.getByRole('button', { name: 'Hủy' }))
  })

  it('Nhân bản in the box clones once and opens the new draft', async () => {
    const user = userEvent.setup()
    renderRowButton('PYC-0007')

    await user.click(screen.getByRole('button', { name: 'Nhân bản PYC-0007' }))
    //  Hai nút cùng chữ: nút trong dòng (nằm ngoài hộp) và nút đồng ý — lấy cái trong hộp.
    const dialog = await screen.findByRole('alertdialog', { name: 'Nhân bản phiếu' })
    await user.click(within(dialog).getByRole('button', { name: 'Nhân bản' }))

    expect(post).toHaveBeenCalledTimes(1)
    expect(post).toHaveBeenCalledWith('/api/purchase-requests/42/clone')
    expect(await screen.findByText('Trang phiếu mới')).toBeInTheDocument()
  })

  it('stays on the list when the clone call fails', async () => {
    const user = userEvent.setup()
    post.mockRejectedValueOnce(new Error('500'))
    renderRowButton('PYC-0007')

    await user.click(screen.getByRole('button', { name: 'Nhân bản PYC-0007' }))
    const dialog = await screen.findByRole('alertdialog', { name: 'Nhân bản phiếu' })
    await user.click(within(dialog).getByRole('button', { name: 'Nhân bản' }))

    expect(post).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('Trang phiếu mới')).toBeNull()
  })
})
