import { describe, expect, it } from 'vitest'

import { SCOPE_DIM } from '../types/document-scope'
import { scopeLabel } from './scope-label'

describe('scopeLabel', () => {
  it('chiều phòng ban luôn kèm pháp nhân — một phòng ban có mặt ở nhiều pháp nhân', () => {
    expect(
      scopeLabel(SCOPE_DIM.department, { department: 'Phòng Kế toán', company: 'Công ty A' }),
    ).toBe('Phòng Kế toán — Công ty A')
  })

  it('chiều pháp nhân đọc đúng tên pháp nhân', () => {
    expect(scopeLabel(SCOPE_DIM.company, { company: 'DEGO Holding' })).toBe('DEGO Holding')
  })

  it('chiều cá nhân đọc tên người, không dính tên pháp nhân đang chọn dở', () => {
    expect(
      scopeLabel(SCOPE_DIM.employee, { employee: 'Trần Minh Đước', company: 'Công ty A' }),
    ).toBe('Trần Minh Đước')
  })

  it('thiếu tên pháp nhân thì không để lại dấu gạch cụt lủn', () => {
    expect(scopeLabel(SCOPE_DIM.department, { department: 'Phòng Kế toán' })).toBe(
      'Phòng Kế toán',
    )
  })
})
