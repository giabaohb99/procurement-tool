import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeaveRequestForm } from './leave-request-form'
import {
  emptyLeaveForm,
  formValuesOf,
  toLeavePayload,
  type LeaveFormValues,
} from '../utils/leave-form-values'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

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

const { useEstimateLeavePeriods } = vi.hoisted(() => ({
  useEstimateLeavePeriods: vi.fn(),
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
  useEstimateLeavePeriods,
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

/** Như `Harness`, nhưng chuyển bản form mới nhất ra ngoài để kiểm thân yêu cầu sẽ gửi. */
function SpyHarness({
  initial,
  onValue,
}: {
  initial: LeaveFormValues
  onValue: (v: LeaveFormValues) => void
}) {
  const [value, setValue] = useState(initial)
  return (
    <LeaveRequestForm
      value={value}
      onChange={(next) => {
        onValue(next)
        setValue(next)
      }}
    />
  )
}

function daysInput(line = 1) {
  return screen.getByLabelText(`Số ngày dòng ${line}`)
}

/** Form một dòng "Phép năm" — hình dạng của gần như mọi tờ đơn. */
function formWith(overrides: Partial<LeaveFormValues> = {}): LeaveFormValues {
  return {
    ...emptyLeaveForm(),
    lines: [{ leave_type_id: 1, days: 0 }],
    ...overrides,
  }
}

/** Một khoảng nghỉ THEO GIỜ trong ngày hôm nay của form rỗng. */
function hourlyPeriods() {
  const [p] = emptyLeaveForm().periods
  return [{ ...p, from_session: LEAVE_SESSION.HOURLY, to_session: LEAVE_SESSION.HOURLY }]
}

/** Form một dòng "Phép năm" với số ngày đã có sẵn. */
function formWithDays(days: number, overrides: Partial<LeaveFormValues> = {}) {
  return formWith({ lines: [{ leave_type_id: 1, days }], ...overrides })
}

beforeEach(() => {
  useEstimateLeavePeriods.mockReset()
  useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 3 } })
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
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5 } })
    rerender(<Harness initial={formWithDays(0)} />)
    expect(daysInput()).toHaveValue('4')
  })
})

describe('LeaveRequestForm — nghỉ theo GIỜ', () => {
  it('chọn "Theo giờ" thì mọc thêm ô giờ ở CẢ HAI đầu, hai ô ngày còn nguyên', async () => {
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
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 0.25 } })
    render(
      <Harness
        initial={formWithDays(0.25, {
          periods: hourlyPeriods(),
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
    //  "Đến ngày", ô số ngày đứng im — vì con số đã lưu bị coi là "người dùng gõ
    //  tay", mà đơn theo giờ thì không có đường gõ tay nào cả.
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 2.31 } })
    render(
      <Harness
        initial={formWithDays(0.38, {
          periods: hourlyPeriods(),
          from_time: '09:30',
          to_time: '12:30',
        })}
      />,
    )
    expect(screen.getByText('Tổng cộng 2.31 ngày')).toBeInTheDocument()
  })

  it('bỏ "Theo giờ" thì XÓA khoảng giờ đã nhập', async () => {
    const user = userEvent.setup()
    render(
      <Harness
        initial={formWith({
          periods: hourlyPeriods(),
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
    //  Backend chặn với câu "khai hai lần", nhưng để người dùng chọn xong mới
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
  it('có quyền đọc danh bạ thì hiện ô "Người nghỉ"', () => {
    render(<Harness initial={formWith()} />)
    expect(screen.getByText('Người nghỉ')).toBeInTheDocument()
  })

  it('đơn MỚI thì ô "Người nghỉ" điền sẵn CHÍNH MÌNH', () => {
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

describe('LeaveRequestForm — nhiều khoảng ngày (duoc-CR-683)', () => {
  const owner = [
    { from_date: '2026-10-27', from_session: LEAVE_SESSION.FULL, to_date: '2026-10-27', to_session: LEAVE_SESSION.FULL },
    { from_date: '2026-11-03', from_session: LEAVE_SESSION.AFTERNOON, to_date: '2026-11-07', to_session: LEAVE_SESSION.FULL },
  ]

  it('the TOTAL of all periods auto-fills the single leave-type line', () => {
    useEstimateLeavePeriods.mockReturnValue({
      data: { total_days: 5.5, periods: [{ days: 1 }, { days: 4.5 }] },
    })
    render(<Harness initial={formWith({ periods: owner })} />)
    //  Ô số ngày hiện theo kiểu Việt Nam (dấu phẩy thập phân).
    expect(daysInput()).toHaveValue('5,5')
    expect(screen.getByText('Cộng 2 khoảng: 5.5 ngày')).toBeInTheDocument()
    expect(screen.getByText('· 4.5 ngày')).toBeInTheDocument()
  })

  it('asks for ONE estimate covering every period, for the leave taker and first type', () => {
    render(<Harness initial={formWith({ periods: owner })} />)
    expect(useEstimateLeavePeriods).toHaveBeenLastCalledWith(
      expect.objectContaining({ periods: owner, leave_type_id: 1, employee_id: 7, enabled: true }),
    )
  })

  it('does NOT ask the server while two rows overlap — the red hint already says so', () => {
    const overlapping = [owner[1], { ...owner[1], from_date: '2026-11-05', to_date: '2026-11-05' }]
    render(<Harness initial={formWith({ periods: overlapping })} />)
    expect(useEstimateLeavePeriods).toHaveBeenLastCalledWith(
      expect.objectContaining({ enabled: false }),
    )
  })

  it('shows the server message when the estimate is refused (e.g. periods across two years)', () => {
    useEstimateLeavePeriods.mockReturnValue({
      data: undefined,
      error: { response: { data: { success: false, error: { code: 'HTTP_422', message: 'Đơn nhiều khoảng ngày phải nằm trong cùng một năm.' } } } },
    })
    render(<Harness initial={formWith({ periods: owner })} />)
    expect(screen.getByText('Đơn nhiều khoảng ngày phải nằm trong cùng một năm.')).toBeInTheDocument()
  })

  it('adding a period from a single-period request turns the layout into numbered rows', async () => {
    const user = userEvent.setup()
    render(<Harness initial={formWith()} />)
    await user.click(screen.getByRole('button', { name: /Thêm khoảng ngày/ }))
    expect(screen.getByText('Khoảng ngày 2')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bỏ khoảng ngày 2' })).toBeInTheDocument()
  })

  it('switching to "Theo giờ" on a single period hides "Thêm khoảng ngày"', async () => {
    const user = userEvent.setup()
    render(<Harness initial={formWith()} />)
    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Theo giờ' }))
    expect(screen.queryByRole('button', { name: /Thêm khoảng ngày/ })).not.toBeInTheDocument()
  })
})

/**
 * MỞ LẠI ĐƠN ĐÃ LƯU rồi đổi ngày (duoc-CR-683 M3). Trước bản vá, mọi đơn đã lưu đều bị coi là
 * "số gõ tay": đổi 27/10 + 03/11→07/11 thành 27/10 + 01/11→05/11 mà ô vẫn 5.5 (đúng ra 5), và
 * lưu là giữ quỹ 5.5 ngày. Số đã gõ đè thật thì vẫn phải đứng yên.
 */
describe('LeaveRequestForm — reopening a saved request (duoc-CR-683 M3)', () => {
  const periods = [
    { id: 1, from_date: '2026-10-27', from_session: 1, to_date: '2026-10-27', to_session: 1, days: 1, sort_order: 0 },
    { id: 2, from_date: '2026-11-03', from_session: 3, to_date: '2026-11-07', to_session: 1, days: 4.5, sort_order: 1 },
  ]

  function saved(days: number, overrides: Partial<LeaveRequest> = {}): LeaveFormValues {
    return formValuesOf({
      id: 9,
      code: 'NP009',
      company_id: 1,
      department_id: 1,
      employee_id: 7,
      leave_type_id: 1,
      from_date: '2026-10-27',
      to_date: '2026-11-07',
      from_session: 1,
      to_session: 1,
      unit: LEAVE_UNIT.DAY,
      total_days: days,
      reason: 'Việc nhà',
      contact_phone: '',
      contact_address: '',
      status: LEAVE_STATUS.DRAFT,
      approval_instance_id: 0,
      document_id: 0,
      decision_note: '',
      lines: [{ id: 1, leave_type_id: 1, days, sort_order: 0 }],
      periods,
      ...overrides,
    })
  }

  it('a saved multi-period total that was machine-computed follows the new dates', () => {
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5.5 } })
    let latest = saved(5.5)
    const onValue = (v: LeaveFormValues) => {
      latest = v
    }
    const initial = latest
    const { rerender } = render(<SpyHarness initial={initial} onValue={onValue} />)
    expect(daysInput()).toHaveValue('5,5')

    //  Người dùng dời khoảng 2 → backend ước lượng lại ra 5.
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5 } })
    rerender(<SpyHarness initial={initial} onValue={onValue} />)
    expect(daysInput()).toHaveValue('5')
    //  …và vẫn là số máy: lưu thì để backend tự tính (giữ chốt khoảng 0 ngày công).
    expect(toLeavePayload(latest).lines).toEqual([{ leave_type_id: 1, days: 0 }])
  })

  it('a saved multi-period total the user had overridden stays put when the estimate moves', () => {
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5.5 } })
    let latest = saved(6)
    const onValue = (v: LeaveFormValues) => {
      latest = v
    }
    const initial = latest
    const { rerender } = render(<SpyHarness initial={initial} onValue={onValue} />)
    expect(daysInput()).toHaveValue('6')

    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5 } })
    rerender(<SpyHarness initial={initial} onValue={onValue} />)
    expect(daysInput()).toHaveValue('6')
    expect(toLeavePayload(latest).lines).toEqual([{ leave_type_id: 1, days: 6 }])
  })

  it('a saved single-period request matching the first estimate follows later date changes', () => {
    //  Đơn một khoảng: chỉ nhận ra "số máy" bằng cách so với con số ước lượng đầu tiên.
    const single = saved(3, { periods: [{ ...periods[0], to_date: '2026-10-29', days: 3 }] })
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 3 } })
    const { rerender } = render(<Harness initial={single} />)
    expect(daysInput()).toHaveValue('3')

    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 4 } })
    rerender(<Harness initial={single} />)
    expect(daysInput()).toHaveValue('4')
  })

  it('a saved single-period override (NP025: typed 4, schedule says 3) survives later estimates', () => {
    const single = saved(4, { periods: [{ ...periods[0], to_date: '2026-10-30', days: 4 }] })
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 3 } })
    const { rerender } = render(<Harness initial={single} />)
    expect(daysInput()).toHaveValue('4')

    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 5 } })
    rerender(<Harness initial={single} />)
    expect(daysInput()).toHaveValue('4')
  })
})

describe('LeaveRequestForm — what a fresh form sends (duoc-CR-683 M2)', () => {
  it('an auto-filled single line is sent as days 0, a typed one as the typed number', async () => {
    const user = userEvent.setup()
    useEstimateLeavePeriods.mockReturnValue({ data: { total_days: 3 } })
    let latest = formWith()
    render(
      <SpyHarness
        initial={latest}
        onValue={(v) => {
          latest = v
        }}
      />,
    )
    expect(daysInput()).toHaveValue('3')
    expect(toLeavePayload(latest).lines).toEqual([{ leave_type_id: 1, days: 0 }])

    await user.clear(daysInput())
    await user.type(daysInput(), '4')
    await user.tab()
    expect(toLeavePayload(latest).lines).toEqual([{ leave_type_id: 1, days: 4 }])
  })
})

