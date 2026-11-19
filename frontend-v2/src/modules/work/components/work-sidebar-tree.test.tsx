import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'

import { WorkSidebarTree } from './work-sidebar-tree'
import type { WorkGroupNode, WorkList, WorkSidebar } from '../types/work'

/**
 * Chốt `onNavigate` — móc để cây TỰ ĐÓNG tờ trượt ở khổ hẹp.
 *
 * Dưới 768px cây nằm trong tờ trượt phủ gần trọn màn hình
 * (`WorkSidebarPeekButton`). Bấm một dự án thì route đổi PHÍA SAU tấm phủ; không
 * có móc này thì người dùng chỉ thấy cây đứng im và tưởng cú chạm bị rơi. Lỗi
 * ấy chỉ lộ ở khổ hẹp nên không ai gặp lúc dựng màn trên máy tính — vì vậy nó
 * phải có bài kiểm canh.
 *
 * Ba điều bài này ghim:
 *
 *  1. Dự án ở tầng gốc (list lẻ, A-08) gọi `onNavigate`.
 *  2. Dự án nằm sâu trong NHÓM CON cũng gọi — `GroupNode` đệ quy, quên luồn
 *     prop xuống một nhánh là nửa cây im lặng mất tính năng.
 *  3. Mở/đóng một nhóm thì KHÔNG gọi: không chuyển trang thì không được đóng tờ
 *     trượt, nếu không người dùng bung nhóm ra một cái là cây biến mất.
 */

function makeList(id: number, name: string): WorkList {
  return {
    id,
    name,
    description: '',
    color: 'blue',
    group_id: null,
    sort_order: 0,
    is_archived: 0,
    my_role: null,
    task_count: 0,
    task_done: 0,
    created_at: '2026-09-10',
    owner: null,
    members: [],
  }
}

function makeGroup(id: number, name: string, extra: Partial<WorkGroupNode> = {}): WorkGroupNode {
  return {
    id,
    name,
    description: '',
    parent_id: null,
    sort_order: 0,
    is_archived: 0,
    my_role: null,
    lists: [],
    children: [],
    ...extra,
  }
}

const sidebar: WorkSidebar = {
  //  Nhóm lồng nhóm: dự án nằm ở tầng thứ hai, đúng nhánh đệ quy dễ quên.
  groups: [
    makeGroup(1, 'Khối Vận hành', {
      //  duoc-CR-783: mình quản trị nhóm con (đích chuyển được), còn nhóm cha thì không có vai trò gì.
      children: [makeGroup(2, 'Tổ Kho vận', { my_role: 2, lists: [makeList(24, 'Kiểm kê kho cuối quý')] })],
    }),
  ],
  //  duoc-CR-783: mình là CHỦ dự án lẻ này (có menu "…" để lưu trữ), còn dự án trong nhóm thì không.
  lists: [{ ...makeList(26, 'Tuyển dụng & Đào tạo Q3'), my_role: 1 }],
}

const archiveList = vi.hoisted(() => vi.fn())
const purgeList = vi.hoisted(() => vi.fn())
const updateList = vi.hoisted(() => vi.fn())
vi.mock('../hooks/use-work-lists', () => ({
  useWorkSidebar: () => ({ data: sidebar, isLoading: false }),
  useArchiveWorkList: () => ({ mutate: archiveList, isPending: false }),
  usePurgeWorkList: () => ({ mutate: purgeList, isPending: false }),
  useUpdateWorkList: () => ({ mutate: updateList, isPending: false }),
}))

//  Ghim lưu ở máy chủ (tùy chọn người dùng) — bài này chỉ soi cách cây vẽ và gọi, nên thay bằng bản giả có state.
const pinState = vi.hoisted(() => ({ pinned: [] as number[], toggle: vi.fn() }))
vi.mock('../hooks/use-pinned-lists', () => ({
  usePinnedLists: () => ({
    pinned: pinState.pinned,
    isPinned: (id: number) => pinState.pinned.includes(id),
    toggle: pinState.toggle,
  }),
}))

beforeEach(() => {
  pinState.pinned = []
  pinState.toggle.mockClear()
})

function renderTree(onNavigate?: () => void) {
  return render(
    <MemoryRouter>
      <WorkSidebarTree
        onCreateList={vi.fn()}
        onCreateGroup={vi.fn()}
        onManageGroup={vi.fn()}
        onToggleCollapse={vi.fn()}
        onNavigate={onNavigate}
      />
      <ConfirmDialogHost />
    </MemoryRouter>,
  )
}

describe('WorkSidebarTree', () => {
  it('reports navigation when a top-level project is picked, so the mobile sheet can close', async () => {
    const onNavigate = vi.fn()
    renderTree(onNavigate)

    await userEvent.click(screen.getByRole('link', { name: 'Tuyển dụng & Đào tạo Q3' }))

    expect(onNavigate).toHaveBeenCalledTimes(1)
  })

  it('reports navigation for a project nested two groups deep', async () => {
    const onNavigate = vi.fn()
    renderTree(onNavigate)

    await userEvent.click(screen.getByRole('link', { name: 'Kiểm kê kho cuối quý' }))

    expect(onNavigate).toHaveBeenCalledTimes(1)
  })

  it('stays quiet when a group is merely expanded or collapsed', async () => {
    const onNavigate = vi.fn()
    renderTree(onNavigate)

    await userEvent.click(screen.getByRole('button', { name: 'Khối Vận hành' }))

    expect(onNavigate).not.toHaveBeenCalled()
  })

  it('works without the callback — the pinned desktop tree never passes one', async () => {
    renderTree()

    await expect(
      userEvent.click(screen.getByRole('link', { name: 'Tuyển dụng & Đào tạo Q3' })),
    ).resolves.not.toThrow()
  })

  it('shows a pinned project in the "Đã ghim" block and in its tree position', () => {
    pinState.pinned = [24]
    renderTree()

    const block = screen.getByLabelText('Dự án đã ghim')
    expect(within(block).getByRole('link', { name: 'Kiểm kê kho cuối quý' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Kiểm kê kho cuối quý' })).toHaveLength(2)
  })

  it('has no pinned block when nothing is pinned, and ignores ids that left the tree', () => {
    renderTree()
    expect(screen.queryByLabelText('Dự án đã ghim')).not.toBeInTheDocument()

    pinState.pinned = [999]
    renderTree()
    expect(screen.queryByLabelText('Dự án đã ghim')).not.toBeInTheDocument()
  })

  it('toggles a pin without navigating', async () => {
    const onNavigate = vi.fn()
    renderTree(onNavigate)

    await userEvent.click(screen.getByRole('button', { name: 'Ghim Tuyển dụng & Đào tạo Q3' }))

    expect(pinState.toggle).toHaveBeenCalledWith(26)
    expect(onNavigate).not.toHaveBeenCalled()
  })
})

describe('WorkSidebarTree — menu "…" lưu trữ / xóa vĩnh viễn dự án (duoc-CR-783)', () => {
  it('only the owner of a project gets the "…" menu', () => {
    renderTree()
    expect(screen.getByRole('button', { name: 'Thao tác với dự án Tuyển dụng & Đào tạo Q3' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thao tác với dự án Kiểm kê kho cuối quý' })).not.toBeInTheDocument()
  })

  it('asks for confirmation before archiving, and archives the right project', async () => {
    const user = userEvent.setup()
    archiveList.mockClear()
    renderTree()
    await user.click(screen.getByRole('button', { name: 'Thao tác với dự án Tuyển dụng & Đào tạo Q3' }))
    await user.click(await screen.findByRole('menuitem', { name: /Đưa vào lưu trữ/ }))
    expect(archiveList).not.toHaveBeenCalled()
    await user.click(await screen.findByRole('button', { name: 'Đưa vào lưu trữ' }))
    expect(archiveList).toHaveBeenCalledWith(26, expect.anything())
    expect(purgeList).not.toHaveBeenCalled()
  })

  it('permanent delete is a separate item with its own confirmation', async () => {
    const user = userEvent.setup()
    purgeList.mockClear()
    archiveList.mockClear()
    renderTree()
    await user.click(screen.getByRole('button', { name: 'Thao tác với dự án Tuyển dụng & Đào tạo Q3' }))
    await user.click(await screen.findByRole('menuitem', { name: /Xóa vĩnh viễn/ }))
    expect(await screen.findByText(/KHÔNG khôi phục được/)).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Xóa vĩnh viễn' }))
    expect(purgeList).toHaveBeenCalledWith(26, expect.anything())
    expect(archiveList).not.toHaveBeenCalled()
  })

  it('does nothing when the confirmation is cancelled', async () => {
    const user = userEvent.setup()
    archiveList.mockClear()
    purgeList.mockClear()
    renderTree()
    await user.click(screen.getByRole('button', { name: 'Thao tác với dự án Tuyển dụng & Đào tạo Q3' }))
    await user.click(await screen.findByRole('menuitem', { name: /Xóa vĩnh viễn/ }))
    await user.click(await screen.findByRole('button', { name: 'Hủy' }))
    expect(purgeList).not.toHaveBeenCalled()
  })
})

describe('WorkSidebarTree — menu "…" chuyển dự án sang nhóm (duoc-CR-783)', () => {
  it('lists only groups I can manage and moves the project there', async () => {
    const user = userEvent.setup()
    updateList.mockClear()
    renderTree()
    await user.click(screen.getByRole('button', { name: 'Thao tác với dự án Tuyển dụng & Đào tạo Q3' }))
    await user.click(await screen.findByRole('menuitem', { name: /Chuyển sang nhóm/ }))
    //  Nhóm cha mình không có vai trò: backend sẽ trả 403 nên không được liệt kê.
    expect(screen.queryByRole('menuitem', { name: 'Khối Vận hành' })).not.toBeInTheDocument()
    //  Dự án đang lẻ: không có "Bỏ khỏi nhóm".
    expect(screen.queryByRole('menuitem', { name: /Bỏ khỏi nhóm/ })).not.toBeInTheDocument()
    //  Chọn bằng bàn phím: jsdom không phát đủ chuỗi sự kiện con trỏ cho menu con của Radix (trên trình duyệt thật bấm
    //  chuột chạy đúng — đã thử tay 19/11/2026).
    const target = await screen.findByRole('menuitem', { name: 'Tổ Kho vận' })
    target.focus()
    await user.keyboard('{Enter}')
    expect(updateList).toHaveBeenCalledWith({ id: 26, values: { group_id: 2 } })
  })
})

describe('WorkSidebarTree — kéo thả đổi nhóm (duoc-CR-783)', () => {
  const dataTransfer = () => ({ setData: vi.fn(), effectAllowed: '', dropEffect: '' })
  const rowOf = (name: string) => {
    const row = screen.getByRole('link', { name }).parentElement
    if (!row) throw new Error(`Không thấy dòng ${name}`)
    return row
  }
  const groupHeaderOf = (name: string) => {
    const header = screen.getByRole('button', { name }).parentElement
    if (!header) throw new Error(`Không thấy nhóm ${name}`)
    return header
  }

  it('drops an owned project onto a group I manage and moves it there', () => {
    updateList.mockClear()
    renderTree()
    const dt = dataTransfer()
    fireEvent.dragStart(rowOf('Tuyển dụng & Đào tạo Q3'), { dataTransfer: dt })
    const target = groupHeaderOf('Tổ Kho vận')
    fireEvent.dragOver(target, { dataTransfer: dt })
    fireEvent.drop(target, { dataTransfer: dt })
    expect(updateList).toHaveBeenCalledWith({ id: 26, values: { group_id: 2 } })
  })

  it('refuses a group I do not manage — the server would answer 403', () => {
    updateList.mockClear()
    renderTree()
    const dt = dataTransfer()
    fireEvent.dragStart(rowOf('Tuyển dụng & Đào tạo Q3'), { dataTransfer: dt })
    const target = groupHeaderOf('Khối Vận hành')
    fireEvent.dragOver(target, { dataTransfer: dt })
    fireEvent.drop(target, { dataTransfer: dt })
    expect(updateList).not.toHaveBeenCalled()
  })

  it('only the owner can drag a project row', () => {
    renderTree()
    expect(rowOf('Tuyển dụng & Đào tạo Q3')).toHaveAttribute('draggable', 'true')
    expect(rowOf('Kiểm kê kho cuối quý')).not.toHaveAttribute('draggable')
  })
})
