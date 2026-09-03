import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ListMembersPanel } from './list-members-panel'
import type { WorkMember } from '../types/work'
import { WORK_ROLE } from '../types/work'

/**
 * STRESS TEST cụm MỜI NGƯỜI + ĐỔI VAI TRÒ — lái ô chọn thật, không chỉ dựng ra
 * rồi ngắm.
 *
 * Bốn thứ dễ hỏng lặng lẽ mà bài này ghim:
 *
 *  1. **Ô vai trò tràn hai dòng.** Radix `SelectValue` mặc định chép NGUYÊN
 *     children của mục đang chọn vào ô; mục ở đây có nhãn + câu giải thích, nên
 *     ô cao gấp đôi và câu giải thích bị cắt cụt thành «Mời và gỡ người,» (lỗi
 *     thật 03/09/2026). Câu giải thích chỉ được xuất hiện khi ĐANG MỞ danh sách.
 *  2. **«Chủ sở hữu» lọt vào danh sách gán được.** Backend chặn gán thẳng vai
 *     chủ, nên để nó trong ô chọn là dựng sẵn một cú 400.
 *  3. **Mời nhiều người một lượt** phải gọi đúng số lần, đúng vai trò, rồi dọn
 *     lựa chọn — không dọn thì bấm Mời lần hai là mời lại y hệt.
 *  4. **Đổi vai trò gửi `employee_id`**, không gửi `member.id`. Hai số này bằng
 *     nhau trong dữ liệu mẫu nên lẫn mà không ai thấy.
 */

const members = vi.fn<() => WorkMember[]>()
const addMember = vi.fn()
const removeMember = vi.fn()
const setRole = vi.fn()

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))

vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: {
      items: [
        { id: 900, full_name: 'Người Mới Một', code: 'NM1' },
        { id: 901, full_name: 'Người Mới Hai', code: 'NM2' },
        { id: 902, full_name: 'Người Mới Ba', code: 'NM3' },
      ],
    },
  }),
}))

vi.mock('../hooks/use-work-config', () => ({
  useWorkMembers: () => ({ data: members() }),
  useAddWorkMember: () => ({ mutate: addMember, isPending: false }),
  useRemoveWorkMember: () => ({ mutate: removeMember, isPending: false }),
  useSetWorkMemberRole: () => ({ mutate: setRole, isPending: false }),
}))

function member(id: number, name: string, role: number = WORK_ROLE.MEMBER): WorkMember {
  return {
    id,
    employee_id: id,
    role,
    department_id: null,
    employee_name: name,
    employee_code: `NV${id}`,
  }
}

function show(myRole: number = WORK_ROLE.OWNER) {
  render(<ListMembersPanel open listId={22} myRole={myRole} />)
}

/** Ô chọn vai trò của HÀNG MỜI — khác với ô trên từng dòng thành viên. */
function inviteRoleBox() {
  return screen.getByLabelText('Vai trò cho người được mời')
}

/**
 * Lớp phủ của bộ chọn nhân sự (Radix Popover dựng ra `role="dialog"`).
 *
 * ⚠️ Phải khoanh vùng vào đây mới tick đúng. Tick một người xong thì một CHIP
 * mang đúng tên đó hiện ra bên dưới ô chọn, nên `screen.getByRole('button')`
 * theo tên bắt trúng hai phần tử và ném lỗi "found multiple".
 */
function pickerPopover() {
  return within(screen.getByRole('dialog'))
}

/** Mở bộ chọn nhân sự rồi tick những người có tên cho sẵn. */
async function pickPeople(nguoi: ReturnType<typeof userEvent.setup>, ...names: string[]) {
  await nguoi.click(screen.getByRole('button', { name: /Chọn nhân sự để mời/ }))
  for (const name of names) {
    await nguoi.click(pickerPopover().getByRole('button', { name: new RegExp(name) }))
  }
  //  Đóng lớp phủ lại để nút Mời không bị Radix chặn con trỏ.
  await nguoi.keyboard('{Escape}')
}

beforeEach(() => {
  vi.clearAllMocks()
  members.mockReturnValue([
    member(1, 'Trần Trưởng Phòng', WORK_ROLE.OWNER),
    member(2, 'Vũ Văn Kinh Doanh Một', WORK_ROLE.ADMIN),
    member(3, 'Bùi Thị Kinh Doanh Hai'),
    member(4, 'Lê Quản Lý TM', WORK_ROLE.VIEWER),
  ])
})

describe('Ô chọn vai trò — hình dáng', () => {
  it('ô ĐÃ CHỌN chỉ in nhãn, KHÔNG in câu giải thích', () => {
    //  Lỗi thật: ô hiện «Quản trị / Mời và gỡ người,» — hai dòng, dòng dưới cụt.
    show()
    const box = screen.getByLabelText('Vai trò của Vũ Văn Kinh Doanh Một')
    expect(box).toHaveTextContent('Quản trị')
    expect(box).not.toHaveTextContent('Mời và gỡ người')
  })

  it('MỞ danh sách ra thì mới thấy câu giải thích của từng vai', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(inviteRoleBox())

    const list = await screen.findByRole('listbox')
    expect(within(list).getByText('Mời và gỡ người, sửa thông tin dự án')).toBeInTheDocument()
    expect(within(list).getByText('Tạo và sửa công việc')).toBeInTheDocument()
    expect(within(list).getByText('Chỉ xem, không sửa được gì')).toBeInTheDocument()
  })

  it('danh sách gán được KHÔNG có «Chủ sở hữu» — backend chặn gán thẳng', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(inviteRoleBox())

    const list = await screen.findByRole('listbox')
    expect(within(list).getAllByRole('option')).toHaveLength(3)
    expect(within(list).queryByText('Chủ sở hữu')).not.toBeInTheDocument()
  })

  it('vai trò mặc định lúc mời là Thành viên, không phải Quản trị', () => {
    //  Mặc định rơi vào Quản trị thì mời nhầm một lượt là cả nhóm gỡ được nhau.
    show()
    expect(inviteRoleBox()).toHaveTextContent('Thành viên')
  })
})

describe('Đổi vai trò người đã ở trong dự án', () => {
  it('chọn vai mới thì gọi API với employee_id, KHÔNG phải member.id', async () => {
    members.mockReturnValue([
      member(1, 'Trần Trưởng Phòng', WORK_ROLE.OWNER),
      { ...member(2, 'Vũ Văn Kinh Doanh Một', WORK_ROLE.ADMIN), id: 555, employee_id: 2 },
    ])
    const nguoi = userEvent.setup()
    show()

    await nguoi.click(screen.getByLabelText('Vai trò của Vũ Văn Kinh Doanh Một'))
    await nguoi.click(await screen.findByRole('option', { name: /Khách xem/ }))

    expect(setRole).toHaveBeenCalledWith({ employee_id: 2, role: WORK_ROLE.VIEWER })
    expect(setRole).toHaveBeenCalledTimes(1)
  })

  it('hạ Quản trị xuống Thành viên gửi đúng mã vai trò', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(screen.getByLabelText('Vai trò của Vũ Văn Kinh Doanh Một'))
    await nguoi.click(await screen.findByRole('option', { name: /Thành viên/ }))

    expect(setRole).toHaveBeenCalledWith({ employee_id: 2, role: WORK_ROLE.MEMBER })
  })

  it('đổi vai trò KHÔNG đụng tới hàng mời — hai ô độc lập', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(screen.getByLabelText('Vai trò của Lê Quản Lý TM'))
    await nguoi.click(await screen.findByRole('option', { name: /Quản trị/ }))

    expect(setRole).toHaveBeenCalledWith({ employee_id: 4, role: WORK_ROLE.ADMIN })
    //  Ô của hàng mời vẫn nguyên mặc định.
    expect(inviteRoleBox()).toHaveTextContent('Thành viên')
    expect(addMember).not.toHaveBeenCalled()
  })

  it('mỗi dòng có ô riêng — đổi dòng này không kéo theo dòng kia', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(screen.getByLabelText('Vai trò của Bùi Thị Kinh Doanh Hai'))
    await nguoi.click(await screen.findByRole('option', { name: /Khách xem/ }))

    expect(setRole).toHaveBeenCalledTimes(1)
    expect(setRole).toHaveBeenCalledWith({ employee_id: 3, role: WORK_ROLE.VIEWER })
    //  Dòng Quản trị vẫn hiện Quản trị.
    expect(screen.getByLabelText('Vai trò của Vũ Văn Kinh Doanh Một')).toHaveTextContent('Quản trị')
  })
})

describe('Mời người', () => {
  it('chưa chọn ai thì nút Mời tắt và không hiện số đếm', () => {
    show()
    const btn = screen.getByRole('button', { name: /^Mời/ })
    expect(btn).toBeDisabled()
    expect(btn).toHaveTextContent(/^Mời$/)
  })

  it('chọn MỘT người rồi bấm Mời: gọi đúng một lần, đúng vai mặc định', async () => {
    const nguoi = userEvent.setup()
    show()
    await pickPeople(nguoi, 'Người Mới Một')
    await nguoi.click(screen.getByRole('button', { name: /^Mời/ }))

    expect(addMember).toHaveBeenCalledTimes(1)
    expect(addMember).toHaveBeenCalledWith({ employee_id: 900, role: WORK_ROLE.MEMBER })
  })

  it('chọn BA người: nút hiện số đếm và gọi đúng ba lần', async () => {
    const nguoi = userEvent.setup()
    show()
    await pickPeople(nguoi, 'Người Mới Một', 'Người Mới Hai', 'Người Mới Ba')

    const btn = screen.getByRole('button', { name: /^Mời/ })
    expect(btn).toHaveTextContent('Mời (3)')

    await nguoi.click(btn)
    expect(addMember).toHaveBeenCalledTimes(3)
    expect(addMember.mock.calls.map(([arg]) => arg.employee_id).sort()).toEqual([900, 901, 902])
  })

  it('đổi vai trò TRƯỚC khi mời thì mọi người được mời theo vai đó', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(inviteRoleBox())
    await nguoi.click(await screen.findByRole('option', { name: /Khách xem/ }))

    await pickPeople(nguoi, 'Người Mới Một', 'Người Mới Hai')
    await nguoi.click(screen.getByRole('button', { name: /^Mời/ }))

    expect(addMember).toHaveBeenCalledTimes(2)
    for (const [arg] of addMember.mock.calls) {
      expect(arg.role).toBe(WORK_ROLE.VIEWER)
    }
  })

  it('mời xong thì DỌN lựa chọn — bấm lần nữa không mời lại y hệt', async () => {
    //  Không dọn thì người dùng bấm hai lần (mạng chậm, tưởng chưa ăn) là gửi
    //  hai lượt giống hệt nhau.
    const nguoi = userEvent.setup()
    show()
    await pickPeople(nguoi, 'Người Mới Một')
    await nguoi.click(screen.getByRole('button', { name: /^Mời/ }))

    expect(screen.getByRole('button', { name: /^Mời/ })).toBeDisabled()
  })

  it('bỏ tick hết thì nút Mời tắt lại', async () => {
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(screen.getByRole('button', { name: /Chọn nhân sự để mời/ }))
    await nguoi.click(pickerPopover().getByRole('button', { name: /Người Mới Một/ }))
    //  Tick lần hai là bỏ tick — vẫn bấm đúng dòng TRONG lớp phủ, không bấm
    //  nhầm sang chip vừa hiện ra bên ngoài.
    await nguoi.click(pickerPopover().getByRole('button', { name: /Người Mới Một/ }))
    await nguoi.keyboard('{Escape}')

    expect(screen.getByRole('button', { name: /^Mời/ })).toBeDisabled()
    expect(addMember).not.toHaveBeenCalled()
  })
})

describe('Gỡ người', () => {
  it('gỡ gửi MEMBER id, không gửi employee id', async () => {
    members.mockReturnValue([
      member(1, 'Trần Trưởng Phòng', WORK_ROLE.OWNER),
      { ...member(2, 'Vũ Văn Kinh Doanh Một', WORK_ROLE.ADMIN), id: 555, employee_id: 2 },
    ])
    const nguoi = userEvent.setup()
    show()
    await nguoi.click(
      screen.getByRole('button', { name: 'Gỡ Vũ Văn Kinh Doanh Một khỏi dự án' }),
    )
    expect(removeMember).toHaveBeenCalledWith(555)
  })

  it('không có nút gỡ trên dòng CHỦ SỞ HỮU', () => {
    show()
    expect(
      screen.queryByRole('button', { name: 'Gỡ Trần Trưởng Phòng khỏi dự án' }),
    ).not.toBeInTheDocument()
  })
})

describe('Quyền sở hữu chỉ để NHÌN', () => {
  it('dòng chủ sở hữu chỉ có huy hiệu — không ô vai trò, không nút gỡ', () => {
    show(WORK_ROLE.OWNER)
    const row = screen.getByText('Trần Trưởng Phòng').closest('li')!
    expect(within(row).getByText('Chủ sở hữu')).toBeInTheDocument()
    expect(within(row).queryByLabelText(/^Vai trò của/)).not.toBeInTheDocument()
    expect(within(row).queryByRole('button', { name: /^Gỡ /})).not.toBeInTheDocument()
  })

  it('KHÔNG còn nút chuyển quyền lẫn thu hồi ở bất kỳ dòng nào', () => {
    //  Chủ đầu tư chốt 03/09/2026: bỏ hẳn chuyển quyền khỏi giao diện. Backend
    //  vẫn giữ endpoint cho ca dự án mồ côi (gọi tay qua API), nên bài này là
    //  chốt chặn duy nhất giữ cho nút đó không lẻn về màn hình.
    show(WORK_ROLE.OWNER)
    expect(screen.queryByRole('button', { name: /Chuyển quyền/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thu hồi' })).not.toBeInTheDocument()
    expect(screen.queryByText(/Bạn vừa chuyển quyền sở hữu/)).not.toBeInTheDocument()
  })
})
