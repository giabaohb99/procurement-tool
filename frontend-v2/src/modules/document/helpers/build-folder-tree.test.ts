import { describe, expect, it } from 'vitest'

import type { DocFolderTreeNode } from '../types/document-folder'
import { buildFolderTree } from './build-folder-tree'

function folder(id: number, parent_id: number, name: string, sort_order = 0): DocFolderTreeNode {
  return {
    id,
    company_id: 1,
    parent_id,
    kind: parent_id === 0 ? 1 : 2,
    kind_label: '',
    name,
    code: '',
    path: '',
    depth: 1,
    sort_order,
    status: 1,
    status_label: '',
    document_count: 0,
    document_count_branch: 0,
    my_level: 2, // Đóng góp — buildFolderTree không đọc trường này, chỉ để khớp kiểu.
  }
}

describe('buildFolderTree', () => {
  it('returns an empty list for no rows', () => {
    expect(buildFolderTree([])).toEqual([])
  })

  it('nests children under their parent regardless of input order', () => {
    const tree = buildFolderTree([folder(3, 2, 'Con'), folder(2, 1, 'Cha'), folder(1, 0, 'DEGO')])
    expect(tree).toHaveLength(1)
    expect(tree[0].label).toBe('DEGO')
    expect(tree[0].children?.[0].label).toBe('Cha')
    expect(tree[0].children?.[0].children?.[0].label).toBe('Con')
  })

  it('lifts a node whose parent is invisible to the viewer up to root instead of dropping it', () => {
    //  Người được cấp quyền riêng vào thư mục 9 mà không thấy cha 5 — mất nút
    //  này là họ có quyền mà không bao giờ tìm thấy thư mục trên cây.
    const tree = buildFolderTree([folder(1, 0, 'DEGO'), folder(9, 5, 'Hợp đồng mật')])
    expect(tree.map((n) => n.id)).toEqual([1, 9])
  })

  it('sorts siblings by sort_order then Vietnamese name', () => {
    const tree = buildFolderTree([
      folder(1, 0, 'Gốc'),
      folder(2, 1, 'Đề xuất', 10),
      folder(3, 1, 'Biên bản', 10),
      folder(4, 1, 'Zeta', 0),
    ])
    expect(tree[0].children?.map((n) => n.label)).toEqual(['Zeta', 'Biên bản', 'Đề xuất'])
  })

  it('does not hang or duplicate on a corrupted cycle', () => {
    const tree = buildFolderTree([folder(1, 2, 'A'), folder(2, 1, 'B'), folder(3, 3, 'Tự trỏ')])
    const ids: number[] = []
    const walk = (list: typeof tree) =>
      list.forEach((n) => {
        ids.push(Number(n.id))
        if (n.children) walk(n.children)
      })
    walk(tree)
    expect(ids.sort()).toEqual([1, 2, 3])
  })

  it('leaves no empty children array on leaves', () => {
    const tree = buildFolderTree([folder(1, 0, 'Gốc')])
    expect(tree[0].children).toBeUndefined()
  })

  it('ưu tiên display_name làm nhãn khi có, rơi về name khi trống/thiếu', () => {
    const withShort = { ...folder(1, 0, 'CÔNG TY TNHH DEGO'), display_name: 'DEGO' }
    const withoutShort = { ...folder(2, 0, 'CÔNG TY B'), display_name: '' }
    const tree = buildFolderTree([withShort, withoutShort])
    expect(tree.find((n) => n.id === 1)?.label).toBe('DEGO')
    expect(tree.find((n) => n.id === 2)?.label).toBe('CÔNG TY B')
  })

  it('mọi node đều expandable: true — chevron luôn hiện kể cả thư mục chưa có con', () => {
    const tree = buildFolderTree([folder(1, 0, 'Gốc')])
    expect(tree[0].expandable).toBe(true)
  })
})
