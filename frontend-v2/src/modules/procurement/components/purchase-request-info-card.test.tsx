import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { Company } from '@/modules/hr/types/company'
import type { Employee } from '@/modules/hr/types/employee'
import type {
  DeptHeadCandidate,
  PurchaseRequestDetail,
} from '../types/purchase-request-detail'
import { PurchaseRequestInfoCard } from './purchase-request-info-card'

/**
 * Đại ca than 24/09/2026: ô chọn dài trên YCMH (Nhân sự YC, Công ty, TBP…) là Radix
 * Select không tìm được, danh sách nhân sự cả trăm người phải cuộn tay. Nay các ô đó
 * là `SearchSelect` gõ thẳng trên ô — mấy bài dưới giữ cho nó KHÔNG quay lại kiểu cũ,
 * và giữ nguyên hành vi của bản Radix (chọn lại đúng người thì không bắn sự kiện).
 */

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
}))

const EMPLOYEES = [
  {
    id: 1,
    code: 'NV001',
    full_name: 'Nguyễn Văn An',
    position: 'Kỹ sư',
    company_id: 10,
    department_id: 3,
    department_name: 'Phòng Kỹ thuật',
    manager_name: 'Lê Văn Trưởng',
  },
  {
    id: 2,
    code: 'NV002',
    full_name: 'Trần Thị Lan',
    position: 'Kế toán',
    company_id: 10,
    department_id: 4,
    department_name: 'Phòng Kế toán',
    manager_name: 'Phạm Thị Hoa',
  },
  {
    id: 3,
    code: 'NV003',
    full_name: 'Lê Minh Tuấn',
    position: '',
    company_id: 10,
    department_id: 3,
    department_name: 'Phòng Kỹ thuật',
    manager_name: 'Lê Văn Trưởng',
  },
] as Employee[]

const COMPANIES = [{ id: 10, name: 'Công ty DEGO' }] as Company[]

const BASE_DATA = {
  id: 7,
  code: 'YCMH-007',
  created_at: '2026-09-20T08:00:00',
  company_id: 10,
  company_name: 'Công ty DEGO',
  requester: 'Nguyễn Văn An',
  requester_id: 1,
  requester_position: 'Kỹ sư',
  department: 'Phòng Kỹ thuật',
  head_of_dept: '',
  head_of_dept_id: 0,
  handler_dept_id: 0,
  received_date: '',
  is_urgent: false,
  purpose: '',
  note: '',
} as PurchaseRequestDetail

function renderCard(
  props: Partial<Parameters<typeof PurchaseRequestInfoCard>[0]> = {},
) {
  const onChange = vi.fn()
  render(
    <MemoryRouter>
      <PurchaseRequestInfoCard
        data={BASE_DATA}
        editing
        companies={COMPANIES}
        employees={EMPLOYEES}
        onChange={onChange}
        {...props}
      />
    </MemoryRouter>,
  )
  return { onChange }
}

describe('PurchaseRequestInfoCard — Nhân sự YC', () => {
  it('filters employees by the text typed straight into the box, ignoring diacritics', async () => {
    const user = userEvent.setup()
    renderCard()

    const requester = screen.getByRole('combobox', { name: /Nhân sự YC/ })
    expect(requester).toHaveValue('NV001 - Nguyễn Văn An')

    //  Gõ không dấu vẫn phải ra người có dấu — người dùng gõ nhanh hay bỏ dấu.
    //  `type` tự bấm vào ô một lần rồi mới gõ, đúng thao tác của người dùng.
    await user.type(requester, 'tran')

    expect(screen.getByRole('button', { name: 'NV002 - Trần Thị Lan' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'NV001 - Nguyễn Văn An' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'NV003 - Lê Minh Tuấn' })).toBeNull()
  })

  it('also matches by employee code', async () => {
    const user = userEvent.setup()
    renderCard()

    const requester = screen.getByRole('combobox', { name: /Nhân sự YC/ })
    await user.type(requester, 'NV003')

    expect(screen.getByRole('button', { name: 'NV003 - Lê Minh Tuấn' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'NV002 - Trần Thị Lan' })).toBeNull()
  })

  it('says so when nobody matches instead of showing an empty list', async () => {
    const user = userEvent.setup()
    renderCard()

    const requester = screen.getByRole('combobox', { name: /Nhân sự YC/ })
    await user.type(requester, 'khong ai ten nay')

    expect(screen.getByText('Không tìm thấy mục nào.')).toBeInTheDocument()
  })

  it('picking a person fills department, position and drops the head of another department', async () => {
    const user = userEvent.setup()
    const { onChange } = renderCard({ data: { ...BASE_DATA, head_of_dept_id: 99 } })

    const requester = screen.getByRole('combobox', { name: /Nhân sự YC/ })
    await user.type(requester, 'lan')
    await user.click(screen.getByRole('button', { name: 'NV002 - Trần Thị Lan' }))

    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith({
      requester_id: 2,
      requester: 'Trần Thị Lan',
      requester_position: 'Kế toán',
      department: 'Phòng Kế toán',
      head_of_dept: 'Phạm Thị Hoa',
      //  Sang phòng khác thì TBP đã chọn không còn đúng phòng (CR-071).
      head_of_dept_id: 0,
      company_id: 10,
      company_name: 'Công ty DEGO',
    })
  })

  it('re-picking the current person changes nothing — the old Radix Select fired no event', async () => {
    //  Chạy tiếp handler thì ô TBP bị đè về trưởng phòng mặc định của nhân sự, dù
    //  người dùng chẳng đổi gì — mất người đứng tên đã chọn tay.
    const user = userEvent.setup()
    const { onChange } = renderCard()

    const requester = screen.getByRole('combobox', { name: /Nhân sự YC/ })
    await user.click(requester)
    await user.click(screen.getByRole('button', { name: 'NV001 - Nguyễn Văn An' }))

    expect(onChange).not.toHaveBeenCalled()
  })
})

describe('PurchaseRequestInfoCard — Trưởng bộ phận', () => {
  const CANDIDATES: DeptHeadCandidate[] = [
    { employee_id: 50, name: 'Lê Văn Trưởng', position: 'Trưởng phòng' },
    { employee_id: 51, name: 'Đỗ Văn Phó', position: '' },
  ] as DeptHeadCandidate[]

  it('shows the saved name, never a raw id, when that person is not among the candidates', () => {
    renderCard({
      deptHeadCandidates: CANDIDATES,
      data: { ...BASE_DATA, head_of_dept_id: 77, head_of_dept: 'Người Cũ Đã Chuyển Phòng' },
    })

    const head = screen.getByRole('combobox', { name: /Trưởng bộ phận/ })
    expect(head).toHaveValue('')
    expect(head).toHaveAttribute('placeholder', 'Người Cũ Đã Chuyển Phòng')
  })

  it('filters candidates by typed text and saves both id and name', async () => {
    const user = userEvent.setup()
    const { onChange } = renderCard({ deptHeadCandidates: CANDIDATES })

    const head = screen.getByRole('combobox', { name: /Trưởng bộ phận/ })
    await user.type(head, 'do van')

    expect(screen.queryByRole('button', { name: 'Lê Văn Trưởng - Trưởng phòng' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Đỗ Văn Phó' }))
    expect(onChange).toHaveBeenCalledWith({ head_of_dept_id: 51, head_of_dept: 'Đỗ Văn Phó' })
  })
})
