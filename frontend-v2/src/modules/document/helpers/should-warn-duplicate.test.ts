import { describe, expect, it } from 'vitest'

import type { DocumentType } from '../types/document-type'
import { shouldWarnDuplicate } from './should-warn-duplicate'

function loai(overrides: Partial<DocumentType> = {}): DocumentType {
  return {
    id: 1,
    code: 'CV',
    name: 'Công văn',
    needs_approval: true,
    needs_signature: false,
    needs_decision: false,
    is_confidential_type: false,
    ...overrides,
  } as DocumentType
}

describe('shouldWarnDuplicate', () => {
  it('công văn, thông báo… KHÔNG nhắc — một phòng ra hàng chục cái mỗi tháng', () => {
    //  Nhắc ở đây thì lần tạo nào cũng thấy băng vàng, và người dùng học được
    //  đúng một điều: bỏ qua nó.
    expect(shouldWarnDuplicate(loai({ code: 'CV', needs_decision: false }))).toBe(false)
    expect(shouldWarnDuplicate(loai({ code: 'TB', needs_decision: false }))).toBe(false)
  })

  it('văn bản quản trị (quy chế, quy định) thì có nhắc', () => {
    //  Bản thứ hai còn hiệu lực cho cùng một phòng gần như luôn là lỗi: quên
    //  bãi bỏ bản cũ, tổ chức có hai bộ luật cùng chạy.
    expect(shouldWarnDuplicate(loai({ code: 'QC', needs_decision: true }))).toBe(true)
  })

  it('chưa chọn loại thì không nhắc', () => {
    expect(shouldWarnDuplicate(undefined)).toBe(false)
  })
})
