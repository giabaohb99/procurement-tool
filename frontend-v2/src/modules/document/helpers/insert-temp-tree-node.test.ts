import { describe, expect, it } from 'vitest'

import type { TreeNode } from '@/shared/tree/tree-types'
import { insertTempChildNode, NEW_FOLDER_TEMP_ID, ROOT_PARENT_ID } from './insert-temp-tree-node'

const TREE: TreeNode<{ id: number }>[] = [
  {
    id: 1,
    label: 'Cha',
    data: { id: 1 },
    children: [{ id: 2, label: 'Con cũ', data: { id: 2 } }],
  },
  { id: 3, label: 'Gốc khác', data: { id: 3 } },
]

describe('insertTempChildNode', () => {
  it('chèn node tạm làm con ĐẦU TIÊN của đúng cha, giữ nguyên con cũ phía sau', () => {
    const result = insertTempChildNode(TREE, 1)
    expect(result[0]?.children?.map((c) => c.id)).toEqual([NEW_FOLDER_TEMP_ID, 2])
    expect(result[0]?.children?.[0]?.data).toBeUndefined()
  })

  it('cha chưa có con nào thì tạo mảng children mới chỉ gồm node tạm', () => {
    const result = insertTempChildNode(TREE, 3)
    expect(result[1]?.children?.map((c) => c.id)).toEqual([NEW_FOLDER_TEMP_ID])
  })

  it('parentId không tồn tại trong cây thì trả về cây với nội dung Y HỆT (không nổ, không chèn lạc chỗ)', () => {
    const result = insertTempChildNode(TREE, 999)
    expect(result).toEqual(TREE)
  })

  it('không sửa TRỰC TIẾP mảng gốc (thuần) — mảng con của cha cũ vẫn nguyên vẹn', () => {
    const originalChildrenRef = TREE[0]?.children
    insertTempChildNode(TREE, 1)
    expect(TREE[0]?.children).toBe(originalChildrenRef)
    expect(TREE[0]?.children).toHaveLength(1)
  })

  it('cây rỗng thì trả mảng rỗng, không nổ', () => {
    expect(insertTempChildNode([], 1)).toEqual([])
  })

  //  Mở 24/09/2026: tạo THƯ MỤC TỰ DO ở gốc cây.
  it('parentId = ROOT puts the temp row FIRST at the top level, not inside any node', () => {
    const result = insertTempChildNode(TREE, ROOT_PARENT_ID)
    expect(result.map((node) => node.id)).toEqual([NEW_FOLDER_TEMP_ID, 1, 3])
    expect(result[1].children?.map((node) => node.id)).toEqual([2])
  })

  it('parentId = ROOT on an empty tree still yields the temp row (first folder ever)', () => {
    expect(insertTempChildNode([], ROOT_PARENT_ID).map((node) => node.id)).toEqual([
      NEW_FOLDER_TEMP_ID,
    ])
  })
})
