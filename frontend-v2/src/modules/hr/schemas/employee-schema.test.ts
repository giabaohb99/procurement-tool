import { describe, expect, it } from 'vitest'

import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  SENSITIVE_PROFILE_FIELDS,
  employeeFormValues,
  employeeProfileFormValues,
  employeeProfileSchema,
  employeeSchema,
  pickWritableProfile,
} from './employee-schema'
import type { Employee } from '../types/employee'

/**
 * Hồ sơ nhân sự mở rộng (duoc-CR-314 Đợt 2).
 *
 * Bài quan trọng nhất ở đây là `pickWritableProfile` — nó đứng giữa một đường
 * MẤT DỮ LIỆU có thật: backend che trường nhạy cảm bằng chuỗi RỖNG, nên hành
 * chính không có `employee_sensitive.read` mở hồ sơ ra sửa số điện thoại rồi
 * bấm Lưu là PATCH rỗng đè lên số tài khoản ngân hàng, và không ai biết cho tới
 * kỳ trả lương.
 */

const BASE: Employee = {
  id: 7,
  code: 'NS007',
  full_name: 'Nguyễn Văn A',
  email: 'a@dego.vn',
  phone: '0901234567',
  company_id: 1,
  department_id: 2,
  position: 'Nhân viên',
  role_name: '',
  status: 'official',
  status_label: 'Chính thức',
  is_active: true,
  gender: 1,
  avatar: '',
  signature: '',
}

describe('pickWritableProfile', () => {
  it('keeps every field when the user may read the sensitive group', () => {
    const values = { ...EMPTY_EMPLOYEE_PROFILE_FORM, bank_account_no: '1903', tax_code: '999' }
    const out = pickWritableProfile(values, true)

    expect(out.bank_account_no).toBe('1903')
    expect(out.tax_code).toBe('999')
  })

  it('drops every sensitive key when the user may not read them', () => {
    // Backend đã che nên form đang cầm chuỗi rỗng — đúng tình huống mất dữ liệu.
    const out = pickWritableProfile({ ...EMPTY_EMPLOYEE_PROFILE_FORM }, false)

    for (const field of SENSITIVE_PROFILE_FIELDS) {
      expect(out, `còn khóa ${field} là ghi đè rỗng lên dữ liệu thật`).not.toHaveProperty(field)
    }
  })

  it('still sends the non-sensitive fields the user actually edited', () => {
    const values = { ...EMPTY_EMPLOYEE_PROFILE_FORM, phone: '0988', full_name: 'Tên mới' }
    const out = pickWritableProfile(values, false)

    expect(out.phone).toBe('0988')
    expect(out.full_name).toBe('Tên mới')
  })

  it('does not mutate the caller values — the form keeps its own state', () => {
    const values = { ...EMPTY_EMPLOYEE_PROFILE_FORM, bank_name: 'TCB' }
    pickWritableProfile(values, false)

    expect(values.bank_name).toBe('TCB')
  })

  it('covers exactly the 13 form fields backend masks (2 ảnh CCCD không ở form)', () => {
    // Lệch danh sách này với `SENSITIVE_FIELDS` của backend là lỗ hổng mất dữ liệu.
    expect(SENSITIVE_PROFILE_FIELDS).toHaveLength(13)
  })
})

describe('employeeProfileFormValues', () => {
  it('turns every null date into an empty string', () => {
    // `null` đè được lên mặc định `''`, và ô ngày nhận `null` là mở hồ sơ ra đã đỏ lỗi.
    const out = employeeProfileFormValues({
      ...BASE,
      hire_date: null,
      date_of_birth: null,
      resign_date: null,
      id_issue_date: null,
      id_expiry_date: null,
    })

    expect(out.hire_date).toBe('')
    expect(out.date_of_birth).toBe('')
    expect(out.resign_date).toBe('')
    expect(out.id_issue_date).toBe('')
    expect(out.id_expiry_date).toBe('')
  })

  it('fills defaults for a legacy record that has none of the new columns', () => {
    const out = employeeProfileFormValues(BASE)

    expect(out.manager_id).toBe(0)
    expect(out.job_level).toBe(0)
    expect(out.children_count).toBe(0)
    expect(out.bank_name).toBe('')
  })

  it('returns a blank form for a missing record instead of throwing', () => {
    expect(employeeProfileFormValues(null)).toEqual(EMPTY_EMPLOYEE_PROFILE_FORM)
    expect(employeeProfileFormValues(undefined)).toEqual(EMPTY_EMPLOYEE_PROFILE_FORM)
  })

  it('keeps a real date untouched', () => {
    const out = employeeProfileFormValues({ ...BASE, date_of_birth: '1990-05-01' })
    expect(out.date_of_birth).toBe('1990-05-01')
  })
})

describe('employeeFormValues (form tạo nhanh)', () => {
  it('carries the two new quick-create fields', () => {
    const out = employeeFormValues({ ...BASE, date_of_birth: '1990-05-01' })

    expect(out.company_id).toBe(1)
    expect(out.date_of_birth).toBe('1990-05-01')
  })

  it('reads a null birth date as empty, same rule as hire date', () => {
    expect(employeeFormValues({ ...BASE, date_of_birth: null }).date_of_birth).toBe('')
  })
})

describe('employeeProfileSchema', () => {
  it('rejects a job level outside the code set', () => {
    const out = employeeProfileSchema.safeParse({ ...EMPTY_EMPLOYEE_PROFILE_FORM, job_level: 99 })
    expect(out.success).toBe(false)
  })

  it('rejects a negative child count', () => {
    const out = employeeProfileSchema.safeParse({
      ...EMPTY_EMPLOYEE_PROFILE_FORM,
      children_count: -1,
    })
    expect(out.success).toBe(false)
  })

  it('rejects an id number longer than the column', () => {
    const out = employeeProfileSchema.safeParse({
      ...EMPTY_EMPLOYEE_PROFILE_FORM,
      full_name: 'A',
      id_number: '0'.repeat(21),
    })
    expect(out.success).toBe(false)
  })

  it('accepts a record with every optional field left blank', () => {
    const out = employeeProfileSchema.safeParse({
      ...EMPTY_EMPLOYEE_PROFILE_FORM,
      full_name: 'Nguyễn Văn A',
    })
    expect(out.success).toBe(true)
  })

  it('still requires a full name — the one field a profile cannot exist without', () => {
    const out = employeeProfileSchema.safeParse({ ...EMPTY_EMPLOYEE_PROFILE_FORM, full_name: '  ' })
    expect(out.success).toBe(false)
  })
})

describe('employeeSchema (tạo nhanh) vs employeeProfileSchema (đầy đủ)', () => {
  it('quick-create does NOT accept the extended fields — it must stay ~10 ô', () => {
    // Gộp hai schema là hộp thoại tạo nhanh gửi thừa 20 ô rỗng lên backend.
    const quick = employeeSchema.safeParse({
      code: '',
      full_name: 'A',
      email: '',
      phone: '',
      department_id: 0,
      position_id: 0,
      status: 'official',
      is_active: true,
      hire_date: '',
      gender: 0,
      company_id: 0,
      date_of_birth: '',
    })
    expect(quick.success).toBe(true)
    if (quick.success) {
      expect(quick.data).not.toHaveProperty('bank_account_no')
      expect(quick.data).not.toHaveProperty('manager_id')
    }
  })
})
