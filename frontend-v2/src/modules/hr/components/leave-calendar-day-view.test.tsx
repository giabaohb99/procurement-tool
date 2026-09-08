import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { LeaveCalendarDayView } from './leave-calendar-day-view'
import {
  LEAVE_SESSION,
  LEAVE_STATUS,
  LEAVE_UNIT,
  type Holiday,
  type LeaveRequest,
} from '../types/leave'

/**
 * Chế độ NGÀY của Lịch nghỉ.
 *
 * Đây là màn hứng phần dư của lưới tháng và lưới tuần ("+9 người nữa" bấm vào
 * là tới đây), nên nó phải chịu được ngày cả phòng nghỉ chung — và lúc đó bộ
 * lọc mới là thứ dùng tới.
 */
const DAY = '2027-03-16'

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    employee_name: 'Lê Văn Nhân Sự Ba',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2027-03-15',
    to_date: DAY,
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

function renderDay(items: LeaveRequest[], holidays: Holiday[] = []) {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại, nên phải có provider —
  //  màn này không tự gọi API nào, cái client dựng ở đây chỉ để nó có chỗ bám.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LeaveCalendarDayView
          anchor={new Date(2027, 2, 16)}
          requestsOn={(iso) => (iso === DAY ? items : [])}
          holidays={holidays}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Số dòng dữ liệu thật — bảng rỗng vẫn dựng một hàng chứa câu thông báo. */
function rowCount() {
  return screen.queryAllByRole('row').filter((r) => r.querySelector('td')).length
}

describe('LeaveCalendarDayView', () => {
  it('không ai nghỉ thì nói rõ, không để bảng trống trơn', () => {
    renderDay([])
    expect(screen.getByText('Không ai nghỉ ngày này.')).toBeInTheDocument()
  })

  it('đếm sẵn đầu người, tách đã duyệt với chờ duyệt', () => {
    //  Chờ duyệt là số người *có thể* vẫn đi làm — người xếp việc cần biết đâu
    //  là chắc chắn, đâu là chưa. Đếm bằng mắt trên mười bốn dòng là đếm sai.
    renderDay([
      request({ id: 1 }),
      request({ id: 2, status: LEAVE_STATUS.PENDING }),
      request({ id: 3, status: LEAVE_STATUS.PENDING }),
    ])

    expect(screen.getByText('3 người nghỉ')).toBeInTheDocument()
    expect(screen.getByText('1 đã duyệt')).toBeInTheDocument()
    expect(screen.getByText('2 chờ duyệt')).toBeInTheDocument()
  })

  it('nói ĐÚNG vị trí trong đợt nghỉ — ngày đầu, ngày cuối, giữa đợt', () => {
    //  Đơn kết thúc chiều nay khác hẳn đơn còn kéo thêm một tuần, mà cả hai đều
    //  "đang nghỉ hôm nay".
    renderDay([
      request({ id: 1, from_date: DAY, to_date: '2027-03-20' }),
      request({ id: 2, from_date: '2027-03-10', to_date: DAY }),
      request({ id: 3, from_date: '2027-03-10', to_date: '2027-03-20' }),
      request({ id: 4, from_date: DAY, to_date: DAY }),
    ])

    expect(screen.getByText('Ngày đầu')).toBeInTheDocument()
    expect(screen.getByText('Ngày cuối')).toBeInTheDocument()
    expect(screen.getByText('Đang giữa đợt')).toBeInTheDocument()
    expect(screen.getByText('Nghỉ một ngày')).toBeInTheDocument()
  })

  it('tìm được theo TÊN, MÃ ĐƠN và LÝ DO — ba thứ người ta nhớ về một tờ đơn', async () => {
    const nguoi = userEvent.setup()
    renderDay([
      request({ id: 1, code: 'NP015', employee_name: 'Phạm Thị Kế Toán', reason: 'Về quê' }),
      request({ id: 2, code: 'NP016', employee_name: 'Trần Trưởng Phòng', reason: 'Khám bệnh' }),
    ])
    const box = screen.getByPlaceholderText(/Tìm theo tên/)

    await nguoi.type(box, 'kế toán')
    expect(rowCount()).toBe(1)

    await nguoi.clear(box)
    await nguoi.type(box, 'NP016')
    expect(rowCount()).toBe(1)
    expect(screen.getByText('Trần Trưởng Phòng')).toBeInTheDocument()

    await nguoi.clear(box)
    await nguoi.type(box, 'khám')
    expect(rowCount()).toBe(1)
  })

  it('tìm không ra ai thì báo KHÁC câu "không ai nghỉ"', async () => {
    //  Hai câu lẫn nhau thì người dùng tưởng cả ngày trống, trong khi thật ra
    //  chỉ là gõ sai một chữ.
    const nguoi = userEvent.setup()
    renderDay([request()])

    await nguoi.type(screen.getByPlaceholderText(/Tìm theo tên/), 'zzzkhongcoai')
    expect(screen.getByText('Không có ai khớp bộ lọc.')).toBeInTheDocument()
    expect(screen.queryByText('Không ai nghỉ ngày này.')).not.toBeInTheDocument()
  })

  it('ô lọc loại nghỉ CHỈ bày loại có mặt trong ngày', async () => {
    //  Nạp cả danh mục thì người dùng chọn được "Nghỉ thai sản" rồi nhận về bảng
    //  rỗng — một bộ lọc chỉ dẫn tới ngõ cụt thì thà đừng có.
    const nguoi = userEvent.setup()
    renderDay([
      request({ id: 1, leave_type_id: 1, leave_type_name: 'Phép năm' }),
      request({ id: 2, leave_type_id: 2, leave_type_name: 'Nghỉ không lương' }),
    ])

    await nguoi.click(screen.getByRole('combobox', { name: 'Lọc theo loại nghỉ' }))
    expect(screen.getByRole('option', { name: 'Phép năm' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Nghỉ không lương' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Nghỉ thai sản' })).not.toBeInTheDocument()
  })

  it('chỉ MỘT loại nghỉ thì ô lọc tự ẨN — một lựa chọn thì lọc được gì', () => {
    //  Ô chọn có đúng một lựa chọn thật không lọc được gì, nó chỉ chiếm chỗ và
    //  mời người ta bấm vào để rồi không thấy gì đổi. Luật "không lặp loại nghỉ"
    //  nằm ở `leaveTypesIn`, có bài kiểm riêng trong `filter-leave-rows.test.ts`.
    renderDay([
      request({ id: 1, leave_type_id: 1, leave_type_name: 'Phép năm' }),
      request({ id: 2, leave_type_id: 1, leave_type_name: 'Phép năm' }),
    ])

    expect(screen.queryByRole('combobox', { name: 'Lọc theo loại nghỉ' })).not.toBeInTheDocument()
    //  Ô lọc trạng thái thì VẪN còn — nó không phụ thuộc dữ liệu.
    expect(screen.getByRole('combobox', { name: 'Lọc theo trạng thái' })).toBeInTheDocument()
  })

  it('ngày lễ thì nói rõ là không tính vào phép', () => {
    const holiday: Holiday = {
      id: 1,
      company_id: 0,
      date: DAY,
      name: 'Giỗ Tổ',
      is_recurring: false,
      is_active: true,
    }
    renderDay([], [holiday])

    expect(screen.getByText('Giỗ Tổ')).toBeInTheDocument()
    expect(screen.getByText(/không tính vào ngày phép/)).toBeInTheDocument()
  })
})
