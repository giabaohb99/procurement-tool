import { describe, expect, it } from 'vitest'

import { folderItemKey, parseFolderItemKey, splitFolderItemKeys } from './folder-item-id'

describe('folderItemKey / parseFolderItemKey', () => {
  it('ghi rồi đọc lại đúng nguyên kind + id', () => {
    expect(parseFolderItemKey(folderItemKey('folder', 5))).toEqual({ kind: 'folder', id: 5 })
    expect(parseFolderItemKey(folderItemKey('document', 12))).toEqual({ kind: 'document', id: 12 })
  })

  it('chuỗi không đúng khuôn (thiếu dấu hai chấm) → null', () => {
    expect(parseFolderItemKey('folder-5')).toBeNull()
  })

  it('tiền tố lạ (không phải folder/document) → null', () => {
    expect(parseFolderItemKey('user:5')).toBeNull()
  })

  it('phần id không phải số nguyên dương → null', () => {
    expect(parseFolderItemKey('folder:abc')).toBeNull()
    expect(parseFolderItemKey('folder:0')).toBeNull()
    expect(parseFolderItemKey('folder:-1')).toBeNull()
    expect(parseFolderItemKey('folder:1.5')).toBeNull()
  })

  it('chuỗi rỗng → null, không ném lỗi', () => {
    expect(parseFolderItemKey('')).toBeNull()
  })
})

describe('splitFolderItemKeys', () => {
  it('tách đúng hai mảng id thuần số theo loại', () => {
    const keys = [folderItemKey('folder', 1), folderItemKey('document', 2), folderItemKey('document', 3)]
    expect(splitFolderItemKeys(keys)).toEqual({ folderIds: [1], documentIds: [2, 3] })
  })

  it('tập RỖNG → hai mảng rỗng', () => {
    expect(splitFolderItemKeys([])).toEqual({ folderIds: [], documentIds: [] })
  })

  it('khóa lạ lẫn vào (dữ liệu hỏng) → bỏ qua, không nổ, không lẫn vào kết quả', () => {
    const keys = [folderItemKey('folder', 1), 'lon-xon', 'user:9']
    expect(splitFolderItemKeys(keys)).toEqual({ folderIds: [1], documentIds: [] })
  })

  it('nhận Set (không chỉ mảng) — chữ ký hàm nhận Iterable<string>', () => {
    const keys = new Set([folderItemKey('document', 7)])
    expect(splitFolderItemKeys(keys)).toEqual({ folderIds: [], documentIds: [7] })
  })
})
