import { describe, expect, it } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import { SUBJECT_KIND } from '../types/document-access'
import { blockedSelfIds } from './blocked-self-ids'

const user = {
  employee_id: 94,
  department_id: 5,
  company_id: 1,
} as AuthUser

describe('idKhongDuocTuChan', () => {
  //  Lỗi thật 24/08/2026: người dùng tự đưa mình vào cụm «không cho phép» rồi
  //  bấm Tạo — văn bản ra đời mà chính người lập không mở lại được, và cũng
  //  không còn đường vào để gỡ.
  it('chặn chính mình khi đang khai chiều KHÔNG CHO PHÉP', () => {
    expect(blockedSelfIds(SUBJECT_KIND.employee, user, true)).toBe(94)
  })

  it('chặn cả PHÒNG BAN và PHÁP NHÂN của mình — chặn phòng mình thì mình cũng nằm trong đó', () => {
    expect(blockedSelfIds(SUBJECT_KIND.department, user, true)).toBe(5)
    expect(blockedSelfIds(SUBJECT_KIND.company, user, true)).toBe(1)
  })

  it('chiều CHO PHÉP thì không chặn gì — tự mở thêm cho mình là chuyện thường', () => {
    expect(blockedSelfIds(SUBJECT_KIND.employee, user, false)).toBe(0)
    expect(blockedSelfIds(SUBJECT_KIND.department, user, false)).toBe(0)
  })

  it('VAI TRÒ thì không chặn — hồ sơ đăng nhập không nói người này giữ vai trò nào', () => {
    expect(blockedSelfIds(SUBJECT_KIND.role, user, true)).toBe(0)
  })

  it('tài khoản chưa gắn hồ sơ nhân sự thì không có gì để so', () => {
    expect(blockedSelfIds(SUBJECT_KIND.employee, {} as AuthUser, true)).toBe(0)
    expect(blockedSelfIds(SUBJECT_KIND.employee, null, true)).toBe(0)
  })
})
