import { describe, expect, it } from 'vitest'

import { SCOPE_DIM, SCOPE_MODE, type DocumentScopeInput } from '../types/document-scope'
import { cloneTargetsFromScopes } from './clone-targets-from-scopes'

function dong(overrides: Partial<DocumentScopeInput> = {}): DocumentScopeInput {
  return {
    dim: SCOPE_DIM.company,
    mode: SCOPE_MODE.include,
    company_id: 2,
    department_id: null,
    employee_id: null,
    include_children: false,
    ...overrides,
  }
}

const PHAP_NHAN_BAN_HANH = 1

describe('cloneTargetsFromScopes', () => {
  it('lấy đúng các pháp nhân được khai bao gồm', () => {
    const rows = [dong({ company_id: 2 }), dong({ company_id: 3 })]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([2, 3])
  })

  it('bỏ pháp nhân ban hành — bản gốc đã nằm ở đó', () => {
    const rows = [dong({ company_id: PHAP_NHAN_BAN_HANH }), dong({ company_id: 3 })]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([3])
  })

  it('bỏ dòng LOẠI TRỪ, không clone về nơi vừa bị loại ra', () => {
    const rows = [dong({ company_id: 2 }), dong({ company_id: 3, mode: SCOPE_MODE.exclude })]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([2])
  })

  it('bỏ dòng phòng ban và nhân sự — chúng không nói được tách bản cho ai', () => {
    const rows = [
      dong({ dim: SCOPE_DIM.department, company_id: 5, department_id: 7 }),
      dong({ dim: SCOPE_DIM.employee, company_id: null, employee_id: 9 }),
      dong({ company_id: 4 }),
    ]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([4])
  })

  it('khai trùng một pháp nhân hai lần thì chỉ tính một', () => {
    const rows = [dong({ company_id: 2 }), dong({ company_id: 2, include_children: true })]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([2])
  })

  it('«gồm cả đơn vị con» KHÔNG tự bung thành các công ty con', () => {
    //  Clone đẻ ra văn bản thật mang số hiệu vĩnh viễn — không thể sinh theo
    //  một danh sách còn đổi (công ty con mở thêm sau này).
    const rows = [dong({ company_id: 2, include_children: true })]

    expect(cloneTargetsFromScopes(rows, PHAP_NHAN_BAN_HANH)).toEqual([2])
  })

  it('chưa khai dòng nào thì không có nơi nhận', () => {
    expect(cloneTargetsFromScopes([], PHAP_NHAN_BAN_HANH)).toEqual([])
  })
})
