import { describe, expect, it } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import { SUBJECT_KIND } from '../types/document-access'
import { idKhongDuocTuChan } from './khong-tu-chan-chinh-minh'

const nguoiDung = {
  employee_id: 94,
  department_id: 5,
  company_id: 1,
} as AuthUser

describe('idKhongDuocTuChan', () => {
  //  Lỗi thật 24/08/2026: người dùng tự đưa mình vào cụm «không cho phép» rồi
  //  bấm Tạo — văn bản ra đời mà chính người lập không mở lại được, và cũng
  //  không còn đường vào để gỡ.
  it('chặn chính mình khi đang khai chiều KHÔNG CHO PHÉP', () => {
    expect(idKhongDuocTuChan(SUBJECT_KIND.employee, nguoiDung, true)).toBe(94)
  })

  it('chặn cả PHÒNG BAN và PHÁP NHÂN của mình — chặn phòng mình thì mình cũng nằm trong đó', () => {
    expect(idKhongDuocTuChan(SUBJECT_KIND.department, nguoiDung, true)).toBe(5)
    expect(idKhongDuocTuChan(SUBJECT_KIND.company, nguoiDung, true)).toBe(1)
  })

  it('chiều CHO PHÉP thì không chặn gì — tự mở thêm cho mình là chuyện thường', () => {
    expect(idKhongDuocTuChan(SUBJECT_KIND.employee, nguoiDung, false)).toBe(0)
    expect(idKhongDuocTuChan(SUBJECT_KIND.department, nguoiDung, false)).toBe(0)
  })

  it('VAI TRÒ thì không chặn — hồ sơ đăng nhập không nói người này giữ vai trò nào', () => {
    expect(idKhongDuocTuChan(SUBJECT_KIND.role, nguoiDung, true)).toBe(0)
  })

  it('tài khoản chưa gắn hồ sơ nhân sự thì không có gì để so', () => {
    expect(idKhongDuocTuChan(SUBJECT_KIND.employee, {} as AuthUser, true)).toBe(0)
    expect(idKhongDuocTuChan(SUBJECT_KIND.employee, null, true)).toBe(0)
  })
})
