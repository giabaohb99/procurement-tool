import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DocumentDashboardFilters } from './document-dashboard-filters'

const COMPANIES = [
  { id: 1, name: 'DEGO HOLDING', code: 'DEGO', is_active: true },
  { id: 12, name: 'SAM', code: 'SAM', is_active: true },
]

//  Danh sách phòng ban "toàn bộ" — dùng khi CHƯA chọn pháp nhân nào.
const ALL_DEPARTMENTS = [
  { id: 4, name: 'Phòng Kế toán', company_id: 1, is_active: true },
  { id: 10, name: 'Phòng CNTT', company_id: 1, is_active: true },
]

//  Cặp (phòng × pháp nhân) do backend trả — nguồn ĐÚNG khi đã chọn pháp nhân.
let capTheoPhapNhan: { department_id: number; department_name: string }[] = []

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: COMPANIES, total: COMPANIES.length } }),
}))

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: ALL_DEPARTMENTS, total: ALL_DEPARTMENTS.length } }),
  useDepartmentsByCompanies: () => ({ data: capTheoPhapNhan }),
}))

function dung(props: Partial<Parameters<typeof DocumentDashboardFilters>[0]> = {}) {
  const onChange = vi.fn()
  render(
    <DocumentDashboardFilters
      rangeKey="all"
      onChange={onChange}
      {...props}
    />,
  )
  return onChange
}

/** Mở ô chọn phòng ban (ô thứ hai trên thanh lọc). */
async function openDepartmentSelect(nguoi: ReturnType<typeof userEvent.setup>) {
  await nguoi.click(screen.getAllByRole('combobox')[1])
}

beforeEach(() => {
  capTheoPhapNhan = []
})

describe('DocumentDashboardFilters', () => {
  it('chưa chọn pháp nhân thì hiện toàn bộ phòng ban', async () => {
    const nguoi = userEvent.setup()
    dung()
    await openDepartmentSelect(nguoi)

    expect(screen.getByText('Phòng Kế toán')).toBeInTheDocument()
    expect(screen.getByText('Phòng CNTT')).toBeInTheDocument()
  })

  it('chọn pháp nhân rồi thì lấy phòng ban từ BACKEND, không lọc ở client', async () => {
    //  Một phòng có mặt ở NHIỀU pháp nhân (`tab_department_company`), còn
    //  `Department.company_id` chỉ là pháp nhân GỐC. Lọc theo mình nó ở client
    //  thì phòng phục vụ pháp nhân khác biến mất khỏi ô chọn.
    capTheoPhapNhan = [{ department_id: 99, department_name: 'Phòng dùng chung' }]
    const nguoi = userEvent.setup()
    dung({ companyId: 12 })
    await openDepartmentSelect(nguoi)

    expect(screen.getByText('Phòng dùng chung')).toBeInTheDocument()
    //  Phòng có `company_id = 1` không được lọt vào khi đang xem pháp nhân 12.
    expect(screen.queryByText('Phòng Kế toán')).not.toBeInTheDocument()
  })

  it('pháp nhân chưa khai phòng ban nào thì NÓI RÕ, không bung ra ô rỗng', async () => {
    //  Lỗi khách báo 25/08/2026: chọn pháp nhân xong ô phòng ban trống trơn,
    //  không câu nào giải thích. Dữ liệu thật: 13 pháp nhân, phòng ban mới khai
    //  cho 2 — nên đây là chuyện gặp thường xuyên chứ không phải ca hiếm.
    capTheoPhapNhan = []
    const nguoi = userEvent.setup()
    dung({ companyId: 12 })
    await openDepartmentSelect(nguoi)

    expect(screen.getByText(/chưa khai phòng ban nào/i)).toBeInTheDocument()
  })

  it('chưa chọn pháp nhân thì KHÔNG hiện câu «chưa khai»', async () => {
    const nguoi = userEvent.setup()
    dung()
    await openDepartmentSelect(nguoi)

    expect(screen.queryByText(/chưa khai phòng ban nào/i)).not.toBeInTheDocument()
  })

  it('ô khoảng ngày chỉ hiện khi chọn mức «Khoảng ngày…»', () => {
    //  Bày sẵn một ô lịch cạnh ô mức thời gian là hai thứ cùng trả lời một câu,
    //  người dùng phải đoán cái nào đang ăn.
    dung({ rangeKey: 'all' })
    expect(screen.queryByText(/Chọn khoảng ngày/)).not.toBeInTheDocument()
  })

  it('chọn mức «Khoảng ngày…» thì hiện ô lịch', () => {
    dung({ rangeKey: 'custom' })
    expect(screen.getByText(/Chọn khoảng ngày/)).toBeInTheDocument()
  })

  it('đã có khoảng thì hiện dd/mm/yyyy, không phải chuỗi ISO', () => {
    //  CÓ số 0 ở đầu. Bài này trước đây chốt `11/9/2026` — chính là đầu ra của
    //  `toLocaleDateString('vi-VN')` trần, lệch hẳn với `formatDate` mà cả hệ
    //  đang dùng, nên nó đang khóa cái sai lại chứ không canh cái đúng.
    dung({ rangeKey: 'custom', fromDate: '2026-09-11', toDate: '2026-09-14' })
    expect(screen.getByText('11/09/2026 – 14/09/2026')).toBeInTheDocument()
  })
})
