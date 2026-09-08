import { describe, expect, it } from 'vitest'

import {
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_FILTER_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  JOB_LEVEL_FILTER_OPTIONS,
  JOB_LEVEL_OPTIONS,
  MARITAL_MARRIED,
  MARITAL_STATUS_OPTIONS,
  RELATION_OPTIONS,
  codeLabel,
} from './employee-codes'
//  Giới tính khai ở `types/employee.ts` (cùng chỗ với `Employee`) nhưng vẫn là
//  một bộ mã số của hồ sơ, nên chốt số mục ở ngay đây cho một chỗ mà tra.
import { EMPLOYEE_GENDER_OPTIONS, employeeGenderLabel } from './employee'

/**
 * Bốn bộ mã SỐ của hồ sơ nhân sự.
 *
 * ⚠️ Bộ này gõ TAY — `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI. Không có gì
 * canh việc nó khớp `backend/app/modules/employee/constants.py`, nên bài dưới
 * đây chốt cứng số mục và giá trị: đổi một con số ở backend mà quên bên này thì
 * ít nhất test đỏ chứ không phải người dùng phát hiện qua một ô chọn trống.
 */

describe('bộ mã số của hồ sơ nhân sự', () => {
  it('giữ đúng số mục như backend khai', () => {
    expect(MARITAL_STATUS_OPTIONS).toHaveLength(4) // 0..3
    expect(EDUCATION_LEVEL_OPTIONS).toHaveLength(6) // 0..5
    expect(EMPLOYMENT_TYPE_OPTIONS).toHaveLength(7) // 0..6
    expect(JOB_LEVEL_OPTIONS).toHaveLength(7) // 0..6
  })

  it('đánh số liên tục từ 0, không nhảy cóc', () => {
    for (const set of [
      MARITAL_STATUS_OPTIONS,
      EDUCATION_LEVEL_OPTIONS,
      EMPLOYMENT_TYPE_OPTIONS,
      JOB_LEVEL_OPTIONS,
    ]) {
      expect(set.map((o) => o.value)).toEqual(set.map((_, i) => i))
    }
  })

  it('để nhãn của mã 0 RỖNG — "chưa khai" không phải một lựa chọn', () => {
    // Gắn chữ cho nó thì ô chọn đọc ra như đã chọn xong, trong khi hồ sơ còn trống.
    for (const set of [
      MARITAL_STATUS_OPTIONS,
      EDUCATION_LEVEL_OPTIONS,
      EMPLOYMENT_TYPE_OPTIONS,
      JOB_LEVEL_OPTIONS,
    ]) {
      expect(set[0]).toEqual({ value: 0, label: '' })
    }
  })
})

describe('giới tính của hồ sơ', () => {
  it('có đủ bốn mục, «Khác» là mã 3 — khớp `employee/constants.GENDER_*`', () => {
    expect(EMPLOYEE_GENDER_OPTIONS.map((o) => o.value)).toEqual([0, 1, 2, 3])
    expect(employeeGenderLabel(3)).toBe('Khác')
  })

  it('mã 0 vẫn là «Chưa khai», KHÔNG phải «Khác»', () => {
    // Gộp hai thứ này là mất luôn khả năng phân biệt "chưa ai nhập" với một
    // giới tính đã khai — mà nghỉ phép đối xử với hai ca đó ngược nhau: chưa
    // khai thì không bị chặn loại nghỉ theo giới, «Khác» thì bị chặn.
    expect(employeeGenderLabel(0)).toBe('Chưa khai')
    expect(employeeGenderLabel(null)).toBe('Chưa khai')
  })

  it('mã ngoài bộ trả rỗng, không trả bừa mục nào', () => {
    expect(employeeGenderLabel(4)).toBe('')
  })
})

describe('codeLabel', () => {
  it('trả nhãn tiếng Việt của một mã hợp lệ', () => {
    expect(codeLabel(JOB_LEVEL_OPTIONS, 4)).toBe('Trưởng phòng')
    expect(codeLabel(MARITAL_STATUS_OPTIONS, 2)).toBe('Có gia đình')
  })

  it('trả RỖNG cho mã lạ, không trả lại con số', () => {
    // Cùng luật với backend: nhìn dữ liệu là biết ngay dòng nào ngoài bộ mã.
    expect(codeLabel(JOB_LEVEL_OPTIONS, 99)).toBe('')
    expect(codeLabel(JOB_LEVEL_OPTIONS, -1)).toBe('')
  })

  it('đọc null / undefined thành mã 0 (chưa khai)', () => {
    expect(codeLabel(JOB_LEVEL_OPTIONS, null)).toBe('')
    expect(codeLabel(JOB_LEVEL_OPTIONS, undefined)).toBe('')
  })
})

describe('bộ mã QUAN HỆ nhân thân', () => {
  it('có đủ 15 mục kể cả «chưa khai» và «Khác»', () => {
    expect(RELATION_OPTIONS).toHaveLength(15)
  })

  it('đánh số 0..13 liền mạch rồi NHẢY sang 99 cho «Khác»', () => {
    // Nhảy số là CỐ Ý: chừa chỗ cho quan hệ thêm về sau, «Khác» luôn cuối bảng.
    const values = RELATION_OPTIONS.map((o) => o.value)
    expect(values.slice(0, 14)).toEqual([...Array(14).keys()])
    expect(values.at(-1)).toBe(99)
  })

  it('để nhãn mã 0 rỗng — «chưa khai» không phải một lựa chọn', () => {
    expect(RELATION_OPTIONS[0]).toEqual({ value: 0, label: '' })
  })

  it('phủ đủ cả hai giới, vì danh sách DÙNG CHUNG không lọc theo giới tính', () => {
    const labels = RELATION_OPTIONS.map((o) => o.label)
    for (const label of ['Cha', 'Mẹ', 'Vợ', 'Chồng', 'Con trai', 'Con gái', 'Ông', 'Bà']) {
      expect(labels, `thiếu «${label}»`).toContain(label)
    }
  })

  it('codeLabel đọc được mã nhảy số 99', () => {
    expect(codeLabel(RELATION_OPTIONS, 99)).toBe('Khác')
  })

  it('mã lạ giữa hai khoảng (vd 50) trả rỗng, không trả bừa mục nào', () => {
    expect(codeLabel(RELATION_OPTIONS, 50)).toBe('')
  })
})

describe('luật hiện ô «Số con»', () => {
  it('MARITAL_MARRIED trỏ đúng mục Có gia đình trong bảng nhãn', () => {
    // Lệch hằng số này thì ô Số con hiện với «Độc thân» — im lặng và sai.
    expect(codeLabel(MARITAL_STATUS_OPTIONS, MARITAL_MARRIED)).toBe('Có gia đình')
  })

  it('KHÔNG trùng Độc thân hay Ly hôn — hai mục đó không hỏi số con', () => {
    expect(codeLabel(MARITAL_STATUS_OPTIONS, MARITAL_MARRIED)).not.toBe('Độc thân')
    expect(codeLabel(MARITAL_STATUS_OPTIONS, MARITAL_MARRIED)).not.toBe('Ly hôn')
  })
})

describe('bộ options cho Ô LỌC', () => {
  it('bỏ mục 0 — "lọc theo chưa khai" không có nghĩa', () => {
    expect(EMPLOYMENT_TYPE_FILTER_OPTIONS.some((o) => o.value === 0)).toBe(false)
    expect(JOB_LEVEL_FILTER_OPTIONS.some((o) => o.value === 0)).toBe(false)
  })

  it('giữ đủ các mục còn lại, không nhãn nào rỗng', () => {
    expect(EMPLOYMENT_TYPE_FILTER_OPTIONS).toHaveLength(EMPLOYMENT_TYPE_OPTIONS.length - 1)
    expect(JOB_LEVEL_FILTER_OPTIONS).toHaveLength(JOB_LEVEL_OPTIONS.length - 1)
    for (const o of [...EMPLOYMENT_TYPE_FILTER_OPTIONS, ...JOB_LEVEL_FILTER_OPTIONS]) {
      expect(o.label).not.toBe('')
    }
  })
})
