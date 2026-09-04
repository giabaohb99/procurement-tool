import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { LeaveCalendarWeekGrid } from './leave-calendar-week-grid'
import {
  LEAVE_SESSION,
  LEAVE_STATUS,
  LEAVE_UNIT,
  type Holiday,
  type LeaveRequest,
} from '../types/leave'

/**
 * Lưới TUẦN — mỗi ngày một hàng ngang.
 *
 * Chốt hai thứ: **cắt ở sáu người** (một ngày cả phòng nghỉ không được nuốt cả
 * màn hình và đẩy sáu ngày còn lại khỏi tầm nhìn) và **phần dư bấm được** (cắt
 * mà không chừa đường xem tiếp thì tên những người còn lại mất luôn).
 */
function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    employee_name: 'Lê Thị C',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2027-03-15',
    to_date: '2027-03-16',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 2,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.APPROVED,
    approval_instance_id: 0,
    document_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

function renderWeek(
  requestsOn: (iso: string) => LeaveRequest[],
  holidays: Holiday[] = [],
  onPickDay: (d: Date) => void = () => {},
) {
  return render(
    <MemoryRouter>
      <LeaveCalendarWeekGrid
        anchor={new Date(2027, 2, 15)}
        requestsOn={requestsOn}
        holidays={holidays}
        todayISO="2027-03-15"
        onPickDay={onPickDay}
      />
    </MemoryRouter>,
  )
}

const many = (count: number) =>
  Array.from({ length: count }, (_, i) => request({ id: i + 1, employee_name: `Người ${i + 1}` }))

describe('LeaveCalendarWeekGrid', () => {
  it('vẽ đủ bảy ngày của tuần', () => {
    renderWeek(() => [])
    expect(screen.getByText('T2')).toBeInTheDocument()
    expect(screen.getByText('CN')).toBeInTheDocument()
  })

  it('cả tuần không ai nghỉ thì nói MỘT LẦN, không lặp bảy dòng giống nhau', () => {
    //  Bảy dòng "không ai nghỉ" nối nhau đọc như màn hình hỏng.
    renderWeek(() => [])
    expect(screen.getByText('Cả tuần này không ai nghỉ.')).toBeInTheDocument()
  })

  it('có người nghỉ thì KHÔNG hiện câu "cả tuần không ai nghỉ"', () => {
    renderWeek((iso) => (iso === '2027-03-15' ? [request()] : []))
    expect(screen.queryByText('Cả tuần này không ai nghỉ.')).not.toBeInTheDocument()
  })

  it('cắt ở SÁU người và gộp phần dư thành nút', () => {
    //  Không cắt thì hàng đó tự dâng lên nuốt hết màn hình, và sáu ngày còn lại
    //  bị đẩy khỏi tầm nhìn — đúng cái tuần bận nhất lại là tuần không xem được.
    renderWeek((iso) => (iso === '2027-03-15' ? many(14) : []))

    expect(screen.getAllByRole('link')).toHaveLength(6)
    expect(screen.getByRole('button', { name: '+8 người nữa' })).toBeInTheDocument()
  })

  it('đúng sáu người thì KHÔNG hiện nút "+0"', () => {
    renderWeek((iso) => (iso === '2027-03-15' ? many(6) : []))
    expect(screen.getAllByRole('link')).toHaveLength(6)
    expect(screen.queryByText(/người nữa/)).not.toBeInTheDocument()
  })

  it('bấm "+N người nữa" mở ĐÚNG ngày của hàng đó', () => {
    const onPick = vi.fn()
    renderWeek((iso) => (iso === '2027-03-15' ? many(14) : []), [], onPick)

    screen.getByRole('button', { name: '+8 người nữa' }).click()
    expect(onPick).toHaveBeenCalledTimes(1)
    expect(onPick.mock.calls[0][0].getDate()).toBe(15)
  })

  it('bấm NHÃN NGÀY cũng mở chế độ ngày', () => {
    const onPick = vi.fn()
    renderWeek(() => [], [], onPick)

    //  Nhãn gồm thứ và ngày; khớp theo thứ là đủ vì mỗi tuần chỉ một T4.
    screen.getByRole('button', { name: /T4/ }).click()
    expect(onPick.mock.calls[0][0].getDate()).toBe(17)
  })

  it('đếm đầu người ở cuối hàng, không bắt tự đếm chip', () => {
    renderWeek((iso) => (iso === '2027-03-15' ? many(14) : []))
    expect(screen.getByText('14 người')).toBeInTheDocument()
  })

  it('ngày lễ mà KHÔNG ai nghỉ thì chỉ hiện thẻ lễ, không kèm "không ai nghỉ"', () => {
    //  Thẻ ngày lễ đã nói đủ; thêm câu kia là hai thông tin chồng nhau.
    const holiday: Holiday = {
      id: 1,
      company_id: 0,
      date: '2027-03-17',
      name: 'Nghỉ bù',
      is_recurring: false,
      is_active: true,
    }
    renderWeek(() => [], [holiday])

    expect(screen.getByText('Nghỉ bù')).toBeInTheDocument()
    //  Sáu ngày còn lại vẫn ghi "Không ai nghỉ", riêng ngày lễ thì không.
    expect(screen.getAllByText('Không ai nghỉ')).toHaveLength(6)
  })
})
