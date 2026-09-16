import { describe, expect, it } from 'vitest'

import { VALIDITY_MONTHS, VALIDITY_OPTIONS, formatValidity } from './validity-text'

describe('formatValidity', () => {
  it('coi 0 là VÔ THỜI HẠN, không phải "0 tháng"', () => {
    //  Quy tắc nghiệp vụ, không phải chuyện chữ nghĩa: `0` là một lựa chọn THẬT
    //  (giấy chứng nhận đăng ký doanh nghiệp, quyết định bổ nhiệm). Bày số 0 trần
    //  thì người đọc hiểu là ô chưa ai nhập và đi tìm cho đủ.
    expect(formatValidity(0)).toBe('Vô thời hạn')
  })

  it('nói bằng NĂM khi là bội của 12', () => {
    expect(formatValidity(12)).toBe('1 năm')
    expect(formatValidity(24)).toBe('2 năm')
    expect(formatValidity(120)).toBe('10 năm')
  })

  it('nói bằng THÁNG khi không chia hết cho 12', () => {
    expect(formatValidity(3)).toBe('3 tháng')
    expect(formatValidity(6)).toBe('6 tháng')
    expect(formatValidity(18)).toBe('18 tháng')
  })

  it('số âm / rác cũng ra Vô thời hạn chứ không ném lỗi', () => {
    //  Dữ liệu cũ hoặc ai đó gọi thẳng API đều lọt xuống đây được. Một cột bảng
    //  ném lỗi là vỡ cả trang danh sách vì MỘT dòng hỏng.
    expect(formatValidity(-1)).toBe('Vô thời hạn')
    expect(formatValidity(Number.NaN)).toBe('Vô thời hạn')
    expect(formatValidity(Number.POSITIVE_INFINITY)).toBe('Vô thời hạn')
  })
})

describe('VALIDITY_OPTIONS', () => {
  it('nhãn lấy đúng formatValidity — ô chọn và cột bảng không được nói khác nhau', () => {
    //  LỖI ĐÃ TRÁNH: ô chọn ghi «3 năm» còn cột *Hạn mặc định* ghi «36 tháng» cho
    //  cùng một dòng, người dùng đọc ra hai giá trị và đi tìm chỗ mình sửa hụt.
    for (const option of VALIDITY_OPTIONS) {
      expect(option.label).toBe(formatValidity(Number(option.value)))
    }
  })

  it('có mục Vô thời hạn, và mọi mốc đều nằm trong dải backend nhận (0..1200)', () => {
    //  Trần 1200 tháng khai ở `backend/app/modules/dossier/type_schema.py`
    //  (`ValidMonths`). Thêm một mốc vượt trần là người dùng chọn xong ăn 422.
    expect(VALIDITY_OPTIONS.some((o) => o.value === 0)).toBe(true)
    for (const months of VALIDITY_MONTHS) {
      expect(months).toBeGreaterThanOrEqual(0)
      expect(months).toBeLessThanOrEqual(1200)
    }
  })

  it('không có mốc trùng nhau', () => {
    expect(new Set(VALIDITY_MONTHS).size).toBe(VALIDITY_MONTHS.length)
  })
})
