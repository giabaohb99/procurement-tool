import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeaveRequestForm } from './leave-request-form'
import { emptyLeaveForm, type LeaveFormValues } from '../utils/leave-form-values'
import { LEAVE_SESSION } from '../types/leave'

/**
 * Ô SỐ NGÀY — con số tự tính KHÔNG được đè lên con số người dùng đã gõ.
 *
 * Lỗi báo 05/09/2026 (đơn NP025): người dùng gõ 4, mở lại tờ đơn thì ô hiện 3
 * (20/09 rơi vào Chủ nhật nên máy tính ra 3 ngày công), lưu xong lại nhảy về 4.
 * Nguyên do: cờ "đã gõ tay" là `useState` trong chính component, nên nó chết
 * theo lần mở màn — mở lại là cờ về `false` và con số gợi ý đè mất số đã lưu.
 *
 * Từ 07/09/2026 ô đó nằm trên TỪNG DÒNG loại nghỉ (một đơn khai được nhiều
 * loại), và tự điền CHỈ áp cho đơn một dòng — xem nhóm bài cuối tệp.
 */

const { useEstimateLeaveDays } = vi.hoisted(() => ({
  useEstimateLeaveDays: vi.fn(),
}))

vi.mock('../hooks/use-leave', () => ({
  useLeaveTypes: () => ({
    data: {
      items: [
        { id: 1, name: 'Phép năm' },
        { id: 2, name: 'Nghỉ không lương' },
      ],
    },
  }),
  useEstimateLeaveDays,
  useLeaveBalanceHint: () => ({ data: undefined, isLoading: true }),
}))

vi.mock('../hooks/use-employees', () => ({
  useEmployees: () => ({
    data: { items: [{ id: 7, code: 'NV007', full_name: 'Lê Thị B' }] },
  }),
}))

const { can } = vi.hoisted(() => ({ can: vi.fn(() => true) }))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can }),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, employee_id: 7, full_name: 'Lê Thị B' } }),
}))

/** Bọc form trong state thật — form là component có kiểm soát, cha giữ giá trị. */
function Harness({ initial }: { initial: LeaveFormValues }) {
  const [value, setValue] = useState(initial)
  return <LeaveRequestForm value={value} onChange={setValue} />
}

function daysInput(line = 1) {
  return screen.getByLabelText(`Số ngày dòng ${line}`)
}

/** Form một dòng «Phép năm» — hình dạng của gần như mọi tờ đơn. */
function formWith(overrides: Partial<LeaveFormValues> = {}): LeaveFormValues {
  return {
    ...emptyLeaveForm(),
    lines: [{ leave_type_id: 1, days: 0 }],
    ...overrides,
  }
}

/** Form một dòng «Phép năm» với số ngày đã có sẵn. */
function formWithDays(days: number, overrides: Partial<LeaveFormValues> = {}) {
  return formWith({ lines: [{ leave_type_id: 1, days }], ...overrides })
}

beforeEach(() => {
  useEstimateLeaveDays.mockReset()
  useEstimateLeaveDays.mockReturnValue({ data: { total_days: 3 } })
  can.mockReset()
  can.mockReturnValue(true)
})

describe('LeaveRequestForm — ô Số ngày', () => {
  it('giữ nguyên số ngày đã lưu của đơn cũ, không để con số tự tính đè lên', () => {
    render(<Harness initial={formWithDays(4)} />)
    expect(daysInput()).toHaveValue('4')
  })

  it('nói ra số ngày công của khoảng để người dùng đối chiếu', () => {
    render(<Harness initial={formWithDays(4)} />)
    expect(screen.getByText(/Khoảng ngày đã chọn có 3 ngày công/)).toBeInTheDocument()
  })

  it('tự điền khi ô còn trống — đó là lý do tồn tại của con số gợi ý', () => {
    render(<Harness initial={formWithDays(0)} />)
    expect(daysInput()).toHaveValue('3')
  })

  it('người dùng gõ đè xong thì con số gợi ý mới KHÔNG được đè lại', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<Harness initial={formWithDays(0)} />)
    expect(daysInput()).toHaveValue('3')

    await user.clear(daysInput())
    await user.type(daysInput(), '4')
    await user.tab()
    expect(daysInput()).toHaveValue('4')

    //  Đổi ngày → backend trả con số gợi ý khác. Số người dùng gõ phải còn.
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 5 } })
    rerender(<Harness initial={formWithDays(0)} />)
    expect(daysInput()).toHaveValue('4')
  })
})

describe('LeaveRequestForm — nghỉ theo GIỜ', () => {
  it('chọn «Theo giờ» thì mọc thêm ô giờ ở CẢ HAI đầu, hai ô ngày còn nguyên', async () => {
    //  Khách bác bản gộp hai ô ngày làm một (07/09/2026): nghỉ từ 14:00 ngày A
    //  đến 10:00 ngày B là tờ đơn có thật.
    const user = userEvent.setup()
    render(<Harness initial={formWith()} />)

    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Theo giờ' }))

    expect(screen.getByLabelText('Từ giờ')).toBeInTheDocument()
    expect(screen.getByLabelText('Đến giờ')).toBeInTheDocument()
    expect(screen.getByText('Từ ngày')).toBeInTheDocument()
    expect(screen.getByText('Đến ngày')).toBeInTheDocument()
    //  Chọn một đầu là đầu kia theo luôn — backend đòi hai ô buổi giống nhau.
    expect(screen.getByRole('combobox', { name: 'Buổi kết thúc' })).toHaveTextContent(
      'Theo giờ',
    )
  })

  it('số ngày của đơn theo giờ là ô CHỈ XEM — không cho gõ đè', () => {
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 0.25 } })
    render(
      <Harness
        initial={formWithDays(0.25, {
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:00',
          to_time: '11:00',
        })}
      />,
    )
    expect(screen.queryByLabelText(/Số ngày dòng/)).not.toBeInTheDocument()
    expect(screen.getByText('Tổng cộng 0.25 ngày')).toBeInTheDocument()
  })

  it('đơn theo giờ LUÔN bám con số máy tính, kể cả khi mở lại đơn đã lưu', () => {
    //  Bắt được lúc test tay 07/09/2026: mở đơn theo giờ đã lưu 0.38 rồi đổi
    //  «Đến ngày», ô số ngày đứng im — vì con số đã lưu bị coi là "người dùng gõ
    //  tay", mà đơn theo giờ thì không có đường gõ tay nào cả.
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 2.31 } })
    render(
      <Harness
        initial={formWithDays(0.38, {
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:30',
          to_time: '12:30',
        })}
      />,
    )
    expect(screen.getByText('Tổng cộng 2.31 ngày')).toBeInTheDocument()
  })

  it('bỏ «Theo giờ» thì XÓA khoảng giờ đã nhập', async () => {
    const user = userEvent.setup()
    render(
      <Harness
        initial={formWith({
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:00',
          to_time: '11:00',
        })}
      />,
    )
    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Cả ngày' }))

    expect(screen.queryByLabelText('Đến giờ')).not.toBeInTheDocument()
  })
})

describe('LeaveRequestForm — nhiều loại nghỉ trong một đơn', () => {
  const twoLines = () =>
    formWith({
      lines: [
        { leave_type_id: 1, days: 3 },
        { leave_type_id: 2, days: 1 },
      ],
    })

  it('cộng số ngày của các dòng thành tổng của đơn', () => {
    render(<Harness initial={twoLines()} />)
    expect(screen.getByText('Tổng cộng 4 ngày')).toBeInTheDocument()
  })

  it('KHÔNG tự điền con số gợi ý khi đơn có từ hai dòng', () => {
    //  Máy không đoán được chia 4 ngày thành 3+1 hay 2+2 — đè con số gợi ý lên
    //  một dòng bất kỳ là âm thầm sửa vào phần quỹ người dùng vừa phân bổ.
    render(<Harness initial={twoLines()} />)
    expect(daysInput(1)).toHaveValue('3')
    expect(daysInput(2)).toHaveValue('1')
  })

  it('thêm dòng thì mọc ra một ô chọn loại nghỉ trống', async () => {
    const user = userEvent.setup()
    render(<Harness initial={formWithDays(3)} />)
    expect(screen.queryByLabelText('Số ngày dòng 2')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Thêm loại nghỉ/ }))
    expect(daysInput(2)).toHaveValue('')
  })

  it('đơn MỘT loại thì KHÔNG bày nút bỏ dòng', () => {
    //  Bấm vào là mất trắng ô chọn, trong khi việc người dùng muốn là ĐỔI loại
    //  — làm bằng chính ô chọn. Bảng rỗng cũng không có chỗ nào bấm để gõ tiếp.
    render(<Harness initial={formWithDays(3)} />)
    expect(screen.queryByRole('button', { name: /Bỏ dòng/ })).not.toBeInTheDocument()
  })

  it('bỏ một dòng thì dòng còn lại ở nguyên đó', async () => {
    const user = userEvent.setup()
    render(<Harness initial={twoLines()} />)

    await user.click(screen.getByRole('button', { name: 'Bỏ dòng 2' }))
    expect(daysInput(1)).toHaveValue('3')
    expect(screen.queryByLabelText('Số ngày dòng 2')).not.toBeInTheDocument()
    expect(screen.getByText('Tổng cộng 3 ngày')).toBeInTheDocument()
  })

  it('cột số ngày có TIÊU ĐỀ — ô số không nhãn là chỗ người dùng phải đoán', () => {
    render(<Harness initial={formWithDays(3)} />)
    expect(screen.getByText('Số ngày')).toBeInTheDocument()
  })

  it('CHƯA chọn loại thì không dựng hộp quỹ phép', () => {
    //  Hộp lúc đó chỉ nói lại đúng thứ ô chọn bên trên đang nói, mà lại chiếm
    //  trọn một hàng viền đứt.
    render(<Harness initial={formWith({ lines: [{ leave_type_id: 0, days: 0 }] })} />)
    expect(screen.queryByText(/Chọn loại nghỉ để xem/)).not.toBeInTheDocument()
  })

  it('loại đã chọn ở dòng khác thì KHÔNG chọn lại được', async () => {
    //  Backend chặn với câu «khai hai lần», nhưng để người dùng chọn xong mới
    //  báo là bắt họ làm hai lần.
    const user = userEvent.setup()
    render(<Harness initial={twoLines()} />)

    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ dòng 1' }))
    expect(screen.getByRole('option', { name: 'Nghỉ không lương' })).toHaveAttribute(
      'aria-disabled',
      'true',
    )
  })

  it('nghỉ theo GIỜ thì không cho thêm dòng', async () => {
    //  Nghỉ hai tiếng mà chia hai loại là ca chưa từng có, và nó phá phép quy đổi.
    const user = userEvent.setup()
    render(<Harness initial={formWith()} />)

    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Theo giờ' }))

    expect(screen.queryByRole('button', { name: /Thêm loại nghỉ/ })).not.toBeInTheDocument()
  })
})

describe('LeaveRequestForm — lập hộ người khác', () => {
  it('có quyền đọc danh bạ thì hiện ô «Người nghỉ»', () => {
    render(<Harness initial={formWith()} />)
    expect(screen.getByText('Người nghỉ')).toBeInTheDocument()
  })

  it('đơn MỚI thì ô «Người nghỉ» điền sẵn CHÍNH MÌNH', () => {
    //  Để trống kèm câu "mặc định là bạn" thì người dùng vẫn phải đoán đơn đứng
    //  tên ai — mà chỗ đó đáng ra là câu trả lời.
    render(<Harness initial={formWith()} />)
    expect(screen.getByText('Lê Thị B (NV007)')).toBeInTheDocument()
  })

  it('KHÔNG có quyền thì giấu hẳn ô đó — đơn luôn đứng tên chính mình', () => {
    can.mockReturnValue(false)
    render(<Harness initial={formWith()} />)
    expect(screen.queryByText('Người nghỉ')).not.toBeInTheDocument()
  })
})
