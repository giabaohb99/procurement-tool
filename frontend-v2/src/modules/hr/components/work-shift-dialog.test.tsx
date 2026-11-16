import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import type { WorkRosterItem } from '../types/work-roster'
import { ROSTER_DAYS, rosterCell, rosterItem, rosterLeave } from './work-roster-fixture'

/*  Hộp xếp ca (bản đại ca chốt 16/11/2026 — danh sách khung "Từ → Đến"): điền sẵn từ mẫu tuần (kèm nghỉ trưa), gửi
    đúng khung giờ, chặn lưu khi khung sai, mẫu nhanh, khóa ô theo luật (chính mình · ngày qua · có đơn nghỉ), và bày
    danh sách ô bị từ chối của lượt áp hàng loạt thành câu đọc được. */

const apiGet = vi.fn()
const apiPut = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()
const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: (...a: unknown[]) => confirmMock(...a) }))
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPut: (...a: unknown[]) => apiPut(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiDelete: (...a: unknown[]) => apiDelete(...a),
}))

const { WorkShiftDialog } = await import('./work-shift-dialog')

const IT = { id: 4, name: 'IT' }
const SELF = 1
const TODAY = '2026-10-06'
const OFFICE_TEMPLATE = {
  schedule_id: 3,
  schedule_name: 'Hành chính',
  weekly_workdays: 5,
  is_fallback: false,
  level: 4,
  days: [0, 1, 2, 3, 4, 5, 6].map((weekday) => ({
    weekday,
    day_kind: weekday < 5 ? 2 : 1,
    start_time: weekday < 5 ? '08:00' : null,
    end_time: weekday < 5 ? '17:00' : null,
    lunch_start: weekday < 5 ? '12:00' : null,
    lunch_end: weekday < 5 ? '13:00' : null,
  })),
}

function user(permissions: AuthUser['permissions']): AuthUser {
  return { id: 9, email: 'a@b.com', full_name: 'Trưởng phòng', employee_id: SELF, department_id: 4, permissions }
}

function staff(id: number, name: string, over: Parameters<typeof rosterCell>[1] = {}): WorkRosterItem {
  return rosterItem(id, name, IT, ROSTER_DAYS.map((d) => rosterCell(d.date, over)))
}

function renderDialog(item: WorkRosterItem, date: string, items: WorkRosterItem[] = [item]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  const { unmount } = render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <WorkShiftDialog target={{ item, date }} onClose={onClose} days={ROSTER_DAYS} items={items} todayISO={TODAY} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { onClose, unmount }
}

beforeEach(() => {
  ;[apiGet, apiPut, apiPost, apiDelete, confirmMock].forEach((m) => m.mockReset())
  apiGet.mockResolvedValue(OFFICE_TEMPLATE)
})

describe('WorkShiftDialog', () => {
  const hrUser = () => user({ work_schedule: { read: true, write: true, delete: true } })
  const managerUser = () => user({ work_schedule_personal: { read: true, write: true, delete: true } })
  //  Ô chọn giờ là Select của shadcn (Radix): ô hiện nhãn "08:00", chọn bằng cách mở danh sách rồi bấm mục.
  const startOf = (n: number) => screen.getByRole('combobox', { name: `Khung ${n} — từ giờ` })
  const endOf = (n: number) => screen.getByRole('combobox', { name: `Khung ${n} — đến giờ` })
  const hourOf = (el: HTMLElement) => Number(el.textContent?.slice(0, 2))
  async function pick(trigger: HTMLElement, label: string) {
    const user = userEvent.setup()
    await user.click(trigger)
    await user.click(await screen.findByRole('option', { name: label }))
  }
  /** Mở danh sách của ô, trả nhãn các mục, rồi đóng lại bằng Esc. */
  async function optionsOf(trigger: HTMLElement) {
    const user = userEvent.setup()
    await user.click(trigger)
    const names = (await screen.findAllByRole('option')).map((o) => o.textContent)
    await user.keyboard('{Escape}')
    return names
  }

  it('HR: prefills the weekly template as two rows around lunch and saves exactly those segments', async () => {
    useAuthStore.setState({ user: hrUser() })
    apiPut.mockResolvedValue({})
    const { onClose } = renderDialog(staff(5, 'An'), '2026-10-05')

    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    expect(hourOf(startOf(1))).toBe(8)
    expect(hourOf(endOf(1))).toBe(12)
    expect(hourOf(endOf(2))).toBe(17)
    //  Tóm tắt ngay cạnh tiêu đề mục.
    expect(screen.getByText('8 giờ')).toBeInTheDocument()
    expect(screen.getByText('1 ngày công')).toBeInTheDocument()
    //  Đầu hộp căn trái: tên, thứ + ngày đầy đủ, nhãn trạng thái của ô.
    expect(screen.getByRole('dialog', { name: 'An' })).toBeInTheDocument()
    expect(screen.getByText('Thứ Hai, 05/10/2026')).toBeInTheDocument()
    expect(screen.getByText('Theo mẫu tuần')).toBeInTheDocument()
    //  Nhãn giờ đủ HH:MM, 24 giờ; thanh ngày ghi SỐ khung.
    expect(startOf(1)).toHaveTextContent('08:00')
    expect(await optionsOf(startOf(1))).toContain('08:00')
    expect(await optionsOf(endOf(2))).toContain('24:00')
    expect(screen.getByLabelText('Khung 2: 13:00 – 17:00')).toHaveTextContent('2')

    //  Ô chưa có ca: chưa sửa gì thì không lưu được (bấm nhầm Lưu sẽ biến mẫu tuần thành ca riêng) — kèm lý do.
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeDisabled()
    expect(screen.getByText('Chưa thay đổi gì')).toBeInTheDocument()
    fireEvent.change(screen.getByRole('textbox', { name: 'Ghi chú' }), { target: { value: 'Livestream' } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(apiPut).toHaveBeenCalledWith('/api/work-shifts/5/2026-10-05', {
      segments: [
        { start_hour: 8, end_hour: 12 },
        { start_hour: 13, end_hour: 17 },
      ],
      note: 'Livestream',
    })
  })

  it('keeps a skeleton while the template loads (rows do not jump) and says so when it fails, without guessing 08–17', async () => {
    useAuthStore.setState({ user: hrUser() })
    let fail: (e: unknown) => void = () => {}
    apiGet.mockReturnValue(new Promise((_, reject) => (fail = reject)))
    renderDialog(staff(5, 'An'), '2026-10-05')
    expect(screen.getByLabelText('Đang đọc mẫu lịch tuần')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Khung 1 — từ giờ' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeDisabled()
    expect(screen.getByText('Đang tải lịch tuần…')).toBeInTheDocument()
    fail(new Error('404'))
    expect(await screen.findByText(/Không đọc được mẫu lịch tuần của ngày này/)).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Khung 1 — từ giờ' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Theo lịch tuần' })).toBeDisabled()
  })

  it('"Đến" only offers hours after "Từ", and moving "Từ" past "Đến" pushes it along', async () => {
    useAuthStore.setState({ user: hrUser() })
    renderDialog(staff(5, 'An'), '2026-10-05')
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    const ends = await optionsOf(endOf(1))
    expect(ends).not.toContain('08:00')
    expect(ends[0]).toBe('09:00')
    await pick(startOf(1), '14:00')
    expect(hourOf(endOf(1))).toBe(18)
  })

  it('an overlap is explained on the row and blocks saving; rows are sorted only when saved', async () => {
    useAuthStore.setState({ user: hrUser() })
    apiPut.mockResolvedValue({})
    renderDialog(staff(5, 'An'), '2026-10-05')
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    await pick(startOf(2), '10:00')
    expect(screen.getAllByText('Trùng giờ với khung 1.').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeDisabled()
    expect(screen.getByText('Còn khung giờ bị lỗi')).toBeInTheDocument()
    //  Đang trùng giờ: tổng là số tạm nên ghi "— giờ", không ghi 9 giờ.
    expect(screen.getByText('— giờ')).toBeInTheDocument()

    //  Sửa cho hết trùng: khung 2 dời lên 20:00–23:00, rồi thêm một khung 1 tiếng ngay sau.
    await pick(startOf(2), '20:00')
    await pick(endOf(2), '23:00')
    expect(screen.getByText('7 giờ')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Thêm khung giờ/ }))
    expect(hourOf(startOf(3))).toBe(23)
    await pick(startOf(3), '06:00')
    //  Đến 24:00 vẫn sau 06:00 nên được giữ — khung 06–24 trùng hai khung kia, phải sửa Đến.
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeDisabled()
    await pick(endOf(3), '07:00')
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() =>
      expect(apiPut).toHaveBeenCalledWith('/api/work-shifts/5/2026-10-05', {
        segments: [
          { start_hour: 6, end_hour: 7 },
          { start_hour: 8, end_hour: 12 },
          { start_hour: 20, end_hour: 23 },
        ],
        note: '',
      }),
    )
  })

  it('presets: "Nghỉ cả ngày" empties the list, "Hành chính 08–17" refills it', async () => {
    useAuthStore.setState({ user: hrUser() })
    renderDialog(staff(5, 'An'), '2026-10-05')
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    fireEvent.click(screen.getByRole('button', { name: 'Nghỉ cả ngày' }))
    expect(screen.queryByRole('combobox', { name: 'Khung 1 — từ giờ' })).toBeNull()
    expect(screen.getByText('không tính công')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Hành chính 08–17' }))
    expect(hourOf(startOf(1))).toBe(8)
    expect(hourOf(endOf(2))).toBe(17)
  })

  it('double click on Lưu sends ONE request (ref guard, not just disabled)', async () => {
    useAuthStore.setState({ user: hrUser() })
    let resolve: (v: unknown) => void = () => {}
    apiPut.mockReturnValue(new Promise((r) => (resolve = r)))
    renderDialog(staff(5, 'An'), '2026-10-05')
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    fireEvent.click(screen.getByRole('button', { name: 'Hành chính 08–17' }))
    const save = screen.getByRole('button', { name: 'Lưu' })
    fireEvent.click(save)
    fireEvent.click(save)
    fireEvent.click(save)
    resolve({})
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
  })

  it('an existing shift opens with its own rows and note; deleting every row saves a day off', async () => {
    useAuthStore.setState({ user: hrUser() })
    apiPut.mockResolvedValue({})
    const shiftItem = staff(5, 'An', {
      is_shift: true,
      shift: { segments: ['19:00–23:00'], ranges: [[19, 23]], hours: 4, note: 'Livestream', is_day_off: false },
    })
    renderDialog(shiftItem, '2026-10-05')
    expect(hourOf(startOf(1))).toBe(19)
    expect(screen.getByDisplayValue('Livestream')).toBeInTheDocument()
    expect(screen.getByText('Ca xếp riêng')).toBeInTheDocument()
    //  05/10 đã qua (hôm nay 06/10): HR cũng không về mẫu tuần được — nút tắt kèm lý do (backend 422).
    expect(screen.getByRole('button', { name: 'Về mẫu tuần' })).toBeDisabled()
    expect(screen.getByText(/Ngày đã qua \(hoặc hôm nay\) không về mẫu tuần được/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Xóa khung 1' }))
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledWith('/api/work-shifts/5/2026-10-05', { segments: [], note: 'Livestream' }))
  })

  it('"Về mẫu tuần": off today, on for a future day with an existing shift; confirmed reset sends DELETE', async () => {
    useAuthStore.setState({ user: hrUser() })
    apiDelete.mockResolvedValue({ deleted: true })
    const shift = { is_shift: true, shift: { segments: ['19:00–23:00'], ranges: [[19, 23]], hours: 4, note: '', is_day_off: false } }
    const { unmount } = renderDialog(staff(5, 'An', shift), TODAY)
    expect(screen.getByRole('button', { name: 'Về mẫu tuần' })).toBeDisabled()
    unmount()

    renderDialog(staff(5, 'An', shift), '2026-10-11')
    const reset = screen.getByRole('button', { name: 'Về mẫu tuần' })
    expect(reset).toBeEnabled()
    expect(screen.queryByText(/không về mẫu tuần được/)).toBeNull()
  })

  it('a cell held by a leave the viewer cannot read (leave_hold only) is locked too', () => {
    useAuthStore.setState({ user: hrUser() })
    renderDialog(staff(5, 'An', { leave_hold: true }), '2026-10-11')
    expect(screen.getByText('Đã có đơn nghỉ — sửa đơn trước.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
  })

  it('a second click on "Về mẫu tuần" while the confirm is open does not ask twice', async () => {
    useAuthStore.setState({ user: hrUser() })
    confirmMock.mockReturnValue(new Promise(() => {}))
    const shift = { is_shift: true, shift: { segments: ['19:00–23:00'], ranges: [[19, 23]], hours: 4, note: '', is_day_off: false } }
    renderDialog(staff(5, 'An', shift), '2026-10-11')
    const reset = screen.getByRole('button', { name: 'Về mẫu tuần' })
    fireEvent.click(reset)
    fireEvent.click(reset)
    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    expect(apiDelete).not.toHaveBeenCalled()
  })

  it('apply to other days: own leave day not pickable, a colleague with leave is flagged and blocks Áp with a warning', async () => {
    useAuthStore.setState({ user: hrUser() })
    const an = rosterItem(5, 'An', IT, ROSTER_DAYS.map((d) => rosterCell(d.date, d.date === '2026-10-11' ? { leave_hold: true } : {})))
    const binh = rosterItem(6, 'Bình', IT, ROSTER_DAYS.map((d) => rosterCell(d.date, d.date === '2026-10-06' ? { leave: rosterLeave() } : {})))
    renderDialog(an, '2026-10-06', [an, binh])
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))
    fireEvent.click(screen.getByRole('button', { name: /Áp cùng ca cho ngày \/ người khác/ }))
    expect(screen.getByRole('button', { name: /11\/10/ })).toBeDisabled()
    expect(screen.getByText('Có đơn nghỉ')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('checkbox'))
    expect(screen.getByText('Thêm 1 người → tổng 2 ô')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('1 ô đã có đơn nghỉ — bỏ chọn người / ngày đó rồi mới áp được.')
    expect(screen.getByRole('button', { name: 'Lưu cho 2 ô' })).toBeDisabled()
    expect(screen.getByText('Có ô không áp được — xem cảnh báo ở trên')).toBeInTheDocument()
  })

  it('on a phone the dialog is a bottom sheet with the same content', () => {
    useAuthStore.setState({ user: hrUser() })
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    try {
      renderDialog(staff(SELF, 'Chính tôi'), '2026-10-11')
      expect(document.querySelector('[data-slot="sheet-content"]')).not.toBeNull()
      expect(screen.getByRole('dialog', { name: 'Chính tôi' })).toBeInTheDocument()
    } finally {
      vi.unstubAllGlobals()
    }
  })

  it('manager: a past day is read-only with the reason, no save button', async () => {
    useAuthStore.setState({ user: managerUser() })
    renderDialog(staff(5, 'An'), '2026-10-05')
    expect(screen.getByText(/Ngày đã qua: Trưởng phòng chỉ xếp ca từ hôm nay trở đi/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
    //  Chỉ xem: chữ thường (copy được), không phải ô chọn bị tắt.
    expect(screen.queryByRole('combobox')).toBeNull()
    expect(await screen.findByText('08:00 – 12:00')).toBeInTheDocument()
    //  Đóng không được tự nhận con trỏ lúc mở (đại ca chê vòng xanh quanh nút).
    expect(screen.getByRole('button', { name: 'Đóng' })).not.toHaveFocus()
  })

  it('own row is read-only for everyone, HR included', () => {
    useAuthStore.setState({ user: hrUser() })
    renderDialog(staff(SELF, 'Chính tôi'), '2026-10-11')
    expect(screen.getByText(/Bạn không tự xếp ca cho mình/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
  })

  it('a day with a leave request is locked with a link to the request', () => {
    useAuthStore.setState({ user: hrUser() })
    renderDialog(staff(5, 'An', { leave: rosterLeave({ request_id: 77, code: 'NP077' }) }), '2026-10-11')
    expect(screen.getByText('Đã có đơn nghỉ — sửa đơn trước.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /xem đơn/ })).toHaveAttribute('href', '/hr/leave-requests/77')
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
  })

  it('manager bulk apply: past days cannot be picked, self is not offered, rejections are listed by name and date', async () => {
    useAuthStore.setState({ user: managerUser() })
    apiPost.mockRejectedValue({
      response: {
        status: 409,
        data: {
          success: false,
          error: {
            code: 'shift_rejected',
            message: 'Không xếp được 1 ô',
            details: {
              rejected: [{ employee_id: 6, work_date: '2026-10-11', code: 'leave_conflict', message: 'Ngày 11/10 đã có đơn nghỉ NP012 (Phép năm) — sửa / hủy đơn trước rồi xếp ca.' }],
            },
          },
        },
      },
    })
    const an = staff(5, 'An')
    const binh = staff(6, 'Bình')
    const me = staff(SELF, 'Chính tôi')
    renderDialog(an, '2026-10-06', [an, binh, me])
    await waitFor(() => expect(hourOf(startOf(2))).toBe(13))

    //  Nút chính: "Lưu" khi chỉ ô này, "Lưu cho N ô" khi chọn thêm — kể cả khi mục đã gập lại.
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Áp cùng ca cho ngày \/ người khác/ }))
    //  05/10 đã qua (hôm nay 06/10) → không chọn được; 11/10 chọn được.
    expect(screen.getByRole('button', { name: /5\/10/ })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: /11\/10/ }))
    expect(screen.queryByText('Chính tôi')).toBeNull()
    fireEvent.click(screen.getByRole('checkbox'))
    expect(screen.getByText('Thêm 1 ngày · 1 người → tổng 4 ô')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Áp cùng ca cho ngày \/ người khác/ }))
    expect(screen.getByText('Thêm 1 ngày · 1 người → tổng 4 ô')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Lưu cho 4 ô' }))
    await screen.findByText('Không ô nào được lưu — 1 ô bị từ chối:')
    expect(screen.getByText('Bình · 11/10/2026: Ngày 11/10 đã có đơn nghỉ NP012 (Phép năm) — sửa / hủy đơn trước rồi xếp ca.')).toBeInTheDocument()
    expect(apiPost).toHaveBeenCalledWith(
      '/api/work-shifts/bulk',
      {
        employee_ids: [5, 6],
        dates: ['2026-10-06', '2026-10-11'],
        segments: [
          { start_hour: 8, end_hour: 12 },
          { start_hour: 13, end_hour: 17 },
        ],
        note: '',
      },
      expect.anything(),
    )
  })
})
