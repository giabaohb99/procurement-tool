import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { EmployeeCard } from '../components/employee-card'
import type { Employee, EmployeeConcurrentRole } from '../types/employee'
import { EMPLOYEE_COLUMNS } from './employee-columns'

/** duoc-CR-756 — cột "Kiêm nhiệm" của danh sách nhân sự + dòng phụ trên thẻ điện thoại. */
function makeEmployee(over: Partial<Employee> = {}): Employee {
  return {
    id: 1,
    code: 'NSU001',
    full_name: 'Nguyễn Văn A',
    email: 'a@x.vn',
    direct_manager_name: 'Trần B',
    position: 'Chuyên viên',
    status: 'official',
    status_label: 'Chính thức',
    avatar: '',
    ...over,
  } as Employee
}

const DEPT: EmployeeConcurrentRole = { kind: 1, text: 'Phòng Kế toán (Phó phòng)' }
const DEPT_2: EmployeeConcurrentRole = { kind: 1, text: 'Phòng Thu mua' }
const COMPANY: EmployeeConcurrentRole = { kind: 2, text: 'Công ty B (Giám đốc)' }

const column = EMPLOYEE_COLUMNS.find((c) => c.key === 'concurrent_roles')

function renderCell(roles?: EmployeeConcurrentRole[]) {
  return render(<>{column!.cell(makeEmployee({ concurrent_roles: roles }))}</>)
}

describe('cột Kiêm nhiệm của danh sách nhân sự', () => {
  it('có cột, KHÔNG sortable (đa giá trị, máy chủ không nhận khóa xếp), hiện mặc định', () => {
    expect(column).toBeDefined()
    expect(column?.header).toBe('Kiêm nhiệm')
    expect(column?.sortable).toBeFalsy()
    expect(column?.defaultHidden).toBeFalsy()
  })

  it('một mục: chỉ chữ mục đó, KHÔNG huy hiệu +N', () => {
    renderCell([COMPANY])
    expect(screen.getByText('Công ty B (Giám đốc)')).toBeInTheDocument()
    expect(screen.queryByText(/^\+\d+$/)).not.toBeInTheDocument()
  })

  it('nhiều mục: chỉ mục ĐẦU (thứ tự backend) + huy hiệu +N, các mục còn lại chưa hiện', () => {
    renderCell([DEPT, DEPT_2, COMPANY])
    expect(screen.getByText('Phòng Kế toán (Phó phòng)')).toBeInTheDocument()
    expect(screen.getByText('+2')).toBeInTheDocument()
    expect(screen.queryByText('Phòng Thu mua')).not.toBeInTheDocument()
    expect(screen.queryByText('Công ty B (Giám đốc)')).not.toBeInTheDocument()
  })

  it('rê chuột vào ô thì tooltip liệt kê ĐỦ mọi dòng, mỗi dòng một hàng', async () => {
    const user = userEvent.setup()
    renderCell([DEPT, DEPT_2, COMPANY])
    await user.hover(screen.getByText('Phòng Kế toán (Phó phòng)'))
    const items = await screen.findAllByRole('listitem')
    expect(items.map((li) => li.textContent)).toEqual([
      'Phòng Kế toán (Phó phòng)',
      'Phòng Thu mua',
      'Công ty B (Giám đốc)',
    ])
  })

  it('ô trống để TRỐNG khi không kiêm nhiệm hoặc thiếu khóa', () => {
    const { container, rerender } = renderCell([])
    expect(container).toBeEmptyDOMElement()
    rerender(<>{column!.cell(makeEmployee())}</>)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('EmployeeCard — dòng Kiêm nhiệm', () => {
  it('có kiêm nhiệm: một dòng chữ "Kiêm nhiệm: <mục đầu> +N", không phải nút', () => {
    render(<EmployeeCard employee={makeEmployee({ concurrent_roles: [DEPT_2, COMPANY] })} />)
    const label = screen.getByText('Kiêm nhiệm:')
    const line = label.parentElement as HTMLElement
    expect(within(line).getByText('Phòng Thu mua')).toBeInTheDocument()
    expect(within(line).getByText('+1')).toBeInTheDocument()
    expect(line).toHaveAttribute('title', 'Phòng Thu mua; Công ty B (Giám đốc)')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('trong thẻ bọc <button> (khuôn DataTableMobileCards) không lồng nút và React không cảnh báo DOM', () => {
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <button type="button">
        <EmployeeCard employee={makeEmployee({ concurrent_roles: [DEPT_2, COMPANY] })} />
      </button>,
    )
    expect(screen.getAllByRole('button')).toHaveLength(1)
    expect(errors.mock.calls.flat().join(' ')).not.toMatch(/validateDOMNesting|cannot be a descendant/)
    errors.mockRestore()
  })

  it('chạm vào dòng Kiêm nhiệm vẫn là chạm thẻ cha (không chặn nổi bọt)', async () => {
    const user = userEvent.setup()
    const onCardClick = vi.fn()
    render(
      <div onClick={onCardClick}>
        <EmployeeCard employee={makeEmployee({ concurrent_roles: [DEPT_2] })} />
      </div>,
    )
    await user.click(screen.getByText('Kiêm nhiệm:'))
    expect(onCardClick).toHaveBeenCalledTimes(1)
  })

  it('không kiêm nhiệm thì không có dòng đó', () => {
    render(<EmployeeCard employee={makeEmployee({ concurrent_roles: [] })} />)
    expect(screen.queryByText(/Kiêm nhiệm/)).not.toBeInTheDocument()
  })
})
