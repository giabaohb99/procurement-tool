import { describe, expect, it } from 'vitest'

import {
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  SECURITY_LEVEL_KIND_URGENCY,
  type SecurityLevel,
} from '../types/security-level'
import { securityLevelLabel } from './security-level-label'

function bac(over: Partial<SecurityLevel>): SecurityLevel {
  return {
    id: 1,
    kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
    value: 1,
    code: 'X',
    name: 'Bậc X',
    description: '',
    is_active: true,
    ...over,
  }
}

describe('securityLevelLabel', () => {
  it('đổi tên bậc trên danh mục thì bảng danh sách hiện tên mới', () => {
    const items = [bac({ id: 3, value: 3, code: 'MAT', name: 'Mật — hạn chế' })]

    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_CONFIDENTIAL, 3)).toBe('Mật — hạn chế')
  })

  //  ĐÂY LÀ CÁI BẪY CHÍNH của cả đợt này. `id` là khóa chính tự tăng, `value`
  //  mới là con số nằm trên văn bản. Bảy dòng seed gốc tình cờ có id trùng
  //  value nên tra nhầm vẫn "chạy đúng"; thêm một bậc mới là lệch ngay.
  it('tra theo value chứ không theo id — thêm bậc mới là hai số lệch nhau', () => {
    const items = [
      bac({ id: 8, value: 7, code: 'TOIMAT', name: 'Tối mật' }),
      bac({ id: 3, value: 3, code: 'MAT', name: 'Mật' }),
    ]

    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_CONFIDENTIAL, 7)).toBe('Tối mật')
    //  Nếu tra nhầm sang `id` thì con số 8 sẽ ra "Tối mật" — phải KHÔNG ra.
    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_CONFIDENTIAL, 8)).toBe('8')
  })

  //  Hai thang dùng chung dải số nhỏ: Công khai và Thường cùng `value = 1`.
  it('không lẫn hai thang khi chúng cùng con số', () => {
    const items = [
      bac({ id: 1, kind: SECURITY_LEVEL_KIND_CONFIDENTIAL, value: 1, name: 'Công khai' }),
      bac({ id: 5, kind: SECURITY_LEVEL_KIND_URGENCY, value: 1, name: 'Thường' }),
    ]

    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_CONFIDENTIAL, 1)).toBe('Công khai')
    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_URGENCY, 1)).toBe('Thường')
  })

  it('chưa nạp xong danh mục thì vẫn đọc ra tên nhờ bản dự phòng', () => {
    expect(securityLevelLabel([], SECURITY_LEVEL_KIND_CONFIDENTIAL, 4)).toBe('Tuyệt mật')
    expect(securityLevelLabel([], SECURITY_LEVEL_KIND_URGENCY, 3)).toBe('Hỏa tốc')
  })

  it('số lạ thì in ra chính con số, không để cột trống', () => {
    expect(securityLevelLabel([], SECURITY_LEVEL_KIND_CONFIDENTIAL, 42)).toBe('42')
  })

  it('không có giá trị thì để trống, không in ra chữ "null"', () => {
    expect(securityLevelLabel([], SECURITY_LEVEL_KIND_CONFIDENTIAL, null)).toBe('')
    expect(securityLevelLabel([], SECURITY_LEVEL_KIND_CONFIDENTIAL, undefined)).toBe('')
  })

  //  Bậc đã ngừng dùng vẫn phải tra ra tên: văn bản cũ còn mang con số đó.
  it('bậc đã ngừng dùng vẫn tra ra tên cho văn bản cũ', () => {
    const items = [bac({ id: 3, value: 3, name: 'Mật', is_active: false })]

    expect(securityLevelLabel(items, SECURITY_LEVEL_KIND_CONFIDENTIAL, 3)).toBe('Mật')
  })
})
