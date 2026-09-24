import { describe, expect, it } from 'vitest'

import { folderBulkResultMessage } from './folder-bulk-result-message'

describe('folderBulkResultMessage', () => {
  it('không có dòng nào bị từ chối — chỉ nói số đã xử lý', () => {
    expect(folderBulkResultMessage('chuyển', { moved: [1, 2, 3], denied: [] })).toBe(
      'Đã chuyển 3 · bị từ chối 0',
    )
  })

  it('một dòng bị từ chối có lý do — kèm luôn lý do vào cuối câu', () => {
    expect(
      folderBulkResultMessage('chuyển', {
        moved: [1, 2],
        denied: [{ id: 3, reason: 'không có quyền sửa văn bản này' }],
      }),
    ).toBe('Đã chuyển 2 · bị từ chối 1 (không có quyền sửa văn bản này)')
  })

  it('nhiều dòng CÙNG một lý do — chỉ nói lý do đó một lần, không lặp lại', () => {
    expect(
      folderBulkResultMessage('gỡ', {
        moved: [],
        denied: [
          { id: 3, reason: 'không tìm thấy hoặc không có quyền' },
          { id: 4, reason: 'không tìm thấy hoặc không có quyền' },
        ],
      }),
    ).toBe('Đã gỡ 0 · bị từ chối 2 (không tìm thấy hoặc không có quyền)')
  })

  it('nhiều lý do KHÁC NHAU — không liệt kê hết, chỉ nói có bao nhiêu loại', () => {
    expect(
      folderBulkResultMessage('thêm', {
        moved: [1],
        denied: [
          { id: 2, reason: 'không có quyền sửa' },
          { id: 3, reason: 'thư mục đích không hợp lệ' },
        ],
      }),
    ).toBe('Đã thêm 1 · bị từ chối 2 (2 lý do khác nhau)')
  })

  it('bị từ chối nhưng lý do RỖNG (dữ liệu thiếu) — vẫn ra câu gốc, không in "()"', () => {
    expect(folderBulkResultMessage('gỡ', { moved: [1], denied: [{ id: 2, reason: '' }] })).toBe(
      'Đã gỡ 1 · bị từ chối 1',
    )
  })

  it('cả hai mảng đều rỗng (thao tác không có gì để làm)', () => {
    expect(folderBulkResultMessage('chuyển', { moved: [], denied: [] })).toBe(
      'Đã chuyển 0 · bị từ chối 0',
    )
  })
})
