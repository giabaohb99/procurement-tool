import { describe, expect, it } from 'vitest'

import { resolveTreeKeyAction } from './tree-keyboard-nav'
import type { FlatTreeNode } from './tree-types'

const FLAT: FlatTreeNode[] = [
  { id: 1, label: 'A', depth: 0, parentId: null, hasChildren: true },
  { id: 2, label: 'A.1', depth: 1, parentId: 1, hasChildren: false },
  { id: 3, label: 'B', depth: 0, parentId: null, hasChildren: false },
]

describe('resolveTreeKeyAction', () => {
  it('phím không xử lý trả null, không đụng gì', () => {
    expect(resolveTreeKeyAction('Tab', FLAT, 0, new Set())).toBeNull()
  })

  it('ArrowDown ở dòng CUỐI trả null thay vì trỏ ra ngoài mảng', () => {
    expect(resolveTreeKeyAction('ArrowDown', FLAT, FLAT.length - 1, new Set())).toBeNull()
  })

  it('ArrowUp ở dòng ĐẦU trả null', () => {
    expect(resolveTreeKeyAction('ArrowUp', FLAT, 0, new Set())).toBeNull()
  })

  it('ArrowDown/ArrowUp giữa danh sách focus đúng dòng liền kề', () => {
    expect(resolveTreeKeyAction('ArrowDown', FLAT, 0, new Set())).toEqual({ type: 'focus', id: 2 })
    expect(resolveTreeKeyAction('ArrowUp', FLAT, 1, new Set())).toEqual({ type: 'focus', id: 1 })
  })

  it('ArrowRight trên nhánh GẬP thì MỞ, không nhảy dòng', () => {
    expect(resolveTreeKeyAction('ArrowRight', FLAT, 0, new Set())).toEqual({
      type: 'toggle',
      id: 1,
    })
  })

  it('ArrowRight trên nhánh ĐÃ MỞ thì nhảy vào dòng con kế tiếp', () => {
    expect(resolveTreeKeyAction('ArrowRight', FLAT, 0, new Set([1]))).toEqual({
      type: 'focus',
      id: 2,
    })
  })

  it('ArrowRight trên node KHÔNG có con và là dòng cuối thì trả null', () => {
    expect(resolveTreeKeyAction('ArrowRight', FLAT, FLAT.length - 1, new Set())).toBeNull()
  })

  it('ArrowLeft trên nhánh ĐÃ MỞ thì ĐÓNG, không lùi ra cha', () => {
    expect(resolveTreeKeyAction('ArrowLeft', FLAT, 0, new Set([1]))).toEqual({
      type: 'toggle',
      id: 1,
    })
  })

  it('ArrowLeft trên dòng CON thì lùi ra CHA (không đóng gì cả)', () => {
    expect(resolveTreeKeyAction('ArrowLeft', FLAT, 1, new Set([1]))).toEqual({
      type: 'focus',
      id: 1,
    })
  })

  it('ArrowLeft trên dòng GỐC (parentId null, chưa mở) trả null', () => {
    expect(resolveTreeKeyAction('ArrowLeft', FLAT, 2, new Set())).toBeNull()
  })

  it('Home/End nhảy thẳng đầu/cuối bất kể đang ở đâu', () => {
    expect(resolveTreeKeyAction('Home', FLAT, 2, new Set())).toEqual({ type: 'focus', id: 1 })
    expect(resolveTreeKeyAction('End', FLAT, 0, new Set())).toEqual({ type: 'focus', id: 3 })
  })

  it('Enter và phím cách đều SELECT đúng dòng đang xét, không phải dòng 0', () => {
    expect(resolveTreeKeyAction('Enter', FLAT, 2, new Set())).toEqual({ type: 'select', row: FLAT[2] })
    expect(resolveTreeKeyAction(' ', FLAT, 2, new Set())).toEqual({ type: 'select', row: FLAT[2] })
  })

  it('index ngoài mảng (dòng vừa bị gỡ khỏi DOM) trả null thay vì ném lỗi', () => {
    expect(resolveTreeKeyAction('ArrowDown', FLAT, 99, new Set())).toBeNull()
    expect(resolveTreeKeyAction('ArrowDown', [], 0, new Set())).toBeNull()
  })
})
