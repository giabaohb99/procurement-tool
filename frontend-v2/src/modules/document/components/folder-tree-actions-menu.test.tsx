import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FolderTreeActionsMenu } from './folder-tree-actions-menu'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

function folderNode(overrides: Partial<DocFolderTreeNode> = {}): DocFolderTreeNode {
  return {
    id: 1,
    company_id: 1,
    parent_id: 0,
    kind: FOLDER_KIND.normal,
    kind_label: 'Thư mục',
    name: 'Hợp đồng',
    code: '',
    path: '/1/',
    depth: 1,
    sort_order: 0,
    status: FOLDER_STATUS.active,
    status_label: 'Đang dùng',
    document_count: 0,
    document_count_branch: 0,
    my_level: FOLDER_ACCESS_LEVEL.manage,
    ...overrides,
  }
}

async function openMenu(data: DocFolderTreeNode, onAction = vi.fn()) {
  const user = userEvent.setup()
  render(<FolderTreeActionsMenu data={data} onAction={onAction} />)
  await user.click(screen.getByRole('button', { name: `Thao tác với ${data.name}` }))
  return { user, onAction }
}

//  Đại ca chốt 24/09/2026 (ĐẢO quyết định cho xóa gốc pháp nhân trước đó cùng
//  ngày): thư mục pháp nhân + nhóm «Công ty» KHÔNG xóa được. Mục «Xóa» vẫn HIỆN
//  nhưng KHÓA kèm lý do — giấu hẳn thì người dùng tưởng tính năng biến mất.
describe('FolderTreeActionsMenu — thư mục PHÁP NHÂN không xóa được, còn lại như thư mục thường', () => {
  it('Manage level: «Xóa» is DISABLED with a reason; rename/move/archive still offered', async () => {
    const root = folderNode({
      kind: FOLDER_KIND.company,
      name: 'CÔNG TY ABC',
      my_level: FOLDER_ACCESS_LEVEL.manage,
    })
    await openMenu(root)

    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toHaveAttribute('data-disabled')
    expect(
      screen.getByText('Thư mục công ty do hệ thống quản lý, không xóa được'),
    ).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Ngừng dùng' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Đổi tên tại chỗ' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chuyển tới…' })).toBeInTheDocument()
  })

  it('thư mục pháp nhân ĐANG NGỪNG DÙNG, mức Quản lý → có «Khôi phục» thay vì «Ngừng dùng»', async () => {
    const root = folderNode({
      kind: FOLDER_KIND.company,
      name: 'CÔNG TY ABC',
      my_level: FOLDER_ACCESS_LEVEL.manage,
      status: FOLDER_STATUS.archived,
    })
    await openMenu(root)
    expect(screen.getByRole('menuitem', { name: 'Khôi phục' })).toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Ngừng dùng' })).not.toBeInTheDocument()
  })

  it('clicking the disabled «Xóa» of a company folder does NOT fire delete', async () => {
    const root = folderNode({ kind: FOLDER_KIND.company, my_level: FOLDER_ACCESS_LEVEL.manage })
    const { user, onAction } = await openMenu(root)
    await user.click(screen.getByRole('menuitem', { name: /^Xóa/ }))
    expect(onAction).not.toHaveBeenCalledWith('delete')
  })

  it('company GROUP «Công ty»: delete locked and no «Chuyển tới…» (it always stays at the root)', async () => {
    const group = folderNode({
      kind: FOLDER_KIND.companyGroup,
      name: 'Công ty',
      my_level: FOLDER_ACCESS_LEVEL.manage,
    })
    await openMenu(group)
    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toHaveAttribute('data-disabled')
    expect(screen.queryByRole('menuitem', { name: 'Chuyển tới…' })).not.toBeInTheDocument()
  })
})

describe('FolderTreeActionsMenu — thư mục THƯỜNG, mức Quản lý → đủ cả bộ', () => {
  it('có Đổi tên, Chuyển tới, Chia sẻ, Ngừng dùng, Xóa (bật)', async () => {
    await openMenu(folderNode({ my_level: FOLDER_ACCESS_LEVEL.manage }))
    expect(screen.getByRole('menuitem', { name: 'Đổi tên tại chỗ' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chuyển tới…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chia sẻ…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Ngừng dùng' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Xóa' })).toBeEnabled()
  })

  it('mức Đóng góp (chưa đủ Quản lý) → «Xóa» khóa, không Đổi tên/Chuyển tới/Ngừng dùng', async () => {
    await openMenu(folderNode({ my_level: FOLDER_ACCESS_LEVEL.contribute }))
    expect(screen.queryByRole('menuitem', { name: 'Đổi tên tại chỗ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Ngừng dùng' })).not.toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toHaveAttribute('data-disabled')
  })
})

describe('FolderTreeActionsMenu — dưới mức Đóng góp thì KHÔNG có nút «⋯» nào cả', () => {
  it('mức Xem → không dựng nút', () => {
    render(
      <FolderTreeActionsMenu
        data={folderNode({ my_level: FOLDER_ACCESS_LEVEL.view })}
        onAction={vi.fn()}
      />,
    )
    expect(screen.queryByRole('button', { name: /Thao tác với/ })).not.toBeInTheDocument()
  })
})

//  26/09/2026: menu dựng LƯỜI — lần bấm đầu là nút trơn, từ lần hai là nút của
//  Radix. Nuốt mất prop Radix gắn vào nút (ref, onPointerDown…) thì lần hai
//  bấm không mở được, mà bài kiểm chỉ bấm một lần sẽ không bao giờ thấy.
describe('FolderTreeActionsMenu — lazy mounting', () => {
  it('renders no menu until the first click, then opens it on that same click', async () => {
    const user = userEvent.setup()
    render(<FolderTreeActionsMenu data={folderNode()} onAction={vi.fn()} />)
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Thao tác với Hợp đồng' }))
    expect(screen.getByRole('menu')).toBeInTheDocument()
  })

  it('reopens after being closed — the second click goes through the Radix trigger', async () => {
    const { user } = await openMenu(folderNode())
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Thao tác với Hợp đồng' }))
    expect(screen.getByRole('menu')).toBeInTheDocument()
  })

  it('clicking the button does not bubble to the tree row (would select the folder)', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()
    render(
      <div onClick={onRowClick}>
        <FolderTreeActionsMenu data={folderNode()} onAction={vi.fn()} />
      </div>,
    )
    await user.click(screen.getByRole('button', { name: 'Thao tác với Hợp đồng' }))
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: 'Thao tác với Hợp đồng' }))
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('runs the chosen action from a menu opened lazily', async () => {
    const { user, onAction } = await openMenu(folderNode())
    await user.click(screen.getByRole('menuitem', { name: 'Chia sẻ…' }))
    expect(onAction).toHaveBeenCalledWith('access')
  })
})
