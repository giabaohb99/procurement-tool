import { describe, expect, it } from 'vitest'

import type { Employee } from '../types/employee'
import { countProfileGaps, countRecentHires, groupCount } from './hr-overview-metrics'

/** Hồ sơ ĐỦ THÔNG TIN — mỗi test chỉ đục đúng ô nó muốn kiểm. */
function makeEmployee(overrides: Partial<Employee> = {}): Employee {
  return {
    id: 1,
    code: 'NV001',
    full_name: 'Trần Thị A',
    email: '',
    phone: '',
    company_id: 1,
    department_id: 3,
    position: 'Nhân viên',
    position_id: 7,
    role_name: '',
    status: 'official',
    status_label: 'Chính thức',
    is_active: true,
    hire_date: '2020-01-15',
    manager_id: 9,
    gender: 2,
    avatar: '',
    signature: '',
    ...overrides,
  }
}

describe('countProfileGaps', () => {
  it('đếm SỐ HỒ SƠ thiếu, không cộng dồn số ô thiếu', () => {
    // Một người bỏ trống cả bốn ô vẫn chỉ là MỘT hồ sơ phải đi nhập bù. Cộng
    // dồn thì thẻ số liệu báo 4 và người dùng đi tìm bốn người không tồn tại.
    const gaps = countProfileGaps([
      makeEmployee({
        id: 1,
        department_id: 0,
        manager_id: 0,
        hire_date: null,
        position: '',
        position_id: 0,
      }),
    ])

    expect(gaps.total).toBe(1)
    expect(gaps.noDepartment).toBe(1)
    expect(gaps.noManager).toBe(1)
    expect(gaps.noHireDate).toBe(1)
    expect(gaps.noPosition).toBe(1)
  })

  it('bỏ qua người đã nghỉ — không ai phải đi nhập bù cho họ nữa', () => {
    const gaps = countProfileGaps([
      makeEmployee({ id: 1, is_active: false, department_id: 0, manager_id: 0 }),
    ])

    expect(gaps.total).toBe(0)
    expect(gaps.noDepartment).toBe(0)
  })

  it('không đếm thiếu quản lý khi API cũ KHÔNG gửi `manager_id` mà vẫn có tên', () => {
    // `manager_id` là cột thêm ở duoc-CR-314. `undefined` mà hiểu thành 0 thì
    // cả công ty bị đếm là "chưa gán" và thẻ cảnh báo trở thành tiếng ồn.
    const gaps = countProfileGaps([
      makeEmployee({ manager_id: undefined, direct_manager_name: 'Lê Văn B' }),
    ])

    expect(gaps.noManager).toBe(0)
  })

  it('vẫn đếm thiếu quản lý khi không có cả khóa lẫn tên', () => {
    const gaps = countProfileGaps([
      makeEmployee({ manager_id: undefined, direct_manager_name: '' }),
    ])

    expect(gaps.noManager).toBe(1)
  })

  it('chức vụ tính là đã gán khi chỉ còn NHÃN CHỮ của dữ liệu cũ', () => {
    // Hồ sơ dựng trước danh mục Chức vụ (duoc-CR-320) không có `position_id`.
    const gaps = countProfileGaps([
      makeEmployee({ position_id: 0, position: 'Trưởng phòng' }),
    ])

    expect(gaps.noPosition).toBe(0)
  })

  it('danh sách rỗng ra bốn số 0, không ném lỗi', () => {
    expect(countProfileGaps([])).toEqual({
      noDepartment: 0,
      noManager: 0,
      noHireDate: 0,
      noPosition: 0,
      total: 0,
    })
  })
})

describe('countRecentHires', () => {
  const today = new Date(2026, 8, 8) // 08/09/2026

  it('đếm người vào làm trong cửa sổ, tính cả hai đầu mút', () => {
    const list = [
      makeEmployee({ id: 1, hire_date: '2026-09-08' }), // đúng hôm nay
      makeEmployee({ id: 2, hire_date: '2026-08-09' }), // đúng 30 ngày trước
      makeEmployee({ id: 3, hire_date: '2026-08-08' }), // 31 ngày -> ngoài
    ]

    expect(countRecentHires(list, today, 30)).toBe(2)
  })

  it('không tính ngày vào làm ở TƯƠNG LAI', () => {
    // Hợp đồng đã ký nhưng người chưa tới — đưa vào "mới vào" thì con số nói
    // sai về đội hình đang có.
    expect(countRecentHires([makeEmployee({ hire_date: '2026-09-30' })], today, 30)).toBe(0)
  })

  it('bỏ qua hồ sơ chưa nhập ngày vào làm và người đã nghỉ', () => {
    const list = [
      makeEmployee({ id: 1, hire_date: null }),
      makeEmployee({ id: 2, hire_date: '', is_active: true }),
      makeEmployee({ id: 3, hire_date: '2026-09-01', is_active: false }),
    ]

    expect(countRecentHires(list, today, 30)).toBe(0)
  })
})

describe('groupCount', () => {
  it('xếp giảm dần, số bằng nhau thì theo bảng chữ cái tiếng Việt', () => {
    const list = [
      makeEmployee({ id: 1, department_name: 'Kế toán' }),
      makeEmployee({ id: 2, department_name: 'Ăn uống' }),
      makeEmployee({ id: 3, department_name: 'Thu mua' }),
      makeEmployee({ id: 4, department_name: 'Thu mua' }),
    ]

    expect(groupCount(list, (e) => e.department_name ?? '')).toEqual([
      { label: 'Thu mua', value: 2 },
      { label: 'Ăn uống', value: 1 },
      { label: 'Kế toán', value: 1 },
    ])
  })

  it('quá 12 hạng mục thì gom phần đuôi vào một cột "Khác"', () => {
    // 20 phòng ban, mỗi phòng 1 người: 11 cột đầu + 1 cột gom 9 phòng còn lại.
    const list = Array.from({ length: 20 }, (_, index) =>
      makeEmployee({ id: index + 1, department_name: `Phòng ${index + 1}` }),
    )

    const rows = groupCount(list, (e) => e.department_name ?? '')

    expect(rows).toHaveLength(12)
    expect(rows.at(-1)).toEqual({ label: 'Khác (9 mục)', value: 9 })
  })
})
