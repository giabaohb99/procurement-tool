import { describe, expect, it } from 'vitest'

import { ancestorIdsOfMatches, folderNameMatches } from './folder-tree-search'

describe('ancestorIdsOfMatches', () => {
  const rows = [
    { id: 1, path: '/1/' },
    { id: 5, path: '/1/5/' },
    { id: 9, path: '/1/5/9/' },
    { id: 12, path: '/1/12/' },
  ]

  it('trả về mọi tổ tiên (KHÔNG gồm chính nó) của một node khớp nằm sâu', () => {
    expect(ancestorIdsOfMatches(rows, new Set([9]))).toEqual(expect.arrayContaining([1, 5]))
    expect(ancestorIdsOfMatches(rows, new Set([9]))).not.toContain(9)
  })

  it('gộp tổ tiên của NHIỀU node khớp, không trùng lặp', () => {
    const result = ancestorIdsOfMatches(rows, new Set([9, 12]))
    //  9 kéo theo tổ tiên {1, 5}; 12 kéo theo tổ tiên {1} — id 1 chung cho cả
    //  hai chỉ được xuất hiện ĐÚNG MỘT LẦN.
    expect(new Set(result)).toEqual(new Set([1, 5]))
    expect(result.filter((id) => id === 1)).toHaveLength(1)
  })

  it('node khớp là GỐC (không có tổ tiên nào ngoài chính nó) → mảng rỗng', () => {
    expect(ancestorIdsOfMatches(rows, new Set([1]))).toEqual([])
  })

  it('matchedIds rỗng → mảng rỗng, không nổ', () => {
    expect(ancestorIdsOfMatches(rows, new Set())).toEqual([])
  })

  it('id khớp không có trong danh sách rows (đã bị lọc mất) → bỏ qua, không nổ', () => {
    expect(ancestorIdsOfMatches(rows, new Set([999]))).toEqual([])
  })

  it('row có path rỗng (dữ liệu hỏng) → bỏ qua thay vì ném lỗi', () => {
    expect(ancestorIdsOfMatches([{ id: 3, path: '' }], new Set([3]))).toEqual([])
  })
})

describe('folderNameMatches', () => {
  it('so khớp bỏ dấu tiếng Việt', () => {
    expect(folderNameMatches('Quyết định nhân sự', 'quyet dinh')).toBe(true)
  })

  it('từ khóa rỗng khớp mọi tên (coi như chưa lọc)', () => {
    expect(folderNameMatches('Bất kỳ tên nào', '')).toBe(true)
  })
})
