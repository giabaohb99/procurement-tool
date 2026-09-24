import { describe, expect, it } from 'vitest'

import { filterTree } from './filter-tree'
import type { TreeNode } from './tree-types'

const TREE: TreeNode[] = [
  {
    id: 'root',
    label: 'Gốc',
    children: [
      {
        id: 'folder-a',
        label: 'Thư mục A',
        children: [
          { id: 'file-1', label: 'hop-dong.pdf' },
          { id: 'file-2', label: 'bao-gia.pdf' },
        ],
      },
      { id: 'folder-b', label: 'Thư mục B rỗng', children: [] },
      { id: 'file-3', label: 'ke-hoach.docx' },
    ],
  },
]

const matchLabel = (needle: string) => (node: TreeNode) =>
  node.label.toLowerCase().includes(needle.toLowerCase())

describe('filterTree', () => {
  it('khớp một leaf sâu trong cây thì GIỮ LẠI tổ tiên dù tổ tiên không khớp', () => {
    const result = filterTree(TREE, matchLabel('hop-dong'))
    //  root → folder-a → file-1 phải còn nguyên đường dẫn, file-2 (không khớp) bị loại.
    expect(result.nodes[0]?.id).toBe('root')
    expect(result.nodes[0]?.children?.map((n) => n.id)).toEqual(['folder-a'])
    expect(result.nodes[0]?.children?.[0]?.children?.map((n) => n.id)).toEqual(['file-1'])
  })

  it('chỉ node THẬT SỰ khớp mới nằm trong matchedIds, tổ tiên ăn theo thì không', () => {
    const result = filterTree(TREE, matchLabel('hop-dong'))
    expect(result.matchedIds.has('file-1')).toBe(true)
    expect(result.matchedIds.has('root')).toBe(false)
    expect(result.matchedIds.has('folder-a')).toBe(false)
  })

  it('không khớp gì thì cây rỗng — không phải cây gốc trơ trọi', () => {
    const result = filterTree(TREE, matchLabel('khong-ton-tai'))
    expect(result.nodes).toEqual([])
    expect(result.matchedIds.size).toBe(0)
  })

  it('cha khớp tên nhưng KHÔNG kéo theo con không khớp — «giữ tổ tiên» khác «lộ cả nhánh»', () => {
    //  Hợp đồng của hàm này CHỈ là "giữ đường dẫn tới kết quả", không phải "node
    //  cha khớp thì show hết con". Hai luật khác nhau: cây tài liệu ngàn tệp mà
    //  gõ đúng TÊN THƯ MỤC lại tràn ra mọi tệp bên trong (kể cả không khớp gì)
    //  là kết quả tìm kiếm sai — người dùng gõ tên thư mục để XÁC NHẬN nó có
    //  tồn tại, không phải để liệt kê toàn bộ nội dung.
    const result = filterTree(TREE, matchLabel('thư mục a'))
    expect(result.nodes[0]?.children?.[0]?.id).toBe('folder-a')
    expect(result.nodes[0]?.children?.[0]?.children).toEqual([])
    expect(result.matchedIds.has('folder-a')).toBe(true)
    expect(result.matchedIds.has('file-1')).toBe(false)
  })

  it('thư mục rỗng (children = []) không khớp gì thì bị loại, không giữ lại vì "có mảng children"', () => {
    const result = filterTree(TREE, matchLabel('ke-hoach'))
    const rootChildren = result.nodes[0]?.children?.map((n) => n.id) ?? []
    expect(rootChildren).not.toContain('folder-b')
    expect(rootChildren).toEqual(['file-3'])
  })

  it('cây rỗng → kết quả rỗng, không lỗi', () => {
    const result = filterTree([], matchLabel('bất kỳ'))
    expect(result.nodes).toEqual([])
    expect(result.matchedIds.size).toBe(0)
  })
})
