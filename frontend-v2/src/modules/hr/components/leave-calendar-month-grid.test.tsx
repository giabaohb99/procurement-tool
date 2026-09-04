import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { LeaveCalendarMonthGrid } from './leave-calendar-month-grid'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type Holiday, type LeaveRequest } from '../types/leave'

/**
 * Lưới tháng của Lịch nghỉ.
 *
 * Chốt hai thứ dễ vỡ âm thầm: **luôn 42 ô** (lưới không nhảy cao thấp khi đổi
 * tháng) và **cắt ở ba mục** (một ngày cả phòng nghỉ không được phá lưới).
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
    from_date: '2026-12-14',
    to_date: '2026-12-15',
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

function renderGrid(
  requestsOn: (iso: string) => LeaveRequest[],
  holidays: Holiday[] = [],
  anchor = new Date(2026, 11, 1),
  onPickDay: (d: Date) => void = () => {},
) {
  return render(
    <MemoryRouter>
      <LeaveCalendarMonthGrid
        anchor={anchor}
        requestsOn={requestsOn}
        holidays={holidays}
        todayISO="2026-12-14"
        onPickDay={onPickDay}
      />
    </MemoryRouter>,
  )
}

describe('LeaveCalendarMonthGrid', () => {
  it('vẽ đủ bảy nhãn thứ, bắt đầu từ T2', () => {
    renderGrid(() => [])
    expect(screen.getByText('T2')).toBeInTheDocument()
    expect(screen.getByText('CN')).toBeInTheDocument()
  })

  it('hiện người nghỉ ở ĐÚNG ngày, và link trỏ về tờ đơn', () => {
    renderGrid((iso) => (iso === '2026-12-14' ? [request()] : []))
    const link = screen.getByRole('link', { name: /Lê Thị C/ })
    expect(link).toHaveAttribute('href', '/hr/leave-requests/1')
  })

  it('quá BA người thì gộp phần dư thành nút "+N người nữa"', () => {
    //  Không cắt thì một ngày cả phòng nghỉ sẽ đẩy ô cao vọt và phá lưới 6 hàng.
    const many = Array.from({ length: 7 }, (_, i) =>
      request({ id: i + 1, employee_name: `Người ${i + 1}` }),
    )
    renderGrid((iso) => (iso === '2026-12-14' ? many : []))

    expect(screen.getAllByRole('link')).toHaveLength(3)
    expect(screen.getByRole('button', { name: '+4 người nữa' })).toBeInTheDocument()
  })

  it('"+N người nữa" BẤM ĐƯỢC và mở đúng ngày đó', () => {
    //  Cắt bớt mà không chừa đường xem tiếp thì màn hình biết có 7 người nghỉ
    //  nhưng người dùng không bao giờ đọc được tên bốn người còn lại.
    const picked: Date[] = []
    const many = Array.from({ length: 7 }, (_, i) => request({ id: i + 1 }))
    renderGrid((iso) => (iso === '2026-12-14' ? many : []), [], undefined, (d) => picked.push(d))

    screen.getByRole('button', { name: '+4 người nữa' }).click()
    expect(picked).toHaveLength(1)
    expect(picked[0].getDate()).toBe(14)
    expect(picked[0].getMonth()).toBe(11)
  })

  it('bấm SỐ NGÀY cũng mở chế độ ngày', () => {
    const picked: Date[] = []
    renderGrid(() => [], [], undefined, (d) => picked.push(d))

    screen.getByRole('button', { name: '25' }).click()
    expect(picked[0].getDate()).toBe(25)
  })

  it('đúng ba người thì KHÔNG hiện dòng "+0 nữa"', () => {
    const three = Array.from({ length: 3 }, (_, i) =>
      request({ id: i + 1, employee_name: `Người ${i + 1}` }),
    )
    renderGrid((iso) => (iso === '2026-12-14' ? three : []))

    expect(screen.getAllByRole('link')).toHaveLength(3)
    expect(screen.queryByText(/nữa/)).not.toBeInTheDocument()
  })

  it('tên ngày lễ hiện trên ô của nó', () => {
    const holiday: Holiday = {
      id: 1,
      company_id: 0,
      date: '2026-12-25',
      name: 'Nghỉ bù cuối năm',
      is_recurring: false,
      is_active: true,
    }
    renderGrid(() => [], [holiday])
    expect(screen.getByText('Nghỉ bù cuối năm')).toBeInTheDocument()
  })

  it('ô của ngày NGOÀI tháng vẫn vẽ, chỉ mờ đi', () => {
    //  Bỏ trắng thì người xem tưởng dữ liệu chưa nạp xong. Tháng 12/2026 bắt
    //  đầu Thứ Ba nên ô đầu là 30/11 — và 30/12 cũng có, nên có ĐÚNG hai ô "30".
    //  Chính chỗ đó là thứ cần phân biệt: một ô mờ, một ô không.
    const { container } = renderGrid(() => [])
    const cells = [...(container.querySelector('.grid-rows-6')?.children ?? [])]

    const ngoaiThang = cells[0]
    expect(ngoaiThang.textContent).toContain('30')
    expect(ngoaiThang.className).toContain('text-muted-foreground/60')

    //  Ô 30/12 nằm trong tháng nên KHÔNG mờ. 30/11 là ô 0, nên 30/12 là ô 30.
    const trongThang = cells[30]
    expect(trongThang.textContent).toContain('30')
    expect(trongThang.className).not.toContain('text-muted-foreground/60')
  })

  it('lưới LUÔN 42 ô dù tháng chỉ cần bốn tuần', () => {
    //  Đếm gián tiếp qua số ngày duy nhất: tháng 2/2027 bắt đầu đúng Thứ Hai và
    //  có 28 ngày, nhưng lưới vẫn phải đủ 6 hàng để không nhảy cao thấp.
    const { container } = renderGrid(() => [], [], new Date(2027, 1, 1))
    const grid = container.querySelector('.grid-rows-6')
    expect(grid?.children).toHaveLength(42)
  })
})
