import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { EMPLOYEE_INFO_PRINT_SECTIONS } from '../config/employee-info-print-sections'
import type { Employee, EmployeeContact, EmployeeFamily } from '../types/employee'
import { EmployeeInfoPrintSheet } from './employee-info-print-sheet'

/**
 * Bản in "Phiếu thông tin nhân viên" BM00../QT01/NS (duoc-CR-676).
 *
 * Canh: đủ bảy mục đúng thứ tự, mã số in ra NHÃN chứ không in số, và ô bị backend che (thiếu
 * quyền nhạy cảm → `''` / `null`) in thành ô TRỐNG — không bao giờ ra chữ "null" / "undefined" /
 * "Chưa khai" trên giấy.
 */

function employee(overrides: Partial<Employee> = {}): Employee {
  return {
    id: 7,
    code: 'NSU007',
    full_name: 'Người Thử',
    company_name: 'Công ty Cổ phần DEGO',
    department_name: 'Phòng Kế toán',
    position: 'Kế toán viên',
    gender: 2,
    date_of_birth: '1990-05-01',
    marital_status: 2,
    marital_status_label: 'Có gia đình',
    children_count: 0,
    education_level: 4,
    employment_type: 1,
    hire_date: '2024-03-15',
    phone: '0901000111',
    bank_name: 'VCB',
    ...overrides,
  } as Employee
}

function fieldValue(label: string): string {
  //  Mỗi ô in là "Nhãn:" + một khối giá trị liền sau.
  const labelNode = screen.getByText(`${label}:`)
  return labelNode.nextElementSibling?.textContent ?? '(không có ô)'
}

describe('EmployeeInfoPrintSheet', () => {
  it('prints the header, form code and the seven sections in order', () => {
    render(<EmployeeInfoPrintSheet employee={employee()} contacts={[]} families={[]} />)

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('PHIẾU THÔNG TIN NHÂN VIÊN')
    //  Tên pháp nhân in ở đầu phiếu (và lặp lại ở ô "Pháp nhân" của mục II).
    const header = screen.getByRole('banner')
    expect(within(header).getByText('Công ty Cổ phần DEGO')).toBeInTheDocument()
    expect(within(header).getByText(/BM00\.\.\/QT01\/NS/)).toBeInTheDocument()
    expect(within(header).getByText('Ban hành 01/06/2025')).toBeInTheDocument()
    expect(fieldValue('Pháp nhân')).toBe('Công ty Cổ phần DEGO')

    const titles = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(titles).toEqual(EMPLOYEE_INFO_PRINT_SECTIONS.map((s) => s.title))
    expect(titles).toHaveLength(7)
    expect(screen.getByText('Người khai')).toBeInTheDocument()
    expect(screen.getByText('Phòng Nhân sự')).toBeInTheDocument()
  })

  it('prints labels for codes and dd/MM/yyyy for dates, preferring the backend label', () => {
    render(<EmployeeInfoPrintSheet employee={employee()} contacts={[]} families={[]} />)
    expect(fieldValue('Giới tính')).toBe('Nữ')
    expect(fieldValue('Tình trạng hôn nhân')).toBe('Có gia đình')
    expect(fieldValue('Trình độ học vấn')).toBe('Đại học')
    expect(fieldValue('Ngày sinh')).toBe('01/05/1990')
    expect(fieldValue('Ngày vào làm')).toBe('15/03/2024')
    //  `0` con là câu trả lời thật, phải in "0".
    expect(fieldValue('Số con')).toBe('0')
  })

  it('prints masked or missing values as blank cells, never null or a placeholder word', () => {
    //  Cách backend che: chuỗi rỗng cho chữ, null cho ngày (`sensitive.mask`).
    const masked = employee({
      date_of_birth: null,
      bank_account_no: '',
      id_number: '',
      id_issue_date: null,
      tax_code: '',
      gender: 0,
      education_level: 0,
    })
    const { container } = render(<EmployeeInfoPrintSheet employee={masked} contacts={[]} families={[]} />)

    expect(fieldValue('Ngày sinh')).toBe('')
    expect(fieldValue('Số tài khoản')).toBe('')
    expect(fieldValue('Số CCCD')).toBe('')
    expect(fieldValue('Ngày cấp CCCD')).toBe('')
    expect(fieldValue('Giới tính')).toBe('')
    expect(fieldValue('Trình độ học vấn')).toBe('')
    expect(container.textContent).not.toMatch(/null|undefined|NaN|Chưa khai|Invalid Date/)
  })

  it('fills the two people tables and keeps blank lines for handwriting', () => {
    const contacts: EmployeeContact[] = [
      { id: 1, full_name: 'Mẹ Thử', relation: 3, address: '12 Lê Lợi', phone: '0909', sort_order: 0 },
    ]
    const families: EmployeeFamily[] = [
      { id: 2, full_name: 'Con Thử', relation: 6, gender: 1, date_of_birth: '2015-02-03', phone: '', id_number: '', sort_order: 0 },
    ]
    render(<EmployeeInfoPrintSheet employee={employee()} contacts={contacts} families={families} />)

    const [contactTable, familyTable] = screen.getAllByRole('table')
    expect(within(contactTable).getByText('Mẹ Thử')).toBeInTheDocument()
    expect(within(contactTable).getByText('Mẹ')).toBeInTheDocument()
    expect(within(familyTable).getByText('Con trai')).toBeInTheDocument()
    expect(within(familyTable).getByText('03/02/2015')).toBeInTheDocument()
    //  Tiêu đề + 1 dòng có dữ liệu + 2 dòng trống = tối thiểu 3 dòng thân.
    expect(within(contactTable).getAllByRole('row')).toHaveLength(4)
  })

  it('still prints empty people tables when the viewer cannot read them', () => {
    render(<EmployeeInfoPrintSheet employee={employee()} contacts={[]} families={[]} />)
    for (const table of screen.getAllByRole('table')) {
      expect(within(table).getAllByRole('row')).toHaveLength(4)
    }
  })
})
