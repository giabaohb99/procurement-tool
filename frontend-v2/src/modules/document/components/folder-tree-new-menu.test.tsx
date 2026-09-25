import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { FolderTreeNewMenu } from './folder-tree-new-menu'

//  Hộp thật có test riêng (`folder-quick-document-dialog.test.tsx`) — ở đây chỉ
//  kiểm menu mở nó với ĐÚNG thư mục + pháp nhân.
vi.mock('./folder-quick-document-dialog', () => ({
  FolderQuickDocumentDialog: (props: { folderId: number; folderCompanyId: number }) => (
    <div role="dialog">
      quick {props.folderId}/{props.folderCompanyId}
    </div>
  ),
}))

function renderMenu(props: Partial<Parameters<typeof FolderTreeNewMenu>[0]> = {}) {
  const onCreateFolder = vi.fn()
  render(
    <MemoryRouter>
      <FolderTreeNewMenu
        folderId={null}
        canCreateFolder
        canCreateDocument
        onCreateFolder={onCreateFolder}
        {...props}
      />
    </MemoryRouter>,
  )
  return { onCreateFolder }
}

describe('FolderTreeNewMenu', () => {
  //  Mở 24/09/2026: ở GỐC (chưa chọn thư mục) vẫn tạo được thư mục tự do.
  //  Hai mục văn bản cần một thư mục đích nên ở gốc không hiện.
  it('at root offers only «Thư mục mới» — document items need a target folder', async () => {
    const user = userEvent.setup()
    renderMenu()
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    expect(await screen.findByRole('menuitem', { name: 'Thư mục mới' })).toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Văn bản mới tại đây' })).not.toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Tạo nhanh từ tệp' })).not.toBeInTheDocument()
  })

  //  Lỗi lead bắt khi test UI 24/09/2026: người CHỈ XEM vẫn thấy nút «+ Mới».
  it('is hidden entirely for a view-only user, inside a folder too', () => {
    renderMenu({ folderId: 5, canCreateFolder: false, canCreateDocument: false })
    expect(screen.queryByRole('button', { name: 'Mới' })).not.toBeInTheDocument()
  })

  it('at root without folder permission is hidden even if the user can create documents', () => {
    renderMenu({ canCreateFolder: false, canCreateDocument: true })
    expect(screen.queryByRole('button', { name: 'Mới' })).not.toBeInTheDocument()
  })

  it('shows only the document items when the role can create documents but not folders', async () => {
    const user = userEvent.setup()
    renderMenu({ folderId: 5, canCreateFolder: false, canCreateDocument: true })
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    expect(await screen.findByRole('menuitem', { name: 'Văn bản mới tại đây' })).toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Thư mục mới' })).not.toBeInTheDocument()
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

  it('«Tạo nhanh từ tệp» opens the quick dialog for the current folder and its company', async () => {
    const user = userEvent.setup()
    renderMenu({ folderId: 23, folderCompanyId: 2 })
    await user.click(screen.getByRole('button', { name: 'Mới' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Tạo nhanh từ tệp' }))
    expect(await screen.findByRole('dialog')).toHaveTextContent('quick 23/2')
  })
})
