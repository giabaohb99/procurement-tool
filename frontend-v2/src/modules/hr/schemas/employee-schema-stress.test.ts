import { describe, expect, it } from 'vitest'

import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  SENSITIVE_PROFILE_FIELDS,
  employeeProfileFormValues,
  employeeProfileSchema,
  pickWritableProfile,
} from './employee-schema'
import { codeLabel, JOB_LEVEL_OPTIONS } from '../types/employee-codes'
import type { Employee } from '../types/employee'

/**
 * STRESS TEST tầng dữ liệu hồ sơ nhân sự (duoc-CR-316).
 *
 * `employee-schema.test.ts` kiểm luật chạy đúng. Bộ này cố tình PHÁ: giá trị
 * `null`/`undefined` mà kiểu nói là không có, số `NaN`/`Infinity`, chuỗi dài
 * hơn cột, đối tượng thiếu khóa.
 *
 * ⚠️ Backend trả về gì thì đây phải chịu được đúng thứ đó. `Employee` khai gần
 * hết trường mới là **tùy chọn** (`?:`) vì hồ sơ cũ không có cột nào trong số
 * đó — nên mọi hàm ở đây phải sống sót với một bản ghi chỉ có 10 trường gốc.
 */

const LEGACY: Employee = {
  id: 1,
  code: 'NS001',
  full_name: 'A',
  email: '',
  phone: '',
  company_id: 0,
  department_id: 0,
  position: '',
  role_name: '',
  status: 'official',
  status_label: '',
  is_active: true,
  gender: 0,
  avatar: '',
  signature: '',
}

describe('pickWritableProfile — ca cực đoan', () => {
  it('survives an object that has none of the sensitive keys', () => {
    // Dữ liệu từ một bản dựng cũ, hoặc bản ghi bị cắt bớt.
    const out = pickWritableProfile({} as never, false)
    expect(out).toEqual({})
  })

  it('drops a sensitive key even when its value is a real string', () => {
    // Bảo vệ phải theo KHÓA, không theo "giá trị có rỗng hay không" — người
    // không được xem mà lại đang cầm giá trị thật thì càng phải bỏ.
    const out = pickWritableProfile(
      { ...EMPTY_EMPLOYEE_PROFILE_FORM, bank_account_no: '1903' },
      false,
    )
    expect(out).not.toHaveProperty('bank_account_no')
  })

  it('keeps the object usable as a PATCH body — no undefined keys left behind', () => {
    const out = pickWritableProfile({ ...EMPTY_EMPLOYEE_PROFILE_FORM }, false)
    // `delete` phải bỏ hẳn khóa, không để lại `key: undefined` — JSON.stringify
    // bỏ qua undefined nên lỗi này sẽ im lặng cho tới khi ai đó dùng Object.keys.
    for (const field of SENSITIVE_PROFILE_FIELDS) {
      expect(Object.keys(out)).not.toContain(field)
    }
  })

  it('leaves an empty-but-writable field alone — xóa ô là thao tác hợp lệ', () => {
    const out = pickWritableProfile(
      { ...EMPTY_EMPLOYEE_PROFILE_FORM, work_location: '' },
      false,
    )
    expect(out).toHaveProperty('work_location', '')
  })
})

describe('employeeProfileFormValues — bản ghi thiếu trường', () => {
  it('handles a legacy record with none of the new columns', () => {
    const out = employeeProfileFormValues(LEGACY)
    expect(out.tax_code).toBe('')
    expect(out.marital_status).toBe(0)
    expect(out.date_of_birth).toBe('')
  })

  it('reads an explicitly undefined date as empty, not as the string "undefined"', () => {
    const out = employeeProfileFormValues({ ...LEGACY, hire_date: undefined })
    expect(out.hire_date).toBe('')
  })

  it('does not let a null numeric code become null in the form', () => {
    // Ô chọn nhận `null` là Radix ném — mà lỗi đó chỉ nổ với hồ sơ cũ.
    const out = employeeProfileFormValues({
      ...LEGACY,
      gender: null as unknown as number,
    })
    expect(out.gender).toBe(0)
  })

  it('keeps unknown extra keys from the API out of the form shape', () => {
    // Backend thêm cột mới mà frontend chưa biết → không được làm vỡ form.
    const out = employeeProfileFormValues({
      ...LEGACY,
      cot_moi_backend_vua_them: 'x',
    } as unknown as Employee)
    expect(out.full_name).toBe('A')
  })
})

describe('employeeProfileSchema — biên của từng ô', () => {
  const base = { ...EMPTY_EMPLOYEE_PROFILE_FORM, full_name: 'A' }

  it.each([
    ['tax_code', 20],
    ['id_number', 20],
    ['bank_name', 100],
    ['place_of_birth', 255],
    ['permanent_address', 500],
  ])('rejects %s longer than its column (%i)', (field, limit) => {
    const out = employeeProfileSchema.safeParse({ ...base, [field]: 'x'.repeat(limit + 1) })
    expect(out.success).toBe(false)
  })

  it.each([
    ['tax_code', 20],
    ['bank_name', 100],
    ['permanent_address', 500],
  ])('accepts %s at exactly its column length (%i)', (field, limit) => {
    const out = employeeProfileSchema.safeParse({ ...base, [field]: 'x'.repeat(limit) })
    expect(out.success).toBe(true)
  })

  it('rejects a fractional child count — nửa đứa con không tồn tại', () => {
    expect(employeeProfileSchema.safeParse({ ...base, children_count: 1.5 }).success).toBe(false)
  })

  it('rejects NaN and Infinity in a numeric code', () => {
    expect(employeeProfileSchema.safeParse({ ...base, job_level: NaN }).success).toBe(false)
    expect(employeeProfileSchema.safeParse({ ...base, job_level: Infinity }).success).toBe(false)
  })

  it('rejects a negative manager id', () => {
    expect(employeeProfileSchema.safeParse({ ...base, manager_id: -1 }).success).toBe(false)
  })

  it('trims a name made only of whitespace down to empty and rejects it', () => {
    expect(employeeProfileSchema.safeParse({ ...base, full_name: '\n\t  ' }).success).toBe(false)
  })

  it('accepts a name at exactly 255 characters', () => {
    expect(
      employeeProfileSchema.safeParse({ ...base, full_name: 'Đ'.repeat(255) }).success,
    ).toBe(true)
  })
})

/**
 * Đối chiếu giới hạn của form với ĐỘ RỘNG CỘT thật ở
 * `backend/app/modules/employee/model.py`.
 *
 * ⚠️ Lệch hai chiều đều hỏng, và cả hai đều im lặng:
 *   · form RỘNG hơn cột → người dùng gõ hết ô, không thấy lỗi nào, bấm Lưu mới
 *     ăn 422 từ backend kèm câu tiếng Anh `String should have at most…`;
 *   · form HẸP hơn cột → chặn nhầm, người dùng không dùng hết được ô.
 *
 * Đã dính chiều thứ nhất ngày 08/09/2026: `code` cho 50 nhưng cột `String(25)`,
 * `phone` cho 30 nhưng cột `String(25)`.
 */
const COLUMN_WIDTHS: Record<string, number> = {
  code: 25,
  full_name: 255,
  email: 255,
  phone: 25,
  //  ⚠️ `position` KHÔNG còn trong bảng này từ duoc-CR-320: form gửi
  //  `position_id` (số), còn cột chữ `position` là NHÃN do backend chép từ danh
  //  mục — không ô nhập nào gõ vào nó nữa, nên "form rộng hơn cột" không còn là
  //  câu hỏi có nghĩa. Chốt độ dài tên chức vụ nay nằm ở
  //  `test_danh_muc_chuc_vu.py` phía backend (`Str100` của `JobPositionCreate`).
  place_of_birth: 255,
  ethnicity: 50,
  religion: 50,
  personal_email: 255,
  tax_code: 20,
  major: 255,
  work_location: 255,
  permanent_address: 500,
  current_address: 500,
  bank_account_no: 50,
  bank_account_name: 255,
  bank_name: 100,
  bank_branch: 255,
  id_number: 20,
  id_issue_place: 255,
  social_insurance_no: 20,
  health_care_place: 255,
  health_care_code: 20,
}

describe('giới hạn của form khớp ĐỘ RỘNG CỘT ở backend', () => {
  const base = { ...EMPTY_EMPLOYEE_PROFILE_FORM, full_name: 'A' }

  it.each(Object.entries(COLUMN_WIDTHS))(
    '%s: nhận đúng %i ký tự, từ chối ký tự thứ n+1',
    (field, width) => {
      const atLimit = employeeProfileSchema.safeParse({ ...base, [field]: 'x'.repeat(width) })
      expect(atLimit.success, `${field} bị chặn HỤT — form hẹp hơn cột`).toBe(true)

      const qua = employeeProfileSchema.safeParse({ ...base, [field]: 'x'.repeat(width + 1) })
      expect(qua.success, `${field} lọt — form RỘNG hơn cột, backend sẽ 422`).toBe(false)
    },
  )
})

describe('codeLabel — đầu vào dị dạng', () => {
  it.each([NaN, Infinity, -Infinity, -1, 9999, 0.5])('returns empty for %p', (value) => {
    expect(codeLabel(JOB_LEVEL_OPTIONS, value)).toBe('')
  })

  it('returns empty for an empty option set instead of throwing', () => {
    expect(codeLabel([], 1)).toBe('')
  })
})
