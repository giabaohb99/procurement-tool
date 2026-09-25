import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { GroupManageDialog } from './group-manage-dialog'
import type { WorkGroup, WorkMember } from '../types/work'
import { WORK_ROLE } from '../types/work'

/**
 * Hộp «Quản lý nhóm» — bao-CR-482. Ba thứ dễ vỡ lặng:
 *  1. Hai ngưỡng quyền: Chủ sở hữu mới sửa tên / lưu trữ; Quản trị chỉ mời + gỡ.
 *  2. Lưu chỉ gửi khi CÓ ĐỔI và tên không rỗng — nút Lưu phải khóa đúng lúc.
 *  3. Lưu trữ phải hỏi lại một nhịp, không bấm một cái là mất nhóm.
 */

const members = vi.fn<() => WorkMember[]>()
const addMember = vi.fn()
const removeMember = vi.fn()
const updateGroup = vi.fn()
const archiveGroup = vi.fn()

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { items: [{ id: 900, full_name: 'Người Mới', code: 'NM1' }] } }),
}))
vi.mock('../hooks/use-work-groups', () => ({
  useWorkGroupMembers: () => ({ data: members() }),
  useAddWorkGroupMember: () => ({ mutate: addMember, isPending: false }),
  useRemoveWorkGroupMember: () => ({ mutate: removeMember, isPending: false }),
  useUpdateWorkGroup: () => ({ mutate: updateGroup, isPending: false }),
  useArchiveWorkGroup: () => ({ mutate: archiveGroup, isPending: false }),
}))

function group(myRole: number): WorkGroup {
  return { id: 1, name: 'DX', description: '', parent_id: null, sort_order: 0, is_archived: 0, my_role: myRole }
}

beforeEach(() => {
  members.mockReturnValue([
    { id: 1, employee_id: 231, role: WORK_ROLE.OWNER, department_id: null, employee_name: 'Huỳnh Gia Bảo', employee_code: 'NSU209', avatar: '' },
  ])
  addMember.mockReset()
  removeMember.mockReset()
  updateGroup.mockReset()
  archiveGroup.mockReset()
})

describe('GroupManageDialog — bao-CR-482', () => {
  it('chủ sở hữu: sửa được tên, Lưu chỉ mở khi có đổi, gửi đúng giá trị', async () => {
    const user = userEvent.setup()
    render(<GroupManageDialog open group={group(WORK_ROLE.OWNER)} onClose={() => {}} />)
    const save = screen.getByRole('button', { name: 'Lưu thông tin' })
    expect(save).toBeDisabled()
    const name = screen.getByLabelText('Tên nhóm')
    await user.clear(name)
    await user.type(name, 'DX 2026')
    expect(save).toBeEnabled()
    await user.click(save)
    expect(updateGroup).toHaveBeenCalledWith({ id: 1, values: { name: 'DX 2026', description: '' } })
  })

  it('chủ sở hữu: tên rỗng thì khóa Lưu và báo lỗi', async () => {
    const user = userEvent.setup()
    render(<GroupManageDialog open group={group(WORK_ROLE.OWNER)} onClose={() => {}} />)
    await user.clear(screen.getByLabelText('Tên nhóm'))
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeDisabled()
    expect(screen.getByText('Tên nhóm không được để trống.')).toBeInTheDocument()
  })

  it('lưu trữ hỏi lại một nhịp rồi mới gọi', async () => {
    const user = userEvent.setup()
    render(<GroupManageDialog open group={group(WORK_ROLE.OWNER)} onClose={() => {}} />)
    await user.click(screen.getByRole('button', { name: 'Lưu trữ nhóm' }))
    expect(archiveGroup).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Lưu trữ' }))
    expect(archiveGroup).toHaveBeenCalledWith(1, expect.anything())
  })

  it('quản trị: thông tin chỉ đọc, không có nút Lưu / Lưu trữ, nhưng vẫn có hàng mời', () => {
    render(<GroupManageDialog open group={group(WORK_ROLE.ADMIN)} onClose={() => {}} />)
    expect(screen.queryByLabelText('Tên nhóm')).toBeNull()
    expect(screen.getByText('DX')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu thông tin' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Lưu trữ nhóm' })).toBeNull()
    expect(screen.getByRole('button', { name: /^Mời/ })).toBeInTheDocument()
  })

  it('khách xem: không có hàng mời, không có nút gỡ', () => {
    render(<GroupManageDialog open group={group(WORK_ROLE.VIEWER)} onClose={() => {}} />)
    expect(screen.queryByRole('button', { name: /^Mời/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Gỡ/ })).toBeNull()
  })
})
