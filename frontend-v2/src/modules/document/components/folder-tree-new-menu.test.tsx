import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { FolderTreeNewMenu } from './folder-tree-new-menu'

function renderMenu(props: Partial<Parameters<typeof FolderTreeNewMenu>[0]> = {}) {
  const onCreateFolder = vi.fn()
  render(
    <MemoryRouter>
      <FolderTreeNewMenu
        folderId={null}
        canCreateFolder
        onCreateFolder={onCreateFolder}
        {...props}
      />
    </MemoryRouter>,
  )
  return { onCreateFolder }
}

describe('FolderTreeNewMenu', () => {
  //  Mở 24/09/2026: ở GỐC (chưa chọn thư mục) vẫn tạo được thư mục tự do.
  it('at root with create permission the button is enabled and only «Thư mục mới» is usable', async () => {
    const user = userEvent.setup()
    renderMenu()
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    expect(await screen.findByRole('menuitem', { name: 'Thư mục mới' })).not.toHaveAttribute(
      'data-disabled',
    )
    expect(screen.getByRole('menuitem', { name: 'Văn bản mới tại đây' })).toHaveAttribute(
      'data-disabled',
    )
    expect(screen.getByRole('menuitem', { name: 'Văn bản từ tệp có sẵn' })).toHaveAttribute(
      'data-disabled',
    )
  })

  it('at root WITHOUT create permission the whole button is disabled', () => {
    renderMenu({ canCreateFolder: false })
    expect(screen.getByRole('button', { name: 'Mới' })).toBeDisabled()
  })

  //  Lỗi báo 24/09/2026: chọn «Thư mục mới» không ra gì — menu modal giữ
  //  focus nên ô nhập mở lúc menu còn mở bị mất focus. Việc tạo phải chạy SAU
  //  khi menu đóng, và chạy đúng MỘT lần.
  it('runs onCreateFolder exactly once after the menu closes', async () => {
    const user = userEvent.setup()
    const { onCreateFolder } = renderMenu({ folderId: 5 })
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Thư mục mới' }))
    await vi.waitFor(() => expect(onCreateFolder).toHaveBeenCalledTimes(1))
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  it('closing the menu without choosing does not create anything', async () => {
    const user = userEvent.setup()
    const { onCreateFolder } = renderMenu({ folderId: 5 })
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    await screen.findByRole('menu')
    await user.keyboard('{Escape}')
    expect(onCreateFolder).not.toHaveBeenCalled()
  })
})
