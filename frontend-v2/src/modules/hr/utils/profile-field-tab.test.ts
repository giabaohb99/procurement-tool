import { describe, expect, it } from 'vitest'

import {
  MAPPED_PROFILE_FIELDS,
  firstInvalidTab,
  tabOfField,
} from './profile-field-tab'
import { EMPTY_EMPLOYEE_PROFILE_FORM } from '../schemas/employee-schema'

/**
 * Bảng «trường nào ở tab nào» — vá cho một lỗi im lặng tuyệt đối.
 *
 * Người dùng nhập sai một ô ở tab «Giấy tờ & BHXH», sang tab «Chung», bấm Lưu →
 * **không có gì xảy ra**. Không toast, không lỗi trên màn, không lời gọi API
 * nào; nút Lưu đọc ra như bị hỏng. Lý do: Radix hủy mount tab ẩn, nên câu lỗi
 * của react-hook-form không có chỗ nào để hiện.
 *
 * Bảng này là thứ cho phép nhảy tới đúng tab. Bỏ sót một tên trường thì lỗi
 * quay lại — nên bài đầu tiên đối chiếu bảng với CHÍNH schema.
 */

describe('bảng trường → tab', () => {
  it('phủ ĐỦ mọi trường của form hồ sơ — bỏ sót là lỗi im lặng quay lại', () => {
    // Đối chiếu với schema thật, không với một danh sách chép tay thứ hai.
    const formFieldNames = Object.keys(EMPTY_EMPLOYEE_PROFILE_FORM)
    const missing = formFieldNames.filter((f) => !MAPPED_PROFILE_FIELDS.includes(f))

    expect(missing, `chưa khai tab cho: ${missing.join(', ')}`).toEqual([])
  })

  it('không khai thừa tên trường đã bị xóa khỏi form', () => {
    const formFieldNames = Object.keys(EMPTY_EMPLOYEE_PROFILE_FORM)
    const extra = MAPPED_PROFILE_FIELDS.filter((f) => !formFieldNames.includes(f))

    expect(extra, `khai thừa, không còn trong form: ${extra.join(', ')}`).toEqual([])
  })

  it.each([
    ['full_name', 'general'],
    ['tax_code', 'general'],
    ['hire_date', 'general'],
    ['manager_id', 'general'],
    ['bank_account_no', 'contact'],
    ['permanent_address', 'contact'],
    ['phone', 'contact'],
    ['id_number', 'documents'],
    ['social_insurance_no', 'documents'],
    ['health_care_code', 'documents'],
  ])('%s nằm ở tab %s', (field, tab) => {
    expect(tabOfField(field)).toBe(tab)
  })

  it('trường lạ rơi về tab Chung thay vì ném lỗi', () => {
    // Backend thêm cột mới mà bảng chưa cập nhật — thà về tab Chung còn hơn nổ.
    expect(tabOfField('cot_backend_vua_them')).toBe('general')
    expect(tabOfField('')).toBe('general')
  })
})

describe('firstInvalidTab', () => {
  it('trả tab của ô sai đầu tiên', () => {
    const out = firstInvalidTab({ id_number: { message: 'quá dài' } })
    expect(out).toEqual({ tab: 'documents', field: 'id_number' })
  })

  it('trả null khi không có lỗi nào — nơi gọi giữ nguyên tab đang xem', () => {
    expect(firstInvalidTab({})).toBeNull()
  })

  it('chịu được errors là undefined / null', () => {
    // `formState.errors` luôn là object, nhưng đừng để một ca rìa làm nổ nút Lưu.
    expect(firstInvalidTab(undefined as never)).toBeNull()
    expect(firstInvalidTab(null as never)).toBeNull()
  })

  it('ô sai ở tab ĐANG XEM cũng trả về tab đó — không nhảy lung tung', () => {
    const out = firstInvalidTab({ full_name: { message: 'nhập họ tên' } })
    expect(out?.tab).toBe('general')
  })
})
