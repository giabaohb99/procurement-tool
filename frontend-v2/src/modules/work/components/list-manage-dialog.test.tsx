import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ListManageDialog } from './list-manage-dialog'
import { LIST_DESCRIPTION_MAX, LIST_NAME_MAX } from '../hooks/use-list-info-form'
import type { WorkList, WorkMember } from '../types/work'
import { WORK_ROLE } from '../types/work'

/**
 * STRESS TEST hộp «Quản lý dự án».
 *
 * Bài này đi tìm chỗ VỠ, không đi xác nhận chỗ chạy. Bốn nhóm rủi ro:
 *
 *  1. **Hai ngưỡng quyền khác nhau** — sửa thông tin đòi CHỦ SỞ HỮU (`CAN_OWN`),
 *     mời/gỡ/đổi vai trò chỉ đòi QUẢN TRỊ (`CAN_MANAGE`). Gộp nhầm làm một là
 *     hoặc Quản trị gõ xong ăn 403, hoặc Khách xem bấm được nút gỡ người.
 *  2. **Bất biến một chủ sở hữu** — dòng chủ không được có ô đổi vai trò lẫn nút
 *     gỡ. Backend chặn cả hai, nên hiện ra là dựng sẵn một cú 400.
 *  3. **Dữ liệu bẩn từ máy chủ** — tên rỗng, tên `null`, mã rỗng, trùng tên.
 *  4. **Số lượng lớn** — vài trăm thành viên thì lọc, sắp xếp và khoá React phải
 *     còn đúng.
 */

const members = vi.fn<() => WorkMember[]>()
const addMember = vi.fn()
const removeMember = vi.fn()
const setRole = vi.fn()
const updateList = vi.fn()
let canReadEmployees = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => canReadEmployees }),
}))

vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: {
      items: [
        { id: 900, full_name: 'Người Mới Một', code: 'NM1' },
        { id: 901, full_name: 'Người Mới Hai', code: 'NM2' },
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

vi.mock('../hooks/use-work-lists', () => ({
  useUpdateWorkList: () => ({ mutate: updateList, isPending: false }),
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

const LIST: WorkList = {
  id: 22,
  name: 'Dự án ERP v2',
  description: 'Dựng phân hệ mới trên frontend-v2.',
  color: 'blue',
  group_id: null,
  sort_order: 0,
  is_archived: 0,
  my_role: WORK_ROLE.OWNER,
  task_count: 0,
  task_done: 0,
  created_at: '2026-09-01T00:00:00',
  owner: null,
  members: [],
}

function show(myRole: number | null, list: Partial<WorkList> = {}) {
  render(
    <ListManageDialog
      open
      list={{ ...LIST, ...list }}
      myRole={myRole}
      onClose={vi.fn()}
    />,
  )
}

/** Dòng thành viên mang tên này — dùng để soi cục nút bên phải của đúng dòng đó. */
function rowOf(name: string): HTMLElement {
  const row = screen.getByText(name).closest('li')
  if (!row) throw new Error(`Không thấy dòng của «${name}»`)
  return row
}

beforeEach(() => {
  vi.clearAllMocks()
  canReadEmployees = true
  members.mockReturnValue([
    member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
    member(2, 'Dego Admin', WORK_ROLE.ADMIN),
    member(3, 'Nguyễn Nhân Viên', WORK_ROLE.MEMBER),
  ])
})

describe('ListManageDialog — hai ngưỡng quyền', () => {
  it('CHỦ SỞ HỮU sửa được thông tin và có nút Lưu ở đáy hộp', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.getByLabelText('Tên dự án')).toHaveValue('Dự án ERP v2')
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeInTheDocument()
  })

  it('QUẢN TRỊ KHÔNG thấy ô nhập lẫn nút Lưu — backend gác update_list bằng CAN_OWN', () => {
    //  Đây là ca đã suýt lọt: mở ô nhập theo `canManage` thì Quản trị gõ xong
    //  bấm Lưu và nhận 403, tệ hơn hẳn việc thấy ngay mình không sửa được.
    show(WORK_ROLE.ADMIN)
    expect(screen.queryByLabelText('Tên dự án')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu thông tin' })).not.toBeInTheDocument()
    //  …nhưng vẫn đọc được tên, và đọc được nghĩa là BÔI ĐEN COPY được.
    expect(screen.getByText('Dự án ERP v2')).toBeInTheDocument()
  })

  it('QUẢN TRỊ vẫn mời và đổi vai trò được — hai quyền độc lập nhau', () => {
    show(WORK_ROLE.ADMIN)
    expect(screen.getByRole('button', { name: /^Mời/ })).toBeInTheDocument()
    expect(screen.getByLabelText('Vai trò của Dego Admin')).toBeInTheDocument()
  })

  it('KHÁCH XEM không có hàng mời, không ô đổi vai trò, không nút gỡ', () => {
    show(WORK_ROLE.VIEWER)
    expect(screen.queryByRole('button', { name: /^Mời/ })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/^Vai trò của/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Gỡ /})).not.toBeInTheDocument()
  })

  it('myRole null (chưa nạp xong / không phải thành viên) xử như thấp nhất, không mở gì', () => {
    //  `myRole === null` mà lỡ so bằng `<=` thì `null <= 2` trong JS là TRUE —
    //  đúng kiểu lỗi mở toang mà không ai thấy.
    show(null)
    expect(screen.queryByRole('button', { name: /^Mời/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu thông tin' })).not.toBeInTheDocument()
  })

  it('không có quyền employee.read thì ẩn hàng mời nhưng vẫn xem được thành viên', () => {
    //  Gọi danh bạ khi thiếu quyền là người dùng ăn toast 403 ngay lúc mở hộp.
    canReadEmployees = false
    show(WORK_ROLE.OWNER)
    expect(screen.queryByRole('button', { name: /^Mời/ })).not.toBeInTheDocument()
    expect(screen.getByText('Lý Phó Phòng')).toBeInTheDocument()
  })
})

describe('ListManageDialog — bất biến MỘT chủ sở hữu', () => {
  it('dòng chủ sở hữu không có ô đổi vai trò và không có nút gỡ', () => {
    //  Backend chặn cả hai (`add_member` và `remove_member` từ chối dòng OWNER),
    //  nên hiện nút ra là dựng sẵn một cú 400 cho người dùng bấm vào.
    show(WORK_ROLE.OWNER)
    const row = rowOf('Lý Phó Phòng')
    expect(within(row).queryByLabelText(/^Vai trò của/)).not.toBeInTheDocument()
    expect(within(row).queryByRole('button', { name: /^Gỡ /})).not.toBeInTheDocument()
    expect(within(row).getByText('Chủ sở hữu')).toBeInTheDocument()
  })

  it('KHÔNG có nút chuyển quyền sở hữu, kể cả khi người xem chính là chủ', () => {
    //  Chủ đầu tư chốt 03/09/2026: quyền sở hữu chỉ để NHÌN. Backend vẫn còn
    //  endpoint chuyển quyền (dùng cho ca dự án mồ côi, gọi tay qua API), nên
    //  bài này là chốt chặn duy nhất giữ cho nút đó không lẻn về giao diện.
    show(WORK_ROLE.OWNER)
    expect(screen.queryByRole('button', { name: /Chuyển quyền/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thu hồi' })).not.toBeInTheDocument()
    //  …nhưng huy hiệu chủ sở hữu vẫn phải còn.
    expect(within(rowOf('Lý Phó Phòng')).getByText('Chủ sở hữu')).toBeInTheDocument()
  })

  it('dữ liệu lỗi có HAI dòng chủ thì cả hai đều khoá, không đẻ thêm đường sửa sai', () => {
    //  Ca thật ngày 03/09/2026: `transfer_ownership` hạ nhầm dòng nên dự án #22
    //  có 3 chủ. Giao diện phải chịu được, không được vỡ hay tự đoán ai là chủ.
    members.mockReturnValue([
      member(1, 'Chủ Một', WORK_ROLE.OWNER),
      member(2, 'Chủ Hai', WORK_ROLE.OWNER),
      member(3, 'Nguyễn Nhân Viên', WORK_ROLE.MEMBER),
    ])
    show(WORK_ROLE.OWNER)
    expect(screen.getAllByText('Chủ sở hữu')).toHaveLength(2)
    expect(screen.queryByLabelText('Vai trò của Chủ Hai')).not.toBeInTheDocument()
  })
})

describe('ListManageDialog — dữ liệu bẩn từ máy chủ', () => {
  it('tên rỗng lùi về «Nhân sự #id», không để dòng trắng', () => {
    members.mockReturnValue([member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER), member(77, '')])
    show(WORK_ROLE.OWNER)
    expect(screen.getByText('Nhân sự #77')).toBeInTheDocument()
  })

  it('tên null (hồ sơ nhân sự đã xoá) không làm vỡ sắp xếp lẫn lọc', async () => {
    const broken = { ...member(78, ''), employee_name: null as unknown as string }
    members.mockReturnValue([member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER), broken])
    show(WORK_ROLE.OWNER)
    expect(screen.getByText('Nhân sự #78')).toBeInTheDocument()
  })

  it('hai người TRÙNG TÊN vẫn là hai dòng riêng — khoá React theo id, không theo tên', () => {
    members.mockReturnValue([
      member(1, 'Nguyễn Văn A', WORK_ROLE.OWNER),
      member(2, 'Nguyễn Văn A'),
      member(3, 'Nguyễn Văn A'),
    ])
    show(WORK_ROLE.OWNER)
    expect(screen.getAllByText('Nguyễn Văn A')).toHaveLength(3)
  })

  it('danh sách rỗng nói rõ là chưa mời ai, không hiện bảng trắng', () => {
    members.mockReturnValue([])
    show(WORK_ROLE.OWNER)
    expect(screen.getByText(/Chưa có ai được mời riêng/)).toBeInTheDocument()
    expect(screen.getByText('(0)')).toBeInTheDocument()
  })
})

describe('ListManageDialog — số lượng lớn', () => {
  it('200 thành viên: hiện đủ, đếm đúng, và bật ô lọc', () => {
    members.mockReturnValue([
      member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
      ...Array.from({ length: 199 }, (_, i) => member(i + 2, `Nhân Viên Số ${i + 2}`)),
    ])
    show(WORK_ROLE.OWNER)
    expect(screen.getByText('(200)')).toBeInTheDocument()
    expect(screen.getByLabelText('Lọc danh sách thành viên')).toBeInTheDocument()
  })

  it('dưới ngưỡng thì KHÔNG hiện ô lọc — ba người mà bắt lọc là thừa', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.queryByLabelText('Lọc danh sách thành viên')).not.toBeInTheDocument()
  })

  it('lọc khớp cả TÊN lẫn MÃ nhân sự, không phân biệt hoa thường', async () => {
    const nguoi = userEvent.setup()
    members.mockReturnValue([
      member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
      ...Array.from({ length: 9 }, (_, i) => member(i + 2, `Nhân Viên Số ${i + 2}`)),
    ])
    show(WORK_ROLE.OWNER)

    const box = screen.getByLabelText('Lọc danh sách thành viên')
    await nguoi.type(box, 'nv5')
    expect(screen.getByText('Nhân Viên Số 5')).toBeInTheDocument()
    expect(screen.queryByText('Lý Phó Phòng')).not.toBeInTheDocument()

    await nguoi.clear(box)
    await nguoi.type(box, 'PHÓ')
    expect(screen.getByText('Lý Phó Phòng')).toBeInTheDocument()
  })

  it('lọc không ra ai thì báo rõ, KHÁC hẳn câu «chưa mời ai»', () => {
    //  Hai câu này lẫn nhau là người dùng tưởng vừa mất sạch thành viên.
    members.mockReturnValue([
      member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
      ...Array.from({ length: 9 }, (_, i) => member(i + 2, `Nhân Viên Số ${i + 2}`)),
    ])
    show(WORK_ROLE.OWNER)
    return userEvent
      .setup()
      .type(screen.getByLabelText('Lọc danh sách thành viên'), 'không-ai-tên-vầy')
      .then(() => {
        expect(screen.getByText('Không có ai khớp từ khóa.')).toBeInTheDocument()
        expect(screen.queryByText(/Chưa có ai được mời riêng/)).not.toBeInTheDocument()
      })
  })

  it('chủ sở hữu luôn đứng ĐẦU dù máy chủ trả về cuối', () => {
    members.mockReturnValue([
      member(3, 'Zz Cuối Bảng'),
      member(2, 'Aa Đầu Bảng', WORK_ROLE.ADMIN),
      member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
    ])
    show(WORK_ROLE.OWNER)
    const names = screen.getAllByRole('listitem').map((li) => li.textContent ?? '')
    expect(names[0]).toContain('Lý Phó Phòng')
    expect(names[1]).toContain('Aa Đầu Bảng')
  })
})

describe('ListManageDialog — ô Thông tin', () => {
  it('mô tả có bộ đếm hiện SUỐT và trần đúng 1500', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.getByText(`${LIST.description.length}/${LIST_DESCRIPTION_MAX}`)).toBeInTheDocument()
    expect(screen.getByLabelText('Mô tả')).toHaveAttribute(
      'maxlength',
      String(LIST_DESCRIPTION_MAX),
    )
  })

  it('ô tên chặn ở đúng trần của cột DB', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.getByLabelText('Tên dự án')).toHaveAttribute('maxlength', String(LIST_NAME_MAX))
  })

  it('chưa sửa gì thì nút Lưu tắt — bấm là một lượt ghi thừa', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeDisabled()
  })

  it('xoá trắng tên thì KHÓA nút Lưu và nói rõ vì sao', async () => {
    const nguoi = userEvent.setup()
    show(WORK_ROLE.OWNER)
    await nguoi.clear(screen.getByLabelText('Tên dự án'))
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeDisabled()
    expect(screen.getByText(/Tên không được để trống/)).toBeInTheDocument()
    expect(updateList).not.toHaveBeenCalled()
  })

  it('tên chỉ toàn khoảng trắng cũng bị coi là rỗng', async () => {
    const nguoi = userEvent.setup()
    show(WORK_ROLE.OWNER)
    const input = screen.getByLabelText('Tên dự án')
    await nguoi.clear(input)
    await nguoi.type(input, '    ')
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeDisabled()
  })

  it('lưu thì cắt khoảng trắng thừa hai đầu, không lưu nguyên chuỗi người ta lỡ gõ', async () => {
    const nguoi = userEvent.setup()
    show(WORK_ROLE.OWNER)
    const input = screen.getByLabelText('Tên dự án')
    await nguoi.clear(input)
    await nguoi.type(input, '  Dự án mới  ')
    await nguoi.click(screen.getByRole('button', { name: 'Lưu thông tin' }))

    expect(updateList).toHaveBeenCalledWith(
      expect.objectContaining({ id: 22, values: expect.objectContaining({ name: 'Dự án mới' }) }),
    )
  })
})

describe('ListManageDialog — thao tác gọi đúng API', () => {
  it('gỡ người gửi MEMBER id, không gửi employee id', async () => {
    //  Hai số này hay lẫn nhau vì trong dữ liệu mẫu chúng thường bằng nhau.
    members.mockReturnValue([
      member(1, 'Lý Phó Phòng', WORK_ROLE.OWNER),
      { ...member(2, 'Dego Admin', WORK_ROLE.ADMIN), id: 555, employee_id: 2 },
    ])
    show(WORK_ROLE.OWNER)
    await userEvent.setup().click(screen.getByRole('button', { name: 'Gỡ Dego Admin khỏi dự án' }))
    expect(removeMember).toHaveBeenCalledWith(555)
  })

  it('chưa chọn ai thì nút Mời tắt', () => {
    show(WORK_ROLE.OWNER)
    expect(screen.getByRole('button', { name: /^Mời/ })).toBeDisabled()
  })
})
