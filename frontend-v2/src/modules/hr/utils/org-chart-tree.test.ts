import { describe, expect, it } from 'vitest'

import { resolveParents } from './org-chart-tree'

describe('resolveParents', () => {
  it('cha ngoài danh sách, bằng 0 hoặc tự trỏ vào mình đều thành gốc', () => {
    const result = resolveParents([1, 2, 3], new Map([[1, 99], [2, 0], [3, 3]]))
    expect([...result.values()]).toEqual([0, 0, 0])
  })

  it('vòng hai nút bị cắt, không treo, vẫn còn đúng một cạnh', () => {
    const result = resolveParents([1, 2], new Map([[1, 2], [2, 1]]))
    expect(result.get(1)).toBe(0) // cắt cạnh của nút id nhỏ nhất
    expect(result.get(2)).toBe(1)
  })

  it('vòng dài có đuôi dẫn vào: đuôi vẫn nối vào vòng, vòng bị cắt', () => {
    const result = resolveParents([1, 2, 3, 4], new Map([[1, 2], [2, 3], [3, 1], [4, 1]]))
    expect(result.get(1)).toBe(0)
    expect(result.get(4)).toBe(1)
  })

  it('danh sách rỗng không nổ', () => {
    expect(resolveParents([], new Map()).size).toBe(0)
  })
})
