import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

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
      children: [makeGroup(2, 'Tổ Kho vận', { lists: [makeList(24, 'Kiểm kê kho cuối quý')] })],
    }),
  ],
  lists: [makeList(26, 'Tuyển dụng & Đào tạo Q3')],
}

vi.mock('../hooks/use-work-lists', () => ({
  useWorkSidebar: () => ({ data: sidebar, isLoading: false }),
}))

function renderTree(onNavigate?: () => void) {
  return render(
    <MemoryRouter>
      <WorkSidebarTree
        onCreateList={vi.fn()}
        onCreateGroup={vi.fn()}
        onToggleCollapse={vi.fn()}
        onNavigate={onNavigate}
      />
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
})
