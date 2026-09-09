import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

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

  it('tràn thì dòng "+N người nữa" CHIẾM CHỖ của một chip, không cộng thêm', () => {
    //  Ô cao ~95px chứa bốn dòng: số ngày + ba chip. Vẽ đủ ba chip RỒI thêm dòng
    //  "+N" là năm dòng — dòng cuối bị đường kẻ ô cắt ngang, mà nó chính là lối
    //  duy nhất đọc tên những người bị giấu.
    const many = Array.from({ length: 7 }, (_, i) =>
      request({ id: i + 1, employee_name: `Người ${i + 1}` }),
    )
    renderGrid((iso) => (iso === '2026-12-14' ? many : []))

    expect(screen.getAllByRole('link')).toHaveLength(2)
    expect(screen.getByRole('button', { name: '+5 người nữa' })).toBeInTheDocument()
  })

  it('ngày lễ cũng ăn một dòng nên bày ít chip hơn', () => {
    //  Tên ngày lễ là chip đầu tiên trong ô (lối Google Calendar). Không trừ nó
    //  ra thì ngày lễ có người nghỉ luôn tràn đúng một dòng.
    const holiday: Holiday = {
      id: 1,
      company_id: 0,
      date: '2026-12-14',
      name: 'Nghỉ bù',
      is_recurring: false,
      is_active: true,
    }
    const many = Array.from({ length: 4 }, (_, i) => request({ id: i + 1 }))
    renderGrid((iso) => (iso === '2026-12-14' ? many : []), [holiday])

    expect(screen.getAllByRole('link')).toHaveLength(1)
    expect(screen.getByRole('button', { name: '+3 người nữa' })).toBeInTheDocument()
  })

  it('"+N người nữa" BẤM ĐƯỢC và mở đúng ngày đó', () => {
    //  Cắt bớt mà không chừa đường xem tiếp thì màn hình biết có 7 người nghỉ
    //  nhưng người dùng không bao giờ đọc được tên năm người còn lại.
    const picked: Date[] = []
    const many = Array.from({ length: 7 }, (_, i) => request({ id: i + 1 }))
    renderGrid((iso) => (iso === '2026-12-14' ? many : []), [], undefined, (d) => picked.push(d))

    screen.getByRole('button', { name: '+5 người nữa' }).click()
    expect(picked).toHaveLength(1)
    expect(picked[0].getDate()).toBe(14)
    expect(picked[0].getMonth()).toBe(11)
  })

  it('ngày 1 kèm TÊN THÁNG — hàng cuối bày 1…11 của tháng sau, chữ mờ thôi chưa đủ', () => {
    renderGrid(() => [])
    expect(screen.getByRole('button', { name: '1 thg 12' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '1 thg 1' })).toBeInTheDocument()
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

/**
 * Khổ điện thoại — ô rộng ~48px nên lưới đổi hẳn hình dạng, xem
 * `LeaveCalendarMonthCellCompact`.
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('LeaveCalendarMonthGrid — khổ điện thoại', () => {
  afterEach(() => vi.unstubAllGlobals())

  function renderMobileGrid(
    requestsOn: (iso: string) => LeaveRequest[],
    holidays: Holiday[] = [],
    onPickDay: (d: Date) => void = () => {},
  ) {
    vi.stubGlobal('matchMedia', (q: string) => ({
      matches: true,
      media: q,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    return renderGrid(requestsOn, holidays, new Date(2026, 11, 1), onPickDay)
  }

  it('KHÔNG kê tên người — ô 48px chỉ cắt được ba ký tự, không nói được ai nghỉ', () => {
    const items = [
      request({ id: 1, employee_name: 'Nguyễn Văn A' }),
      request({ id: 2, employee_name: 'Trần Thị B' }),
    ]
    renderMobileGrid((iso) => (iso === '2026-12-14' ? items : []))

    expect(screen.queryAllByRole('link')).toHaveLength(0)
  })

  it('nói ĐỦ SỐ và tách đã duyệt / chờ duyệt thành lời — hàng chấm là hình, không đọc được', () => {
    //  Ô khổ hẹp chỉ vẽ chấm (lối Google Calendar trên điện thoại). Hai màu là
    //  thứ duy nhất phân biệt "chắc chắn nghỉ" với "có thể nghỉ", mà người dùng
    //  trình đọc màn hình không thấy màu — thiếu câu này là họ mất sạch.
    const items = [
      request({ id: 1, status: LEAVE_STATUS.APPROVED }),
      request({ id: 2, status: LEAVE_STATUS.APPROVED }),
      request({ id: 3, status: LEAVE_STATUS.APPROVED }),
      request({ id: 4, status: LEAVE_STATUS.PENDING }),
    ]
    renderMobileGrid((iso) => (iso === '2026-12-14' ? items : []))

    expect(
      screen.getByRole('button', {
        name: 'Ngày 14/12 — 4 người nghỉ (3 đã duyệt, 1 chờ duyệt)',
      }),
    ).toBeInTheDocument()
  })

  it('CẢ Ô là một nút — ngón tay không nhắm được vào con số 12px', () => {
    const picked: Date[] = []
    renderMobileGrid(() => [], [], (d) => picked.push(d))

    screen.getByRole('button', { name: /Ngày 25\/12/ }).click()
    expect(picked).toHaveLength(1)
    expect(picked[0].getDate()).toBe(25)
  })

  it('MÀN RỘNG nhưng LƯỚI hẹp cũng đổi sang ô đếm — menu trái ăn mất 256px', () => {
    //  Máy 820px với menu trái mở: lưới chỉ còn 530px, ô 75px, tên cắt thành
    //  «Dego …» y hệt trên điện thoại. `matchMedia` ở đây vẫn nói "khổ rộng"
    //  (mặc định của `setup.ts`) — chỉ phép đo bắt được ca này.
    class NarrowResizeObserver {
      constructor(private readonly callback: ResizeObserverCallback) {}
      observe() {
        this.callback(
          [{ contentRect: { width: 530 } } as ResizeObserverEntry],
          this as unknown as ResizeObserver,
        )
      }
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal('ResizeObserver', NarrowResizeObserver)

    renderGrid(
      (iso) => (iso === '2026-12-14' ? [request({ employee_name: 'Nguyễn Văn A' })] : []),
      [],
      new Date(2026, 11, 1),
    )

    expect(screen.queryAllByRole('link')).toHaveLength(0)
    expect(screen.getByRole('button', { name: /Ngày 14\/12 — 1 người nghỉ/ })).toBeInTheDocument()
  })

  it('tên ngày lễ nói được thành LỜI dù ô không còn chỗ hiện chữ', () => {
    //  Ô khổ hẹp chỉ tô nền hồng + một chấm; thiếu tên trong `aria-label` thì
    //  người dùng trình đọc màn hình mất hẳn thông tin ngày lễ.
    const holiday: Holiday = {
      id: 1,
      company_id: 0,
      date: '2026-12-25',
      name: 'Nghỉ bù cuối năm',
      is_recurring: false,
      is_active: true,
    }
    renderMobileGrid(() => [], [holiday])

    expect(
      screen.getByRole('button', { name: /Ngày 25\/12 — Nghỉ bù cuối năm/ }),
    ).toBeInTheDocument()
  })
})
