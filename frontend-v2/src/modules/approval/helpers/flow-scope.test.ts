import { describe, expect, it } from 'vitest'

import { buildScopeCondition, laDieuKienNangCao, parseScope } from './flow-scope'

describe('flow-scope', () => {
  it('không khai điều kiện nghĩa là áp cho tất cả', () => {
    expect(parseScope('')).toEqual({ kind: 'all', ids: [] })
    expect(buildScopeCondition({ kind: 'all', ids: [] })).toBe('')
  })

  it('chọn vài loại văn bản rồi đọc lại vẫn ra đúng thứ đã chọn', () => {
    const scope = { kind: 'doc_type' as const, ids: [3, 5] }
    expect(parseScope(buildScopeCondition(scope))).toEqual(scope)
  })

  it('chọn vài văn bản cụ thể rồi đọc lại vẫn ra đúng thứ đã chọn', () => {
    const scope = { kind: 'document' as const, ids: [12] }
    expect(parseScope(buildScopeCondition(scope))).toEqual(scope)
  })

  it('chọn kiểu lọc nhưng chưa tick gì thì coi như tất cả, KHÔNG phải không ai', () => {
    //  Gửi `in: []` là điều kiện không bao giờ khớp — luồng lặng lẽ không chạy
    //  và người khai không hiểu vì sao phiếu vẫn đi đường cũ.
    expect(buildScopeCondition({ kind: 'doc_type', ids: [] })).toBe('')
  })

  it('điều kiện hỏng không làm nổ bộ chọn', () => {
    expect(parseScope('{khong phai json')).toEqual({ kind: 'all', ids: [] })
  })

  describe('điều kiện nâng cao gõ tay', () => {
    it('nhận ra điều kiện bộ chọn không diễn tả được', () => {
      const goTay = '[{"field":"total","op":"gte","value":50000000}]'
      expect(laDieuKienNangCao(goTay)).toBe(true)
    })

    it('điều kiện do chính bộ chọn sinh ra thì không phải nâng cao', () => {
      expect(laDieuKienNangCao(buildScopeCondition({ kind: 'doc_type', ids: [3] }))).toBe(false)
    })

    it('để trống không phải là nâng cao', () => {
      expect(laDieuKienNangCao('')).toBe(false)
    })
  })
})
