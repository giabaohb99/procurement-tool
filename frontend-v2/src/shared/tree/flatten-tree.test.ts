import { describe, expect, it } from 'vitest'

import { flattenTree } from './flatten-tree'
import type { TreeNode } from './tree-types'

const TREE: TreeNode[] = [
  {
    id: 'a',
    label: 'A',
    children: [
      { id: 'a1', label: 'A1' },
      { id: 'a2', label: 'A2', children: [{ id: 'a2-1', label: 'A2.1' }] },
    ],
  },
  { id: 'b', label: 'B' },
]

describe('flattenTree', () => {
  it('cây rỗng ra danh sách rỗng', () => {
    expect(flattenTree([], () => true)).toEqual([])
  })

  it('không mở gì thì CHỈ thấy các node GỐC, con bị gập không xuất hiện', () => {
    const flat = flattenTree(TREE, () => false)
    expect(flat.map((row) => row.id)).toEqual(['a', 'b'])
  })

  it('mở một nhánh thì con của ĐÚNG nhánh đó chen ngay sau nó, cháu vẫn gập', () => {
    const flat = flattenTree(TREE, (id) => id === 'a')
    expect(flat.map((row) => row.id)).toEqual(['a', 'a1', 'a2', 'b'])
    //  a2 có con (a2-1) nhưng a2 KHÔNG nằm trong tập mở → cháu không hiện.
    expect(flat.find((row) => row.id === 'a2')?.hasChildren).toBe(true)
  })

  it('mở lồng nhau (cha VÀ con đều mở) thì thấy đủ ba tầng theo đúng độ sâu', () => {
    const flat = flattenTree(TREE, (id) => id === 'a' || id === 'a2')
    expect(flat.map((row) => [row.id, row.depth])).toEqual([
      ['a', 0],
      ['a1', 1],
      ['a2', 1],
      ['a2-1', 2],
      ['b', 0],
    ])
  })

  it('gán đúng parentId — node gốc parentId là null', () => {
    const flat = flattenTree(TREE, () => true)
    expect(flat.find((row) => row.id === 'a')?.parentId).toBeNull()
    expect(flat.find((row) => row.id === 'a1')?.parentId).toBe('a')
    expect(flat.find((row) => row.id === 'a2-1')?.parentId).toBe('a2')
  })

  it('leaf (không có children) thì hasChildren = false, không phải mảng rỗng bị hiểu nhầm', () => {
    const flat = flattenTree([{ id: 'x', label: 'X', children: [] }], () => true)
    expect(flat[0]?.hasChildren).toBe(false)
  })

  it('giữ nguyên `data` gắn ở node gốc', () => {
    const flat = flattenTree([{ id: 'x', label: 'X', data: { foo: 1 } }], () => true)
    expect(flat[0]?.data).toEqual({ foo: 1 })
  })

  it('`expandable: true` ép hasChildren dù chưa có children thật (thư mục chưa nạp con)', () => {
    const flat = flattenTree([{ id: 'x', label: 'X', expandable: true }], () => true)
    expect(flat[0]?.hasChildren).toBe(true)
  })

  it('node expandable đang MỞ mà children vẫn undefined thì không nổ, không sinh dòng con nào', () => {
    expect(() =>
      flattenTree([{ id: 'x', label: 'X', expandable: true }], () => true),
    ).not.toThrow()
    const flat = flattenTree([{ id: 'x', label: 'X', expandable: true }], () => true)
    expect(flat.map((row) => row.id)).toEqual(['x'])
  })
})
