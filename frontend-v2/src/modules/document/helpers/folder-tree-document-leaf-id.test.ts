import { describe, expect, it } from 'vitest'

import {
  makeDocumentLeafId,
  makeEmptyLeafId,
  makeLoadingLeafId,
  makeMoreLeafId,
  parseDocumentLeafId,
} from './folder-tree-document-leaf-id'

describe('makeDocumentLeafId / parseDocumentLeafId', () => {
  it('mã hóa rồi tách lại đúng cặp (folderId, documentId)', () => {
    const id = makeDocumentLeafId(5, 123)
    expect(parseDocumentLeafId(id)).toEqual({ folderId: 5, documentId: 123 })
  })

  it('CÙNG MỘT văn bản dưới HAI thư mục khác nhau ra HAI id khác nhau (văn bản gắn nhiều thư mục)', () => {
    expect(makeDocumentLeafId(5, 123)).not.toBe(makeDocumentLeafId(9, 123))
  })

  it('id số (thư mục thật) không khớp khuôn lá văn bản', () => {
    expect(parseDocumentLeafId(5)).toBeNull()
  })

  it('id chuỗi của LOẠI LÁ KHÁC (trống/đang tải/xem thêm) không khớp khuôn lá văn bản', () => {
    expect(parseDocumentLeafId(makeEmptyLeafId(5))).toBeNull()
    expect(parseDocumentLeafId(makeLoadingLeafId(5))).toBeNull()
    expect(parseDocumentLeafId(makeMoreLeafId(5))).toBeNull()
  })

  it('chuỗi rác/hỏng khuôn (0, số âm, không phải số) không nổ, trả null', () => {
    expect(parseDocumentLeafId('doc:0:123')).toBeNull()
    expect(parseDocumentLeafId('doc:5:-1')).toBeNull()
    expect(parseDocumentLeafId('doc:abc:123')).toBeNull()
    expect(parseDocumentLeafId('doc:5')).toBeNull()
    expect(parseDocumentLeafId('')).toBeNull()
  })

  it('bốn hàm make* luôn ra id KHÁC NHAU cho cùng một folderId (không đụng nhau trong cùng cây)', () => {
    const ids = new Set([
      makeDocumentLeafId(5, 1),
      makeEmptyLeafId(5),
      makeLoadingLeafId(5),
      makeMoreLeafId(5),
    ])
    expect(ids.size).toBe(4)
  })
})
