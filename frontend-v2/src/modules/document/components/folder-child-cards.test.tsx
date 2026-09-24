import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FolderChildCards } from './folder-child-cards'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolderTree: vi.fn(() => ({ data: undefined })),
  useDeleteDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
}))

const FOLDER: DocFolderTreeNode = {
  id: 7,
  company_id: 1,
  parent_id: 2,
  kind: FOLDER_KIND.normal,
  kind_label: 'Thư mục',
  name: 'Phụ lục',
  code: '',
  path: '/1/2/7/',
  depth: 2,
  sort_order: 0,
  status: FOLDER_STATUS.active,
  status_label: 'Đang dùng',
  document_count: 0,
  document_count_branch: 0,
  my_level: FOLDER_ACCESS_LEVEL.manage,
}

function renderCards(onOpen = vi.fn(), onItemClick = vi.fn()) {
  render(
    <FolderChildCards
      children={[FOLDER]}
      sourceFolderId={2}
      isSelected={() => false}
      onItemClick={onItemClick}
      onOpen={onOpen}
      onViewDetails={vi.fn()}
      onDropItems={vi.fn()}
    />,
  )
  return { onOpen, onItemClick }
}

//  Chốt 24/09/2026: bấm MỘT LẦN là MỞ (bỏ bấm đúp) — chọn phải kèm phím.
describe('FolderChildCards — bấm một lần MỞ, Ctrl/Shift+bấm CHỌN', () => {
  it('opens on a plain single click and does not select', async () => {
    const user = userEvent.setup()
    const { onOpen, onItemClick } = renderCards()
    await user.click(screen.getByRole('button', { name: /Phụ lục/ }))
    expect(onOpen).toHaveBeenCalledTimes(1)
    expect(onOpen).toHaveBeenCalledWith(7)
    expect(onItemClick).not.toHaveBeenCalled()
  })

  it('ticking the card checkbox selects (toggle) without opening', async () => {
    const user = userEvent.setup()
    const { onOpen, onItemClick } = renderCards()
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Phụ lục' }))
    expect(onItemClick).toHaveBeenCalledWith(7, expect.objectContaining({ ctrlKey: true }))
    expect(onOpen).not.toHaveBeenCalled()
  })

  it('Ctrl+click selects instead of opening', async () => {
    const user = userEvent.setup()
    const { onOpen, onItemClick } = renderCards()
    await user.keyboard('{Control>}')
    await user.click(screen.getByRole('button', { name: /Phụ lục/ }))
    await user.keyboard('{/Control}')
    expect(onItemClick).toHaveBeenCalledWith(7, expect.objectContaining({ ctrlKey: true }))
    expect(onOpen).not.toHaveBeenCalled()
  })

  it('Shift+click selects a range instead of opening', async () => {
    const user = userEvent.setup()
    const { onOpen, onItemClick } = renderCards()
    await user.keyboard('{Shift>}')
    await user.click(screen.getByRole('button', { name: /Phụ lục/ }))
    await user.keyboard('{/Shift}')
    expect(onItemClick).toHaveBeenCalledWith(7, expect.objectContaining({ shiftKey: true }))
    expect(onOpen).not.toHaveBeenCalled()
  })

  it('Enter (bàn phím, đã focus thẻ) → cũng MỞ — lỗi thật đã báo 24/09/2026 tối: "bấm vào thư mục không nhảy", đúng đường Enter trên thẻ `<button>` (tự phát `click` nên trước đây chỉ CHỌN, không MỞ)', async () => {
    const user = userEvent.setup()
    const { onOpen } = renderCards()
    screen.getByRole('button', { name: /Phụ lục/ }).focus()
    await user.keyboard('{Enter}')
    //  Đúng MỘT lần — `<button>` tự phát `click` khi Enter, mà `click` nay
    //  cũng MỞ; thiếu `preventDefault` ở `onKeyDown` là mở hai lần.
    expect(onOpen).toHaveBeenCalledTimes(1)
    expect(onOpen).toHaveBeenCalledWith(7)
  })
})

//  Gốc «Thư mục của bạn» (`folder-my-drive-panel.tsx`, duoc-CR-476) REUSE
//  nguyên xi component này để vẽ thư mục PHÁP NHÂN — phải truyền đúng
//  `isCompanyRoot` cho `FolderItemContextMenu`, không thì menu ⋯ lộ ra
//  Đổi tên/Chuyển tới cho một loại thư mục backend luôn từ chối hai việc đó.
describe('FolderChildCards — thẻ PHÁP NHÂN (kind=company) có đủ Đổi tên/Chuyển tới', () => {
  const COMPANY_ROOT: DocFolderTreeNode = {
    id: 1,
    company_id: 1,
    parent_id: 0,
    kind: FOLDER_KIND.company,
    kind_label: 'Thư mục pháp nhân',
    name: 'CÔNG TY A',
    code: '',
    path: '/1/',
    depth: 0,
    sort_order: 0,
    status: FOLDER_STATUS.active,
    status_label: 'Đang dùng',
    document_count: 0,
    document_count_branch: 0,
    my_level: FOLDER_ACCESS_LEVEL.manage,
  }

  it('company folder menu offers Rename and Move like any folder', async () => {
    //  Luật cũ (ẩn với thư mục pháp nhân) BỎ 24/09/2026 — đại ca chốt thư mục pháp
    //  nhân chỉ là thư mục thường: đổi tên, chuyển đâu cũng được.
    const user = userEvent.setup()
    render(
      <FolderChildCards
        children={[COMPANY_ROOT]}
        sourceFolderId={null}
        isSelected={() => false}
        onItemClick={vi.fn()}
        onOpen={vi.fn()}
        onViewDetails={vi.fn()}
        onDropItems={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Thêm tùy chọn' }))
    expect(await screen.findByRole('menuitem', { name: 'Đổi tên' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chuyển tới…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chia sẻ…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Xem chi tiết' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toBeInTheDocument()
  })
})
